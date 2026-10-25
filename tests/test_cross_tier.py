"""Multi-tier assurance gate tests; synthetic providers, no production PKI."""
from __future__ import annotations
import copy
from pathlib import Path
import time
import unittest

from pqc_layer.crypto_backend import OpenSSLPQC, canon, b64
from pqc_layer.access_control import AccessDenied, PostQuantumAccessControl
from pqc_layer.darp_pqc import (build_policies, create_protected_record,
                                accept_protected_record)
from pqc_layer.multitier_assurance import (CrossTierAssuranceGate,
                                            derive_tier_requirements,
                                            ATTESTATION_CONTEXT)

ROOT = Path(__file__).resolve().parent.parent


class TestCrossTierAssurance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry, _ = build_policies(ROOT)
        cls.sid = "S01"
        cls.policy = cls.registry.get(cls.sid)
        cls.req = derive_tier_requirements(ROOT)
        cls.crypto = OpenSSLPQC()
        cls.recipient = {alg: cls.crypto.keypair(alg) for alg in ("ML-KEM-768", "ML-KEM-1024")}
        cls.signer = cls.crypto.keypair(cls.policy.signature)
        cls.access = PostQuantumAccessControl(cls.crypto)
        cls.access.register("bank_teller", "teller", cls.signer)
        cls.gate = CrossTierAssuranceGate(cls.crypto, cls.req)
        cls.providers = {}
        for r in cls.req[cls.sid]:
            key = cls.crypto.keypair("ML-DSA-65")
            cls.gate.register_provider_key(r.asset_id, key)
            cls.providers[r.asset_id] = key
        cls.record = {"transaction_id": "SYN-TEST-001", "amount_minor_units": 1000,
                      "currency": "INR", "customer_alias": "synthetic"}

    @classmethod
    def tearDownClass(cls):
        cls.crypto.close()

    def assertions(self):
        b = self.policy.binding(action="initiate_payment")
        return [self.gate.issue(r, self.providers[r.asset_id],
                                binding=b, record=self.record) for r in self.req[self.sid]]

    def make(self, signed=None):
        return create_protected_record(
            self.crypto, self.access, self.registry, self.recipient,
            self.signer, actor="bank_teller", service_id=self.sid,
            action="initiate_payment", record=self.record,
            dependency_attestations=self.assertions() if signed is None else signed)

    def accept(self, env, gate=True):
        return accept_protected_record(
            self.crypto, self.access, self.registry, self.recipient,
            service_id=self.sid, action="initiate_payment", envelope=env,
            tier_gate=self.gate if gate else None)

    def test_requirements_cover_direct_and_subtier(self):
        tiers = {r.tier for r in self.req[self.sid]}
        self.assertEqual(tiers, {"Third-Party", "Sub-Tier"})
        self.assertTrue(all(r.path_risk > 0 for r in self.req[self.sid]))

    def test_signed_multitier_encryption_and_decryption(self):
        out = self.accept(self.make())
        self.assertTrue(out["accepted"])
        self.assertEqual(out["record"], self.record)
        self.assertEqual(out["cross_tier_assurance"]["third_party"], 1)
        self.assertEqual(out["cross_tier_assurance"]["sub_tier"], 1)

    def test_missing_subtier_attestation_denied(self):
        with self.assertRaises(AccessDenied):
            self.accept(self.make(signed=self.assertions()[:1]))

    def test_malformed_provider_signature_denied(self):
        a = self.assertions()
        a[0]["signature"] = "AAAA"
        with self.assertRaises(AccessDenied):
            self.accept(self.make(signed=a))

    def test_tampered_provider_asset_denied(self):
        a = self.assertions()
        a[0]["claims"]["asset_id"] = "A999"
        with self.assertRaises(AccessDenied):
            self.accept(self.make(signed=a))

    def test_duplicate_attestations_denied(self):
        a = self.assertions()
        with self.assertRaises(AccessDenied):
            self.accept(self.make(signed=[a[0], copy.deepcopy(a[0])]))

    def test_valid_signed_expired_evidence_denied(self):
        a = self.assertions()
        first = a[0]["claims"]
        first["issued_at"] = int(time.time()) - 200
        first["expires_at"] = int(time.time()) - 100
        a[0]["signature"] = b64(self.crypto.sign(self.providers[first["asset_id"]],
                                                canon(first), context=ATTESTATION_CONTEXT))
        with self.assertRaises(AccessDenied):
            self.accept(self.make(signed=a))

    def test_provider_evidence_bound_to_record(self):
        a = self.assertions()
        self.record = dict(self.record)
        try:
            self.record["amount_minor_units"] = 2000
            with self.assertRaises(AccessDenied):
                self.accept(self.make(signed=a))
        finally:
            self.record["amount_minor_units"] = 1000

    def test_same_envelope_replay_denied(self):
        env = self.make()
        self.accept(env)
        with self.assertRaises(AccessDenied):
            self.accept(env)

    def test_gate_is_not_optional_if_proofs_are_supplied(self):
        with self.assertRaises(AccessDenied):
            self.accept(self.make(), gate=False)

    def test_missing_evidence_denied_when_gate_required(self):
        env = create_protected_record(
            self.crypto, self.access, self.registry, self.recipient,
            self.signer, actor="bank_teller", service_id=self.sid,
            action="initiate_payment", record=self.record)
        with self.assertRaises(AccessDenied):
            self.accept(env)


if __name__ == '__main__':
    unittest.main()
