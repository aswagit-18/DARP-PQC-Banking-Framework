"""End-to-end authenticated, encrypted synthetic banking transaction.

Receiver must verify both the ML-DSA transaction signature AND ML-DSA RBAC
request before accepting. No real money, networks, or bank accounts involved.
"""
from __future__ import annotations
import hashlib
import json

from .access_control import PostQuantumAccessControl, AccessDenied
from .crypto_backend import OpenSSLPQC, KeyPair, canon, b64, unb64

TX_CONTEXT = "PQC-BANK-TXN-V1"


def bank_aad(service_id: str, action: str) -> bytes:
    return canon({"version": 1, "service_id": service_id, "action": action, "audience": "bank-gateway"})


def create_transaction_envelope(crypto: OpenSSLPQC, access: PostQuantumAccessControl, recipient: KeyPair, sender: KeyPair, *, actor: str, service_id: str, action: str, transaction: dict) -> dict:
    proof = access.issue_request(actor, sender, action=action, resource=service_id, payload=transaction)
    signature = crypto.sign(sender, canon(transaction), context=TX_CONTEXT)
    body = {"transaction": transaction, "actor": actor, "transaction_signature": b64(signature), "access_request": proof}
    return crypto.encrypt(recipient, canon(body), aad=bank_aad(service_id, action))


def accept_transaction_envelope(crypto: OpenSSLPQC, access: PostQuantumAccessControl, recipient: KeyPair, *, service_id: str, action: str, envelope: dict) -> dict:
    raw = crypto.decrypt(recipient, envelope, expected_aad=bank_aad(service_id, action))
    payload = json.loads(raw)
    actor = payload["actor"]
    txn = payload["transaction"]
    if actor not in access.users:
        raise AccessDenied("Unknown sender")
    if not crypto.verify(access.users[actor].public_key, canon(txn), unb64(payload["transaction_signature"]), context=TX_CONTEXT):
        raise AccessDenied("Transaction digital signature invalid")
    access.authorize(payload["access_request"], action=action, resource=service_id, payload=txn)
    return {"accepted": True, "actor": actor, "service": service_id, "operation": action, "transaction_sha256": hashlib.sha256(canon(txn)).hexdigest(), "transaction": txn}
