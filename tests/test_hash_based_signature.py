"""Alternative standardized hash-based PQ digital signatures (NIST FIPS 205)."""
import unittest
from pqc_layer.crypto_backend import OpenSSLPQC


class TestSLHDSA(unittest.TestCase):
    def test_hash_based_signature_roundtrip_and_tamper(self):
        with OpenSSLPQC() as crypto:
            key = crypto.keypair("SLH-DSA-SHA2-128s")
            payload = b"synthetic banking audit event"
            sig = crypto.sign(key, payload)
            self.assertTrue(crypto.verify(key.public_view(), payload, sig))
            self.assertFalse(crypto.verify(key.public_view(), payload+b"!", sig))
            self.assertGreater(len(sig), 3000)


if __name__ == '__main__':
    unittest.main()
