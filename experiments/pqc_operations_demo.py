"""Run using python -m experiments.pqc_operations_demo from project root."""
import json
from pathlib import Path
import sys

from pqc_layer.crypto_backend import OpenSSLPQC
from pqc_layer.access_control import PostQuantumAccessControl, AccessDenied
from pqc_layer.transaction_demo import create_transaction_envelope, accept_transaction_envelope

ROOT = Path(__file__).resolve().parent.parent


def main():
    with OpenSSLPQC() as crypto:
        kem = crypto.keypair("ML-KEM-768")
        teller_sig = crypto.keypair("ML-DSA-65")
        auditor_sig = crypto.keypair("ML-DSA-65")
        access = PostQuantumAccessControl(crypto)
        access.register("teller_01", "teller", teller_sig)
        access.register("auditor_01", "auditor", auditor_sig)
        txn = {"transaction_id": "DEMO-0001", "from_account": "SYNTHETIC-A", "to_account": "SYNTHETIC-B", "amount_minor_units": 12500, "currency": "INR"}
        envelope = create_transaction_envelope(crypto, access, kem, teller_sig, actor="teller_01", service_id="S06", action="initiate_payment", transaction=txn)
        receipt = accept_transaction_envelope(crypto, access, kem, service_id="S06", action="initiate_payment", envelope=envelope)
        replay_blocked = False
        try:
            accept_transaction_envelope(crypto, access, kem, service_id="S06", action="initiate_payment", envelope=envelope)
        except AccessDenied:
            replay_blocked = True
        wrong_role_blocked = False
        unauth = create_transaction_envelope(crypto, access, kem, auditor_sig, actor="auditor_01", service_id="S06", action="initiate_payment", transaction=txn)
        try:
            accept_transaction_envelope(crypto, access, kem, service_id="S06", action="initiate_payment", envelope=unauth)
        except AccessDenied:
            wrong_role_blocked = True
        results = {
            "openssl_version": crypto.version,
            "key_establishment": "ML-KEM-768",
            "encryption": "HKDF-SHA256 + AES-256-GCM",
            "signature": "ML-DSA-65",
            "access_control": "ML-DSA-65 authenticated role-based access control",
            "decryption_roundtrip_pass": receipt["transaction"] == txn,
            "signature_verified_and_access_granted": receipt["accepted"],
            "replay_blocked": replay_blocked,
            "unauthorized_role_blocked": wrong_role_blocked,
            "kem_ciphertext_bytes": len(__import__("base64").b64decode(envelope["kem_ciphertext"])),
            "transaction_signature_bytes": len(crypto.sign(teller_sig, b"test", context="PQC-BANK-TXN-V1")),
            "synthetic_service_id": "S06",
            "synthetic_transaction_hash": receipt["transaction_sha256"]
        }
        out = ROOT / "results" / "tables" / "pqc_operations_demo.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(results, indent=2))
        if not all([results["decryption_roundtrip_pass"], results["signature_verified_and_access_granted"], replay_blocked, wrong_role_blocked]):
            raise AssertionError("One or more critical test assertions failed")
        print("Saved:", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
