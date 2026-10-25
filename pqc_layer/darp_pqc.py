"""DARP-PQC: Dependency-Aware Risk-Bound Post-Quantum Protection.

RESEARCH PROTOTYPE — NOT SECURITY-AUDITED OR PRODUCTION-READY.

The proposed contribution is binding the *existing* multi-tier banking risk
assessment to an enforced PQC configuration and a transaction authorization.
Cryptographic primitives themselves are standardized, not invented here.

Security-critical assumptions:
  - The risk engine's inputs and PolicyRegistry are trusted server-side.
  - Recipient public keys and registered actor signing keys are authentic.
  - The policy epoch is monotonic and the current policy is authoritative.
  - This protects demonstration data exchanged inside this application,
    not the entire banking network, TLS, storage, or external vendors.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any

from .crypto_backend import KeyPair, OpenSSLPQC, b64, canon, unb64
from .access_control import AccessDenied, PostQuantumAccessControl

PROFILES = {
    "standard": ("ML-KEM-768", "ML-DSA-65"),
    "elevated": ("ML-KEM-1024", "ML-DSA-87"),
}
RECORD_SIGNATURE_CONTEXT = "DARP-PQC-RECORD-V1"
DOMAIN = "DARP-PQC-POLICY-V1"


@dataclass(frozen=True)
class ServicePolicy:
    service_id: str
    epoch: int
    total_risk: float
    inherited_risk: float
    criticality: float
    max_subtier_path_risk: float
    max_reachable_hndl: float
    profile: str
    kem: str
    signature: str
    evidence_digest: str
    policy_digest: str
    relevant_assets: int

    def binding(self, *, action: str) -> dict[str, Any]:
        return {
            "domain": DOMAIN,
            "service_id": self.service_id,
            "action": action,
            "policy_epoch": self.epoch,
            "policy_digest": self.policy_digest,
            "risk_evidence_digest": self.evidence_digest,
            "security_profile": self.profile,
            "kem": self.kem,
            "signature": self.signature,
        }

    def public_report(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "epoch": self.epoch,
            "total_risk": self.total_risk,
            "inherited_risk": self.inherited_risk,
            "criticality": self.criticality,
            "max_subtier_path_risk": self.max_subtier_path_risk,
            "max_reachable_hndl": self.max_reachable_hndl,
            "profile": self.profile,
            "kem": self.kem,
            "signature": self.signature,
            "relevant_assets": self.relevant_assets,
            "evidence_digest": self.evidence_digest,
            "policy_digest": self.policy_digest,
        }


class PolicyRegistry:
    """Server-owned policy state; rejects rollback and duplicate epochs."""

    def __init__(self, policies: list[ServicePolicy]):
        self.policies = {p.service_id: p for p in policies}
        if len(self.policies) != len(policies):
            raise ValueError("Duplicate service policies")

    def get(self, service_id: str) -> ServicePolicy:
        if service_id not in self.policies:
            raise AccessDenied("Unknown service or missing authoritative policy")
        return self.policies[service_id]

    def replace(self, new_policy: ServicePolicy) -> None:
        previous = self.get(new_policy.service_id)
        if new_policy.epoch <= previous.epoch:
            raise AccessDenied("Non-monotonic policy epoch / rollback attempt")
        self.policies[new_policy.service_id] = new_policy


def _rounded(x: Any) -> float:
    number = float(x)
    if not 0 <= number <= 1:
        raise ValueError("Risk or criticality outside [0,1]")
    return round(number, 9)


def choose_profile(total_risk: float, criticality: float, max_subtier_path_risk: float, max_hndl: float) -> str:
    """RESEARCH POLICY, not a NIST-mandated security selection rule.

    Baseline is already NIST Category-3; this only steps UP to Category-5.
    Risk values are normalized synthetic model values, not probabilities.
    Thresholds must later be justified with sensitivity/ablation tests.
    """
    if (total_risk >= 0.85 or max_subtier_path_risk >= 0.70
            or (criticality >= 0.95 and max_hndl >= 0.85)):
        return "elevated"
    return "standard"


def build_policies(project_root: Path, *, epoch: int = 1, data_dir: str = "data") -> tuple[PolicyRegistry, float]:
    """Recompute policies from project graph and synthetic data, NOT cached scores.

    All graph inputs, risk factors, and reachable asset path evidence for each
    service are digested into a reproducible trusted policy snapshot.
    """
    if epoch < 1:
        raise ValueError("Epoch must be >= 1")
    project_root = Path(project_root).resolve()
    sys.path.insert(0, str(project_root / "src"))
    from data_loader import load_data, validate_data
    from graph_builder import build_graph
    from risk_model import calculate_direct_risk
    from propagation import calculate_service_propagation
    from ecosystem_risk import calculate_baseline_ecosystem_risk

    if data_dir == "data":
        assets, services, dependencies = load_data()
    else:
        import pandas as pd
        folder = project_root / data_dir
        assets = pd.read_csv(folder / "banking_assets.csv")
        services = pd.read_csv(folder / "banking_services.csv")
        dependencies = pd.read_csv(folder / "banking_dependencies.csv")
    validate_data(assets, services, dependencies)
    risk_assets = calculate_direct_risk(assets)
    graph = build_graph(risk_assets, services, dependencies)
    propagation, path_details, _ = calculate_service_propagation(graph, services, risk_assets)
    service_results, er = calculate_baseline_ecosystem_risk(risk_assets, services, propagation)

    asset_lookup = {str(row.asset_id): row for row in risk_assets.itertuples(index=False)}
    by_service: dict[str, list[dict]] = {}
    for r in path_details:
        by_service.setdefault(str(r["service_id"]), []).append(r)

    policies = []
    for row in service_results.itertuples(index=False):
        sid = str(row.service_id)
        risk = _rounded(row.total_service_risk)
        inherited = _rounded(row.inherited_quantum_risk)
        criticality = _rounded(row.criticality)
        evidence = []
        sub_tier_max = 0.0
        max_hndl = 0.0
        for p in by_service.get(sid, []):
            asset = asset_lookup[str(p["source_asset"])]
            end_tier = str(asset.tier)
            current_risk = _rounded(p["path_risk"])
            if end_tier == "Sub-Tier":
                sub_tier_max = max(sub_tier_max, current_risk)
            max_hndl = max(max_hndl, _rounded(asset.hndl_exposure))
            evidence.append({
                "source_asset": str(p["source_asset"]),
                "tier": end_tier,
                "path": [str(x) for x in p["path"]],
                "path_risk": current_risk,
                "dependency_weight": _rounded(p["dependency_weight"]),
                "quantum_vulnerability": _rounded(asset.quantum_vulnerability),
                "hndl_exposure": _rounded(asset.hndl_exposure),
            })
        evidence.sort(key=lambda p: (p["source_asset"], p["path"]))
        # Inputs include all relevant analyzed paths and current service risk.
        attested = {
            "model": "DARP-PQC-RISK-SNAPSHOT-V1",
            "service_id": sid,
            "risk": risk,
            "inherited": inherited,
            "criticality": criticality,
            "paths": evidence,
        }
        evidence_digest = sha256(canon(attested)).hexdigest()
        profile = choose_profile(risk, criticality, sub_tier_max, max_hndl)
        kem, signature = PROFILES[profile]
        policy_fields = {
            "domain": DOMAIN,
            "service_id": sid,
            "epoch": epoch,
            "evidence_digest": evidence_digest,
            "profile": profile,
            "kem": kem,
            "signature": signature,
        }
        policies.append(ServicePolicy(
            service_id=sid, epoch=epoch, total_risk=risk,
            inherited_risk=inherited, criticality=criticality,
            max_subtier_path_risk=sub_tier_max, max_reachable_hndl=max_hndl,
            profile=profile, kem=kem, signature=signature,
            evidence_digest=evidence_digest,
            policy_digest=sha256(canon(policy_fields)).hexdigest(),
            relevant_assets=len(evidence),
        ))
    return PolicyRegistry(policies), float(er)


def create_protected_record(
    crypto: OpenSSLPQC,
    access: PostQuantumAccessControl,
    registry: PolicyRegistry,
    recipients: dict[str, KeyPair],
    sender: KeyPair,
    *, actor: str, service_id: str, action: str, record: dict,
    dependency_attestations: list[dict] | None = None,
) -> dict:
    """Apply authoritative profile and sign the *policy-bound* request."""
    policy = registry.get(service_id)
    if policy.kem not in recipients:
        raise AccessDenied("Missing key for the mandated PQC KEM profile")
    if sender.algorithm != policy.signature:
        raise AccessDenied("Sender does not possess the mandated PQC signing credential")
    binding = policy.binding(action=action)
    protected = {"record": record, "binding": binding}
    if dependency_attestations is not None:
        protected["attestations_sha256"] = sha256(canon(dependency_attestations)).hexdigest()
    signed_record = b64(crypto.sign(sender, canon(protected), context=RECORD_SIGNATURE_CONTEXT))
    auth = access.issue_request(actor, sender, action=action, resource=service_id, payload=protected)
    body = {
        "actor": actor,
        "record": record,
        "binding": binding,
        "signature": signed_record,
        "authorization": auth,
    }
    if dependency_attestations is not None:
        body["dependency_attestations"] = dependency_attestations
    envelope = crypto.encrypt(recipients[policy.kem].public_view(), canon(body), aad=canon(binding))
    # Visible header isn't trusted; it is re-checked against the server registry.
    envelope["policy_binding"] = binding
    return envelope


def accept_protected_record(
    crypto: OpenSSLPQC,
    access: PostQuantumAccessControl,
    registry: PolicyRegistry,
    recipients: dict[str, KeyPair],
    *, service_id: str, action: str, envelope: dict,
    tier_gate=None,
) -> dict:
    """Fail-closed on stale policy, altered service, wrong suite or invalid role."""
    policy = registry.get(service_id)
    expected = policy.binding(action=action)
    if envelope.get("policy_binding") != expected:
        raise AccessDenied("Risk-policy mismatch, replayed epoch, or profile downgrade")
    if envelope.get("kem") != policy.kem:
        raise AccessDenied("Wrong KEM for authoritative service profile")
    if policy.kem not in recipients:
        raise AccessDenied("Missing mandated server KEM key")
    plaintext = crypto.decrypt(recipients[policy.kem], envelope, expected_aad=canon(expected))
    try:
        body = json.loads(plaintext)
        if body["binding"] != expected:
            raise AccessDenied("Decrypted policy binding differs from trusted policy")
        actor = body["actor"]
        user = access.users.get(actor)
        if user is None or user.public_key.algorithm != policy.signature:
            raise AccessDenied("Unknown actor or signer below required profile")
        protected = {"record": body["record"], "binding": expected}
        attestations = body.get("dependency_attestations")
        if tier_gate is not None:
            if attestations is None:
                raise AccessDenied("Missing required cross-tier signed acknowledgements")
            protected["attestations_sha256"] = sha256(canon(attestations)).hexdigest()
        elif attestations is not None:
            raise AccessDenied("Cross-tier evidence supplied without an authoritative verifier")
        signature = unb64(body["signature"])
        if not crypto.verify(user.public_key, canon(protected), signature, context=RECORD_SIGNATURE_CONTEXT):
            raise AccessDenied("Invalid PQ signature over record and risk policy")
        assurance_report = (tier_gate.verify(service_id=service_id, binding=expected,
                                              record=body["record"], attestations=attestations)
                            if tier_gate is not None else None)
        access.authorize(body["authorization"], action=action, resource=service_id, payload=protected)
        return {
            "accepted": True,
            "actor": actor,
            "service_id": service_id,
            "action": action,
            "record": body["record"],
            "record_sha256": sha256(canon(body["record"])).hexdigest(),
            "policy_epoch": policy.epoch,
            "policy_digest": policy.policy_digest,
            "security_profile": policy.profile,
            "cross_tier_assurance": assurance_report,
        }
    except (KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AccessDenied("Invalid or malformed protected record") from exc
