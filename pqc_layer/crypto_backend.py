"""Real NIST-standard ML-KEM / ML-DSA via OpenSSL 3.5+, with AES-256-GCM.

Uses subprocesses and private temporary files for an auditable, portable
research demo. Timings include process startup and file I/O; not raw primitive
benchmark timings. For production use audited HSM/PKCS#11 + native integrations.
"""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

KEMS = {"ML-KEM-512", "ML-KEM-768", "ML-KEM-1024", "X25519"}
SIGNATURES = {"ML-DSA-44", "ML-DSA-65", "ML-DSA-87", "ED25519", "SLH-DSA-SHA2-128s"}
KDF_DOMAIN = b"PQC-BANK-ENCRYPTION-V1"


def canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def b64(x: bytes) -> str:
    return base64.b64encode(x).decode("ascii")


def unb64(s: str) -> bytes:
    return base64.b64decode(s, validate=True)


@dataclass(frozen=True)
class KeyPair:
    algorithm: str
    private: Path | None
    public: Path

    def public_view(self) -> "KeyPair":
        return KeyPair(self.algorithm, None, self.public)


class OpenSSLPQC:
    """Owns disposable key files; never exports long-term secrets in reports."""

    def __init__(self, openssl: str | None = None):
        self.openssl = openssl or os.getenv("OPENSSL_BIN", "openssl")
        if not shutil.which(self.openssl):
            raise RuntimeError("OpenSSL not found; install OpenSSL >= 3.5 and set OPENSSL_BIN")
        version = self._exec(["version"]).stdout.decode("utf-8", "replace")
        match = re.search(r"OpenSSL\s+(\d+)\.(\d+)", version)
        if not match or (int(match[1]), int(match[2])) < (3, 5):
            raise RuntimeError(f"OpenSSL >= 3.5 required; found {version.strip()}")
        self.version = version.strip()
        self.tmp = tempfile.TemporaryDirectory(prefix="banking_pqc_")
        self.home = Path(self.tmp.name)
        self.counter = 0

    def close(self):
        self.tmp.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _exec(self, args: list[str], *, allow_failure: bool = False):
        process = subprocess.run([self.openssl, *args], capture_output=True)
        if process.returncode and not allow_failure:
            raise RuntimeError("OpenSSL cryptographic operation failed: " + process.stderr.decode("utf-8", "replace")[:800])
        return process

    def _file(self, content: bytes | None = None) -> Path:
        self.counter += 1
        path = self.home / f"blob_{self.counter}"
        if content is not None:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as f:
                f.write(content)
        return path

    def keypair(self, algorithm: str) -> KeyPair:
        if algorithm not in KEMS | SIGNATURES:
            raise ValueError(f"Unsupported key algorithm {algorithm}")
        private = self._file()
        public = self._file()
        self._exec(["genpkey", "-algorithm", algorithm, "-out", str(private)])
        private.chmod(0o600)
        self._exec(["pkey", "-in", str(private), "-pubout", "-out", str(public)])
        return KeyPair(algorithm, private, public)

    def public_key_der_size(self, key: KeyPair) -> int:
        p = self._file()
        self._exec(["pkey", "-pubin", "-in", str(key.public), "-outform", "DER", "-out", str(p)])
        return p.stat().st_size

    def encapsulate(self, public_key: KeyPair) -> tuple[bytes, bytes]:
        if public_key.algorithm not in KEMS:
            raise ValueError("Not a key-encapsulation algorithm")
        ct = self._file()
        secret = self._file()
        self._exec(["pkeyutl", "-encap", "-inkey", str(public_key.public), "-pubin", "-out", str(ct), "-secret", str(secret)])
        return ct.read_bytes(), secret.read_bytes()

    def decapsulate(self, private_key: KeyPair, kem_ct: bytes) -> bytes:
        if private_key.algorithm not in KEMS:
            raise ValueError("Not a key-encapsulation algorithm")
        if private_key.private is None:
            raise ValueError("Private KEM key required")
        ct = self._file(kem_ct)
        secret = self._file()
        self._exec(["pkeyutl", "-decap", "-inkey", str(private_key.private), "-in", str(ct), "-secret", str(secret)])
        return secret.read_bytes()

    def sign(self, private_key: KeyPair, message: bytes, *, context: str = "PQC-BANK-TXN-V1") -> bytes:
        if private_key.algorithm not in SIGNATURES:
            raise ValueError("Not a signature algorithm")
        if private_key.private is None:
            raise ValueError("Private signing key required")
        msg, sig = self._file(message), self._file()
        args = ["pkeyutl", "-sign", "-inkey", str(private_key.private), "-in", str(msg), "-out", str(sig)]
        if private_key.algorithm.startswith("ML-DSA"):
            args.extend(["-pkeyopt", f"context-string:{context}"])
        self._exec(args)
        return sig.read_bytes()

    def verify(self, public_key: KeyPair, message: bytes, signature: bytes, *, context: str = "PQC-BANK-TXN-V1") -> bool:
        if public_key.algorithm not in SIGNATURES:
            raise ValueError("Not a signature algorithm")
        msg, sig = self._file(message), self._file(signature)
        args = ["pkeyutl", "-verify", "-inkey", str(public_key.public), "-pubin", "-in", str(msg), "-sigfile", str(sig)]
        if public_key.algorithm.startswith("ML-DSA"):
            args.extend(["-pkeyopt", f"context-string:{context}"])
        return self._exec(args, allow_failure=True).returncode == 0

    @staticmethod
    def _aeskey(secret: bytes, salt: bytes, aad: bytes) -> bytes:
        return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=KDF_DOMAIN + b"|" + aad).derive(secret)

    def encrypt(self, recipient: KeyPair, plaintext: bytes, *, aad: bytes) -> dict[str, str | int]:
        kem_ct, secret = self.encapsulate(recipient)
        salt, nonce = os.urandom(16), os.urandom(12)
        ciphertext = AESGCM(self._aeskey(secret, salt, aad)).encrypt(nonce, plaintext, aad)
        return {"version": 1, "kem": recipient.algorithm, "aead": "AES-256-GCM", "kdf": "HKDF-SHA256", "kem_ciphertext": b64(kem_ct), "salt": b64(salt), "nonce": b64(nonce), "ciphertext": b64(ciphertext), "aad": b64(aad)}

    def decrypt(self, recipient: KeyPair, envelope: dict, *, expected_aad: bytes) -> bytes:
        if envelope.get("version") != 1 or envelope.get("kem") != recipient.algorithm or envelope.get("aead") != "AES-256-GCM" or envelope.get("kdf") != "HKDF-SHA256":
            raise ValueError("Unsupported envelope configuration / downgrade attempt")
        aad = unb64(envelope["aad"])
        if aad != expected_aad:
            raise ValueError("Envelope context does not match expected audience/action")
        nonce, salt = unb64(envelope["nonce"]), unb64(envelope["salt"])
        if len(nonce) != 12 or len(salt) != 16:
            raise ValueError("Invalid AES-GCM nonce / KDF salt size")
        secret = self.decapsulate(recipient, unb64(envelope["kem_ciphertext"]))
        return AESGCM(self._aeskey(secret, salt, aad)).decrypt(nonce, unb64(envelope["ciphertext"]), aad)
