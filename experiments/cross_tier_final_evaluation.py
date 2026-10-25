"""Final controlled ablation: fixed/risk-bound PQC vs cross-tier risk acknowledgement.

The extension is real cryptography but simulated organizational issuers.
Its attestations prove signatures and accountability, NOT PQC deployment status.
"""
from __future__ import annotations
import argparse
import csv
import json
import platform
import statistics
import time
from pathlib import Path

from pqc_layer.crypto_backend import OpenSSLPQC, canon
from pqc_layer.access_control import AccessDenied, PostQuantumAccessControl
from pqc_layer.darp_pqc import build_policies, create_protected_record, accept_protected_record
from pqc_layer.multitier_assurance import CrossTierAssuranceGate, derive_tier_requirements
from pqc_layer.banking_gateway import RiskBoundBankingGateway

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "results" / "tables"


def main(iterations: int = 20):
    if iterations < 3:
        raise ValueError("Use at least three repetitions")
    registry, risk = build_policies(ROOT)
    requirements = derive_tier_requirements(ROOT)
    sid = "S01"
    policy = registry.get(sid)
    selected = requirements[sid]
    assert {r.tier for r in selected} == {"Third-Party", "Sub-Tier"}
    data = {"transaction_id": "SYNTHETIC-MULTITIER-DEMO", "amount_minor_units": 12500,
            "currency": "INR", "customer_alias": "NOT_REAL_CUSTOMER"}

    with OpenSSLPQC() as crypto:
        recipient = {alg: crypto.keypair(alg) for alg in ("ML-KEM-768", "ML-KEM-1024")}
        bank_signer = crypto.keypair(policy.signature)
        acl = PostQuantumAccessControl(crypto)
        acl.register("bank_employee", "teller", bank_signer)
        gate = CrossTierAssuranceGate(crypto, requirements)
        gateway = RiskBoundBankingGateway(crypto, acl, registry, recipient, gate)
        provider_keys = {}
        for req in selected:
            key = crypto.keypair("ML-DSA-65")
            gate.register_provider_key(req.asset_id, key)
            provider_keys[req.asset_id] = key

        def base():
            env = create_protected_record(crypto, acl, registry, recipient, bank_signer,
                actor="bank_employee", service_id=sid, action="initiate_payment", record=data)
            receipt = accept_protected_record(crypto, acl, registry, recipient,
                service_id=sid, action="initiate_payment", envelope=env)
            assert receipt["accepted"] and receipt["record"] == data
            return env

        def upgraded():
            binding = policy.binding(action="initiate_payment")
            attestations = [gate.issue(req, provider_keys[req.asset_id],
                                       binding=binding, record=data) for req in selected]
            env = gateway.protect(bank_signer, actor="bank_employee", service_id=sid,
                action="initiate_payment", record=data,
                external_attestations=attestations)
            receipt = gateway.accept(service_id=sid, action="initiate_payment", envelope=env)
            assert receipt["accepted"] and receipt["record"] == data
            assert receipt["cross_tier_assurance"]["sub_tier"] == 1
            return env

        scenarios = [("DARP-PQC without tier-gate", base),
                     ("DARP-PQC with cross-tier gate", upgraded)]
        rows = []
        for name, func in scenarios:
            milliseconds, sizes = [], []
            for _ in range(iterations):
                t = time.perf_counter_ns()
                env = func()
                milliseconds.append((time.perf_counter_ns() - t) / 1e6)
                sizes.append(len(canon(env)))
            rows.append({
                "scenario": name, "repetitions": iterations, "service_id": sid,
                "median_ms": round(statistics.median(milliseconds), 3),
                "mean_ms": round(statistics.mean(milliseconds), 3),
                "p95_ms": round(sorted(milliseconds)[max(0, int(0.95 * iterations + .9999)-1)], 3),
                "median_json_bytes": statistics.median(sizes),
                "cross_tier_signatures": len(selected) if name == "DARP-PQC with cross-tier gate" else 0,
            })

        failures = {}
        binding = policy.binding(action="initiate_payment")
        both = [gate.issue(r, provider_keys[r.asset_id], binding=binding, record=data) for r in selected]
        for label, variant in [("missing_subtier", both[:1]), ("missing_all", []),
                               ("duplicate_provider", [both[0], both[0]])]:
            env = create_protected_record(crypto, acl, registry, recipient, bank_signer,
                actor="bank_employee", service_id=sid, action="initiate_payment", record=data,
                dependency_attestations=variant)
            try:
                accept_protected_record(crypto, acl, registry, recipient,
                    service_id=sid, action="initiate_payment", envelope=env, tier_gate=gate)
                failures[label] = "INCORRECTLY ACCEPTED"
            except AccessDenied:
                failures[label] = "REJECTED"
        if any(v != "REJECTED" for v in failures.values()):
            raise AssertionError("Gate negative tests failed")
        summary = {
            "dataset": "V1 synthetic banking ecosystem", "service_id": sid,
            "baseline_ecosystem_risk": risk,
            "security_profile": policy.profile, "kem": policy.kem, "signature": policy.signature,
            "required_tiers": [r.report() for r in selected],
            "negative_checks": failures,
            "host": {"python": platform.python_version(), "platform": platform.platform(),
                     "openssl": crypto.version},
            "limitations": "Simulated providers, locally registered keys, no production vendor attestation, no forward secrecy, not a security proof; timings include OpenSSL CLI and temporary files.",
        }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    csvfile = OUTPUT / "cross_tier_ablation.csv"
    with csvfile.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (OUTPUT / "cross_tier_proof_demo.json").write_text(json.dumps(summary, indent=2)+"\n",encoding="utf-8")
    print("\nMULTI-TIER PQC ASSURANCE TEST")
    print("Service:", sid, "/", policy.profile, "/", policy.kem, "/", policy.signature)
    print("External dependency requirements:", [r.asset_id+":"+r.tier for r in selected])
    for r in rows:
        print(f"{r['scenario']}: median={r['median_ms']}ms, p95={r['p95_ms']}ms, bytes={r['median_json_bytes']}")
    print("Negative checks:", failures)
    print("Saved:", csvfile, "and cross_tier_proof_demo.json")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--iterations", type=int, default=20)
    main(p.parse_args().iterations)
