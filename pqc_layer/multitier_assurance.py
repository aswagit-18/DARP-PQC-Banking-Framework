"""DARP-PQC extension: graph-selected, ML-DSA-signed cross-tier risk acknowledgements.

RESEARCH ONLY. These signatures prove that keys registered as provider identities
signed a risk acknowledgement; they DO NOT prove a vendor has actually deployed
PQC or that data is protected outside this demo application. Key registration and
risk-policy inputs must come from a trusted bank authority in production.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import secrets
import time
from pathlib import Path
import sys
from typing import Any

from .access_control import AccessDenied
from .crypto_backend import KeyPair, OpenSSLPQC, b64, canon, unb64

ATTESTATION_DOMAIN = "DARP-PQC-CROSS-TIER-RISK-ACK-V1"
ATTESTATION_CONTEXT = "DARP-TIER-V1"
TIERS = ("Third-Party", "Sub-Tier")


@dataclass(frozen=True)
class TierRequirement:
    service_id: str
    asset_id: str
    tier: str
    provider: str
    path_risk: float
    path: tuple[str, ...]

    def report(self) -> dict:
        return dict(service_id=self.service_id, asset_id=self.asset_id,
                    tier=self.tier, provider=self.provider,
                    path_risk=round(self.path_risk, 6), path=list(self.path))


def derive_tier_requirements(project_root: Path, *, dataset: str = "data",
                             min_path_risk: float = 0.35,
                             max_per_tier: int = 1) -> dict[str, list[TierRequirement]]:
    """Select risk-significant externally controlled dependencies per service.

    One highest-risk reachable asset per external tier by default; this keeps
    the demo small. Tune and evaluate thresholds, don't mistake for an official
    NIST requirement. Internal assets do not issue third-party assertions.
    """
    if not 0 <= min_path_risk <= 1 or max_per_tier < 1:
        raise ValueError("Invalid requirement parameters")
    root = Path(project_root).resolve()
    sys.path.insert(0, str(root / "src"))
    import pandas as pd
    from data_loader import validate_data
    from graph_builder import build_graph
    from risk_model import calculate_direct_risk
    from propagation import calculate_service_propagation

    folder = root / dataset
    a = pd.read_csv(folder / "banking_assets.csv")
    s = pd.read_csv(folder / "banking_services.csv")
    e = pd.read_csv(folder / "banking_dependencies.csv")
    validate_data(a, s, e)
    a = calculate_direct_risk(a)
    g = build_graph(a, s, e)
    _, paths, _ = calculate_service_propagation(g, s, a)
    asset_lookup = {str(row.asset_id): row for row in a.itertuples(index=False)}
    candidates: dict[tuple[str, str], list[TierRequirement]] = {}
    for item in paths:
        asset = asset_lookup[str(item["source_asset"])]
        tier = str(asset.tier)
        value = float(item["path_risk"])
        if tier not in TIERS or value < min_path_risk:
            continue
        sid = str(item["service_id"])
        req = TierRequirement(sid, str(item["source_asset"]), tier,
                              str(asset.provider), value, tuple(str(x) for x in item["path"]))
        candidates.setdefault((sid, tier), []).append(req)
    selected = {str(sid): [] for sid in s.service_id}
    for (sid, tier), group in candidates.items():
        group.sort(key=lambda r: (-r.path_risk, r.asset_id))
        selected[sid].extend(group[:max_per_tier])
    for reqs in selected.values():
        reqs.sort(key=lambda r: (TIERS.index(r.tier), r.asset_id))
    return selected


class CrossTierAssuranceGate:
    """Enforces signed acknowledgement from selected external dependency owners.

    Signed acknowledgement is evidence of the stated acknowledgement only,
    NOT verification that any provider is quantum-resistant.
    """
    def __init__(self, crypto: OpenSSLPQC, requirements: dict[str, list[TierRequirement]]):
        self.crypto = crypto
        self.requirements = {k: tuple(v) for k, v in requirements.items()}
        self.trusted_keys: dict[str, KeyPair] = {}

    def register_provider_key(self, asset_id: str, key: KeyPair) -> None:
        if key.algorithm not in {"ML-DSA-65", "ML-DSA-87"}:
            raise ValueError("Provider attestations require an approved ML-DSA credential")
        known = {r.asset_id for rs in self.requirements.values() for r in rs}
        if asset_id not in known:
            raise ValueError("Provider asset not among attestation requirements")
        if asset_id in self.trusted_keys:
            raise ValueError("Cannot silently replace a registered provider credential")
        self.trusted_keys[asset_id] = key.public_view()

    def required(self, service_id: str) -> tuple[TierRequirement, ...]:
        if service_id not in self.requirements:
            raise AccessDenied("Unknown service assurance policy")
        return self.requirements[service_id]

    def issue(self, requirement: TierRequirement, signer: KeyPair, *, binding: dict,
              record: dict, ttl_seconds: int = 90) -> dict[str, Any]:
        if not 1 <= ttl_seconds <= 300:
            raise ValueError("Attestation TTL must be 1..300 seconds")
        if requirement not in self.required(requirement.service_id):
            raise AccessDenied("Attestation requested for unrecognized asset")
        registered = self.trusted_keys.get(requirement.asset_id)
        if registered is None or registered.algorithm != signer.algorithm or registered.public != signer.public:
            raise AccessDenied("Unregistered provider signing credential")
        if binding.get("service_id") != requirement.service_id:
            raise AccessDenied("Service binding mismatch")
        now = int(time.time())
        claims = {
            "domain": ATTESTATION_DOMAIN,
            "asset_id": requirement.asset_id,
            "provider": requirement.provider,
            "tier": requirement.tier,
            "service_id": requirement.service_id,
            "action": binding["action"],
            "policy_digest": binding["policy_digest"],
            "policy_epoch": binding["policy_epoch"],
            "risk_evidence_digest": binding["risk_evidence_digest"],
            "record_sha256": sha256(canon(record)).hexdigest(),
            "statement": "reviewed_and_acknowledged_quantum_risk",
            "issued_at": now,
            "expires_at": now + ttl_seconds,
            "nonce": secrets.token_hex(16),
        }
        return {"claims": claims, "signature_algorithm": signer.algorithm,
                "signature": b64(self.crypto.sign(signer, canon(claims), context=ATTESTATION_CONTEXT))}

    def verify(self, *, service_id: str, binding: dict, record: dict,
               attestations: list[dict]) -> dict:
        reqs = self.required(service_id)
        if not isinstance(attestations, list) or len(attestations) != len(reqs):
            raise AccessDenied("Missing, duplicated, or unexpected cross-tier assurances")
        by_asset = {r.asset_id: r for r in reqs}
        seen: set[str] = set()
        now = int(time.time())
        for att in attestations:
            try:
                c = att["claims"]
                asset_id = c["asset_id"]
                if asset_id not in by_asset or asset_id in seen:
                    raise AccessDenied("Unexpected or duplicated provider attestation")
                r = by_asset[asset_id]
                expected = {
                    "domain": ATTESTATION_DOMAIN, "asset_id": r.asset_id,
                    "provider": r.provider, "tier": r.tier,
                    "service_id": service_id, "action": binding["action"],
                    "policy_digest": binding["policy_digest"],
                    "policy_epoch": binding["policy_epoch"],
                    "risk_evidence_digest": binding["risk_evidence_digest"],
                    "record_sha256": sha256(canon(record)).hexdigest(),
                    "statement": "reviewed_and_acknowledged_quantum_risk",
                }
                if any(c.get(k) != v for k, v in expected.items()):
                    raise AccessDenied("Provider evidence not bound to current transaction and policy")
                if (type(c.get("issued_at")) is not int or type(c.get("expires_at")) is not int
                    or c["issued_at"] > now + 5 or c["expires_at"] < now
                    or c["expires_at"] <= c["issued_at"]
                    or c["expires_at"] - c["issued_at"] > 300):
                    raise AccessDenied("Stale or invalid provider evidence")
                if not isinstance(c.get("nonce"), str) or len(c["nonce"]) != 32:
                    raise AccessDenied("Invalid provider evidence nonce")
                key = self.trusted_keys.get(asset_id)
                if key is None or key.algorithm != att.get("signature_algorithm"):
                    raise AccessDenied("Untrusted provider evidence signer")
                if not self.crypto.verify(key, canon(c), unb64(att["signature"]), context=ATTESTATION_CONTEXT):
                    raise AccessDenied("Invalid provider ML-DSA signature")
                seen.add(asset_id)
            except (KeyError, TypeError, ValueError) as exc:
                raise AccessDenied("Malformed provider assurance") from exc
        return {"verified": True, "provider_assets": sorted(seen),
                "third_party": sum(r.tier == "Third-Party" for r in reqs),
                "sub_tier": sum(r.tier == "Sub-Tier" for r in reqs)}
