"""PQ-signed role-based access control (RBAC) for synthetic banking services.

Only the server registry assigns roles and public keys. Signed request context,
resource binding, short TTL and replay rejection are enforced. Prototype only.
"""
from __future__ import annotations
import hashlib
import binascii
import secrets
import time
from dataclasses import dataclass

from .crypto_backend import OpenSSLPQC, KeyPair, canon, b64, unb64

POLICY: dict[str, set[str]] = {
    "teller": {"read_balance", "initiate_payment"},
    "manager": {"read_balance", "initiate_payment", "approve_payment"},
    "auditor": {"read_audit"},
}
ACCESS_CONTEXT = "PQC-BANK-ACCESS-V1"


@dataclass(frozen=True)
class User:
    user_id: str
    role: str
    public_key: KeyPair  # public part is used by authorization server


class AccessDenied(Exception):
    pass


class PostQuantumAccessControl:
    def __init__(self, crypto: OpenSSLPQC):
        self.crypto = crypto
        self.users: dict[str, User] = {}
        self.seen_nonces: set[tuple[str, str]] = set()

    def register(self, user_id: str, role: str, key: KeyPair):
        if role not in POLICY or key.algorithm not in {"ML-DSA-44", "ML-DSA-65", "ML-DSA-87"}:
            raise ValueError("Only known roles and ML-DSA signature credentials permitted")
        self.users[user_id] = User(user_id, role, key.public_view())

    def issue_request(self, actor: str, signing_key: KeyPair, *, action: str, resource: str, payload: dict, ttl_seconds: int = 60) -> dict:
        if not 1 <= ttl_seconds <= 300:
            raise ValueError("TTL must be 1 to 300 seconds")
        now = int(time.time())
        claims = {
            "actor": actor,
            "action": action,
            "resource": resource,
            "payload_sha256": hashlib.sha256(canon(payload)).hexdigest(),
            "nonce": secrets.token_hex(16),
            "issued_at": now,
            "expires_at": now + ttl_seconds,
        }
        return {"claims": claims, "signature": b64(self.crypto.sign(signing_key, canon(claims), context=ACCESS_CONTEXT)), "signature_algorithm": signing_key.algorithm}

    def authorize(self, request: dict, *, action: str, resource: str, payload: dict) -> bool:
        try:
            claims = request["claims"]
            actor = claims["actor"]
            user = self.users[actor]
            now = int(time.time())
            if request.get("signature_algorithm") != user.public_key.algorithm:
                raise AccessDenied("Unsupported or mismatched signing algorithm")
            if claims["action"] != action or claims["resource"] != resource:
                raise AccessDenied("Action / resource mismatch")
            if claims["payload_sha256"] != hashlib.sha256(canon(payload)).hexdigest():
                raise AccessDenied("Signed payload mismatch")
            if claims["issued_at"] > now + 5 or claims["expires_at"] < now or claims["expires_at"] - claims["issued_at"] > 300:
                raise AccessDenied("Access request expired or time claims invalid")
            if action not in POLICY[user.role]:
                raise AccessDenied("Insufficient role permission")
            nonce = claims["nonce"]
            if not isinstance(nonce, str) or len(nonce) < 16:
                raise AccessDenied("Invalid request nonce")
            if (actor, nonce) in self.seen_nonces:
                raise AccessDenied("Replay detected")
            if not self.crypto.verify(user.public_key, canon(claims), unb64(request["signature"]), context=ACCESS_CONTEXT):
                raise AccessDenied("Invalid post-quantum access signature")
            self.seen_nonces.add((actor, nonce))
            return True
        except AccessDenied:
            raise
        except (KeyError, TypeError, ValueError, binascii.Error) as exc:
            raise AccessDenied("Malformed or unregistered access request") from exc
