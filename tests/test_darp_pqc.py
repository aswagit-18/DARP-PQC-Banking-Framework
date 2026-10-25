"""Security properties of the research prototype (not a formal security proof)."""
import base64
import copy
from dataclasses import replace
from pathlib import Path
import unittest

from cryptography.exceptions import InvalidTag
from pqc_layer.crypto_backend import OpenSSLPQC, canon
from pqc_layer.access_control import PostQuantumAccessControl, AccessDenied
from pqc_layer.darp_pqc import (
    build_policies, create_protected_record, accept_protected_record,
    PolicyRegistry, choose_profile
)

ROOT = Path(__file__).resolve().parent.parent


class TestDARPPQC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry, cls.baseline_er = build_policies(ROOT)
        cls.crypto = OpenSSLPQC()
        cls.recipients = {
            a: cls.crypto.keypair(a) for a in ("ML-KEM-768", "ML-KEM-1024")
        }
        cls.signers = {
            a: cls.crypto.keypair(a) for a in ("ML-DSA-65", "ML-DSA-87")
        }
        cls.acl = PostQuantumAccessControl(cls.crypto)
        cls.acl.register("teller_standard", "teller", cls.signers["ML-DSA-65"])
        cls.acl.register("teller_elevated", "teller", cls.signers["ML-DSA-87"])
        cls.acl.register("auditor_elevated", "auditor", cls.signers["ML-DSA-87"])
        cls.record = {"id": "DEMO-1", "customer_alias": "synthetic", "amount_minor_units": 10000, "currency": "INR"}
        cls.standard = next(p.service_id for p in cls.registry.policies.values() if p.profile == "standard")
        cls.elevated = next(p.service_id for p in cls.registry.policies.values() if p.profile == "elevated")

    @classmethod
    def tearDownClass(cls):
        cls.crypto.close()

    def produce(self, sid, actor=None, signing_key=None):
        pol = self.registry.get(sid)
        key = signing_key or self.signers[pol.signature]
        identity = actor or ("teller_elevated" if pol.profile == "elevated" else "teller_standard")
        return create_protected_record(self.crypto, self.acl, self.registry, self.recipients, key,
                                       actor=identity, service_id=sid, action="initiate_payment", record=self.record)

    def accept(self, sid, e, registry=None):
        return accept_protected_record(self.crypto, self.acl, registry or self.registry, self.recipients,
                                       service_id=sid, action="initiate_payment", envelope=e)

    def test_both_security_profiles_roundtrip(self):
        for sid in (self.standard, self.elevated):
            with self.subTest(service=sid):
                env = self.produce(sid)
                got = self.accept(sid, env)
                self.assertEqual(got["record"], self.record)
                self.assertEqual(got["security_profile"], self.registry.get(sid).profile)
                self.assertEqual(got["policy_digest"], self.registry.get(sid).policy_digest)

    def test_algorithm_downgrade_blocked(self):
        env = self.produce(self.elevated)
        bad = copy.deepcopy(env)
        bad["kem"] = "ML-KEM-768"
        with self.assertRaises(AccessDenied):
            self.accept(self.elevated, bad)

    def test_policy_digest_alteration_blocked(self):
        env = self.produce(self.elevated)
        bad = copy.deepcopy(env)
        bad["policy_binding"]["policy_digest"] = "0"*64
        with self.assertRaises(AccessDenied):
            self.accept(self.elevated, bad)

    def test_stale_epoch_blocked_after_policy_update(self):
        env = self.produce(self.standard)
        original = self.registry.get(self.standard)
        revised = replace(original, epoch=original.epoch + 1, policy_digest="f"*64)
        local = PolicyRegistry(list(self.registry.policies.values()))
        local.replace(revised)
        with self.assertRaises(AccessDenied):
            self.accept(self.standard, env, registry=local)
        with self.assertRaises(AccessDenied):
            local.replace(original)

    def test_cross_service_replay_blocked(self):
        env = self.produce(self.standard)
        other = self.elevated
        with self.assertRaises(AccessDenied):
            self.accept(other, env)

    def test_replay_denied(self):
        env = self.produce(self.elevated)
        self.accept(self.elevated, env)
        with self.assertRaises(AccessDenied):
            self.accept(self.elevated, env)

    def test_ciphertext_integrity_tamper(self):
        env = self.produce(self.standard)
        bad = copy.deepcopy(env)
        raw = bytearray(base64.b64decode(env["ciphertext"]))
        raw[-1] ^= 1
        bad["ciphertext"] = base64.b64encode(raw).decode()
        with self.assertRaises(InvalidTag):
            self.accept(self.standard, bad)

    def test_envelope_binding_cannot_be_replaced(self):
        env = self.produce(self.elevated)
        bad = copy.deepcopy(env)
        bad["aad"] = base64.b64encode(b'{}').decode()
        with self.assertRaises(ValueError):
            self.accept(self.elevated, bad)

    def test_unauthorized_role_rejected(self):
        env = self.produce(self.elevated, actor="auditor_elevated")
        with self.assertRaises(AccessDenied):
            self.accept(self.elevated, env)

    def test_weaker_signing_key_rejected_in_high_profile(self):
        with self.assertRaises(AccessDenied):
            self.produce(self.elevated, actor="teller_standard", signing_key=self.signers["ML-DSA-65"])

    def test_lower_risk_cannot_turn_off_postquantum_security(self):
        self.assertEqual(choose_profile(0.1,0.1,0.0,0.1), "standard")
        self.assertEqual(choose_profile(0.9,0.1,0.0,0.1), "elevated")

    def test_private_keys_not_serialized(self):
        env=self.produce(self.standard)
        self.assertNotIn("private", str(env).lower())
        self.assertEqual(env["kem"], "ML-KEM-768")

if __name__ == "__main__":
    unittest.main()
