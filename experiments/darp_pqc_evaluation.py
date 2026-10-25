"""Compare fixed PQC protection with DARP-PQC on the SAME host.

Includes CLI process and file I/O, NOT microbenchmark timings.
Run: python -m experiments.darp_pqc_evaluation --iterations 15
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
from pqc_layer.access_control import PostQuantumAccessControl
from pqc_layer.transaction_demo import create_transaction_envelope, accept_transaction_envelope
from pqc_layer.darp_pqc import build_policies, create_protected_record, accept_protected_record

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "results" / "tables"


def stats(data: list[float]) -> tuple[float, float, float]:
    s = sorted(data)
    p95 = s[min(len(s) - 1, max(0, int(0.95 * len(s) + 0.9999) - 1))]
    return round(statistics.median(s), 3), round(p95, 3), round(statistics.mean(s), 3)


def main(n: int = 15):
    if n < 3:
        raise ValueError("At least three iterations required")
    started = time.perf_counter_ns()
    registry, er = build_policies(ROOT)
    assessment_ms = (time.perf_counter_ns()-started)/1e6
    policies = [p.public_report() for p in registry.policies.values()]
    standard = next(p for p in registry.policies.values() if p.profile == "standard")
    elevated = next(p for p in registry.policies.values() if p.profile == "elevated")

    rows = []
    record = {
        "transaction_id": "SYNTHETIC-ONLY-9001", "customer_alias": "test-customer",
        "amount_minor_units": 12735, "currency": "INR", "note": "no live customer data",
    }
    with OpenSSLPQC() as crypto:
        recipient = {alg: crypto.keypair(alg) for alg in ("ML-KEM-768", "ML-KEM-1024")}
        signing = {alg: crypto.keypair(alg) for alg in ("ML-DSA-65", "ML-DSA-87")}
        acl = PostQuantumAccessControl(crypto)
        acl.register("operator_standard", "teller", signing["ML-DSA-65"])
        acl.register("operator_elevated", "teller", signing["ML-DSA-87"])

        def fixed():
            e = create_transaction_envelope(crypto, acl, recipient["ML-KEM-768"], signing["ML-DSA-65"],
                actor="operator_standard", service_id=standard.service_id,
                action="initiate_payment", transaction=record)
            receipt = accept_transaction_envelope(crypto, acl, recipient["ML-KEM-768"],
                service_id=standard.service_id, action="initiate_payment", envelope=e)
            assert receipt["transaction"] == record
            return e

        def proposed(policy):
            signer = signing[policy.signature]
            actor = "operator_elevated" if policy.profile == "elevated" else "operator_standard"
            e = create_protected_record(crypto, acl, registry, recipient, signer, actor=actor,
                service_id=policy.service_id, action="initiate_payment", record=record)
            receipt = accept_protected_record(crypto, acl, registry, recipient,
                service_id=policy.service_id, action="initiate_payment", envelope=e)
            assert receipt["record"] == record and receipt["policy_digest"] == policy.policy_digest
            return e

        scenarios = [
            ("Fixed-PQC baseline", "standard", standard.service_id, fixed),
            ("DARP-PQC standard", "standard", standard.service_id, lambda: proposed(standard)),
            ("DARP-PQC elevated", "elevated", elevated.service_id, lambda: proposed(elevated)),
        ]
        for name, profile, service_id, fn in scenarios:
            samples = []
            envelope_size = None
            for _ in range(n):
                start = time.perf_counter_ns()
                envelope = fn()
                samples.append((time.perf_counter_ns()-start)/1e6)
                envelope_size = len(canon(envelope))
            median, p95, mean = stats(samples)
            rows.append({
                "scenario": name, "service_id": service_id, "profile": profile,
                "operations": n, "roundtrip_successes": n, "median_ms": median,
                "p95_ms": p95, "mean_ms": mean,
                "envelope_json_bytes": envelope_size,
            })

        standard_ct, _ = crypto.encapsulate(recipient["ML-KEM-768"])
        elevated_ct, _ = crypto.encapsulate(recipient["ML-KEM-1024"])
        sign_65 = crypto.sign(signing["ML-DSA-65"], b"example")
        sign_87 = crypto.sign(signing["ML-DSA-87"], b"example")
        sizes = {
            "ML-KEM-768_ciphertext_bytes":len(standard_ct),
            "ML-KEM-1024_ciphertext_bytes":len(elevated_ct),
            "ML-DSA-65_signature_bytes":len(sign_65),
            "ML-DSA-87_signature_bytes":len(sign_87),
        }
        info = {
            "openssl_version": crypto.version,
            "python": platform.python_version(),
            "platform": platform.platform(), "machine": platform.machine(),
            "iterations_per_scenario": n,
            "pqc_profiles": {"standard": ["ML-KEM-768", "ML-DSA-65"], "elevated": ["ML-KEM-1024", "ML-DSA-87"]},
            "risk_dataset": "V1 synthetic banking graph",
            "risk_baseline_er": er,
            "assessment_ms_one_shot":round(assessment_ms,3),
            "policy_counts": {
                "standard": sum(p.profile == "standard" for p in registry.policies.values()),
                "elevated": sum(p.profile == "elevated" for p in registry.policies.values()),
            },
            "measurement": "End-to-end wall time for Python+OpenSSL CLI+temp files+JSON+HKDF+AES+ML-KEM+ML-DSA+access control; NOT optimized native primitive latency",
            "conditions": "Research only: local synthetic transactions; no network, HSM, persistence, certificate validation, or production banking integration",
            "artifact_sizes": sizes,
            "notes": "Fixed-PQC baseline is already quantum-resistant. DARP-PQC adds policy binding and risk-based security profile enforcement; does not prove superior resistance to unknown future attacks."
        }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "darp_pqc_workflow_benchmark.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    (OUTPUT / "darp_pqc_policy_selection.json").write_text(json.dumps({"baseline_er": er, "policies": policies},indent=2) + "\n",encoding="utf-8")
    (OUTPUT / "darp_pqc_benchmark_metadata.json").write_text(json.dumps(info,indent=2) + "\n", encoding="utf-8")
    print(f"\nBaseline ER: {er:.6f}")
    print("Policy selection:", info["policy_counts"])
    print("\nComparison (end-to-end OpenSSL CLI timings):")
    for row in rows:
        print(f"  {row['scenario']:<25} median {row['median_ms']:.3f} ms, p95 {row['p95_ms']:.3f} ms, envelope {row['envelope_json_bytes']} bytes")
    print("\nAlgorithm sizes:", sizes)
    print("\nResults: results/tables/darp_pqc_*.{csv,json}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=15)
    args = parser.parse_args()
    main(args.iterations)
