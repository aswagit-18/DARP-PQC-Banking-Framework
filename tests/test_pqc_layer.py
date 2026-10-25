import base64
import copy
import unittest
from cryptography.exceptions import InvalidTag

from pqc_layer.crypto_backend import OpenSSLPQC, canon
from pqc_layer.access_control import PostQuantumAccessControl, AccessDenied
from pqc_layer.transaction_demo import create_transaction_envelope, accept_transaction_envelope, bank_aad


class TestPQCProtection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.crypto=OpenSSLPQC()
        cls.bank=cls.crypto.keypair("ML-KEM-768")
        cls.teller=cls.crypto.keypair("ML-DSA-65")
        cls.audit=cls.crypto.keypair("ML-DSA-65")
        cls.acl=PostQuantumAccessControl(cls.crypto)
        cls.acl.register("teller", "teller", cls.teller)
        cls.acl.register("auditor", "auditor", cls.audit)
        cls.txn={"transaction_id":"T-101", "amount_minor_units":10000, "currency":"INR"}

    @classmethod
    def tearDownClass(cls):
        cls.crypto.close()

    def signed_envelope(self, actor="teller", key=None, action="initiate_payment"):
        return create_transaction_envelope(self.crypto, self.acl, self.bank, key or self.teller, actor=actor, service_id="S06", action=action, transaction=self.txn)

    def accept(self, envelope, action="initiate_payment"):
        return accept_transaction_envelope(self.crypto, self.acl, self.bank, service_id="S06", action=action, envelope=envelope)

    def test_roundtrip_and_valid_signature(self):
        self.assertEqual(self.accept(self.signed_envelope())["transaction"], self.txn)

    def test_unauthorized_role_denied(self):
        with self.assertRaises(AccessDenied):
            self.accept(self.signed_envelope(actor="auditor", key=self.audit))

    def test_replay_rejected(self):
        env=self.signed_envelope()
        self.accept(env)
        with self.assertRaises(AccessDenied):
            self.accept(env)

    def test_ciphertext_tamper_rejected(self):
        env=self.signed_envelope()
        corrupted=copy.deepcopy(env)
        cipher=bytearray(base64.b64decode(env["ciphertext"]))
        cipher[-1] ^= 1
        corrupted["ciphertext"]=base64.b64encode(cipher).decode()
        with self.assertRaises(InvalidTag):
            self.accept(corrupted)

    def test_signature_tamper_rejected(self):
        msg=canon(self.txn)
        sig=bytearray(self.crypto.sign(self.teller, msg))
        sig[5] ^= 1
        self.assertFalse(self.crypto.verify(self.teller, msg, bytes(sig)))
        self.assertFalse(self.crypto.verify(self.teller, msg+b"tampered", self.crypto.sign(self.teller,msg)))

    def test_cross_service_binding_rejected(self):
        with self.assertRaises(ValueError):
            self.crypto.decrypt(self.bank, self.signed_envelope(), expected_aad=bank_aad("S02","initiate_payment"))

    def test_algorithm_downgrade_rejected(self):
        corrupted=copy.deepcopy(self.signed_envelope())
        corrupted["kem"]="RSA"
        with self.assertRaises(ValueError):
            self.accept(corrupted)

    def test_non_registered_actor_fails_closed(self):
        with self.assertRaises(AccessDenied):
            self.accept(self.signed_envelope(actor="unknown"))

    def test_private_key_is_not_in_envelope(self):
        self.assertNotIn("private_key", self.signed_envelope())

if __name__ == '__main__':
    unittest.main()
