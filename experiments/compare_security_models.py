"""Controlled 3-way comparison for the DARP-PQC banking research prototype.

Run at the PROJECT ROOT:
    python -m experiments.compare_security_models --iterations 20

All three variants use the same S01, ML-KEM-1024, ML-DSA-87 and synthetic
record. This is a locally implemented paper-inspired baseline, NOT a
reproduction of any publication's original protocol or benchmark.

Timings include Python/OpenSSL subprocesses, temp files, signature generation,
access control, serialization and decryption. Provider attestations are simulated.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
import time
from dataclasses import replace
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pqc_layer.access_control import AccessDenied, PostQuantumAccessControl
from pqc_layer.banking_gateway import RiskBoundBankingGateway
from pqc_layer.crypto_backend import OpenSSLPQC, canon
from pqc_layer.darp_pqc import (
    build_policies, create_protected_record, accept_protected_record,
)
from pqc_layer.multitier_assurance import CrossTierAssuranceGate, derive_tier_requirements
from pqc_layer.transaction_demo import create_transaction_envelope, accept_transaction_envelope

ROOT = Path(__file__).resolve().parent.parent
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"


def percentile_95(samples):
    samples = sorted(samples)
    return samples[math.ceil(.95 * len(samples)) - 1]


def save_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_performance_chart(rows):
    labels = ["Fixed PQC\n(reference-inspired)", "DARP-PQC\npolicy only", "DARP-PQC\nfull cross-tier"]
    fig, ax = plt.subplots(figsize=(9.1, 5.2))
    bars = ax.bar(labels, [r["median_ms"] for r in rows], color=["#94a3b8", "#3b82f6", "#0f766e"])
    ax.set_ylabel("Median end-to-end time (ms)")
    ax.set_title("Same service (S01), same ML-KEM-1024 + ML-DSA-87 security suite")
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    for bar, row in zip(bars, rows):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{row["median_ms"]:.1f} ms', ha="center", va="bottom", fontsize=10)
    fig.text(.5, .01, "Prototype wall time includes OpenSSL CLI and temp-file I/O; simulated provider evidence.",
             ha="center", fontsize=9, color="#475569")
    fig.tight_layout(rect=[0, .04, 1, 1])
    fig.savefig(FIGURES / "three_way_latency_comparison.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9.1, 5.2))
    bars = ax.bar(labels, [r["median_envelope_bytes"] / 1024 for r in rows], color=["#94a3b8", "#3b82f6", "#0f766e"])
    ax.set_ylabel("Serialized encrypted envelope (KiB)")
    ax.set_title("Communication artifact size for the same synthetic transaction")
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    for bar, row in zip(bars, rows):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{row["median_envelope_bytes"]:,} B', ha="center", va="bottom", fontsize=10)
    fig.text(.5, .01, "Envelope bytes are local JSON sizes, not on-wire TLS handshake sizes.",
             ha="center", fontsize=9, color="#475569")
    fig.tight_layout(rect=[0, .04, 1, 1])
    fig.savefig(FIGURES / "three_way_envelope_size.png", dpi=180)
    plt.close(fig)


def save_risk_chart():
    """Use the existing experiment's independent migration-baseline output."""
    source = TABLES / "final_strategy_comparison_v1.csv"
    if not source.exists():
        return False
    with source.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows or not {"strategy", "risk_reduction_percent"}.issubset(rows[0]):
        return False
    rows.sort(key=lambda r: -float(r["risk_reduction_percent"]))
    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    labels = [r["strategy"].replace("Proposed Dynamic DeltaER/Cost", "Proposed dynamic ΔER/cost") for r in rows]
    values = [float(r["risk_reduction_percent"]) for r in rows]
    bars = ax.barh(labels[::-1], values[::-1], color=["#64748b", "#64748b", "#64748b", "#0f766e"][:len(values)])
    ax.set_xlabel("Reduction in normalized synthetic ecosystem-risk index (%)")
    ax.set_title("Migration strategies at the same 7.5-unit budget ceiling")
    ax.grid(axis="x", alpha=.2)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(values)*1.23)
    for bar, value in zip(bars, values[::-1]):
        ax.text(bar.get_width() + .6, bar.get_y()+bar.get_height()/2, f"{value:.2f}%", va="center")
    fig.tight_layout()
    fig.savefig(FIGURES / "three_way_migration_baselines.png", dpi=180)
    plt.close(fig)
    return True


def main(n=20):
    if n < 3:
        raise ValueError("Use at least 3 iterations")
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    registry, ecosystem_risk = build_policies(ROOT)
    sid, action = "S01", "initiate_payment"
    policy = registry.get(sid)
    if policy.profile != "elevated":
        raise RuntimeError("This three-way demonstration assumes S01 has an elevated PQC policy")
    requirements = derive_tier_requirements(ROOT)
    selected = requirements[sid]
    if {r.tier for r in selected} != {"Third-Party", "Sub-Tier"}:
        raise RuntimeError("Expected one or more requirements from each external tier")

    record = {
        "transaction_id": "SYNTHETIC-COMPARISON-001",
        "amount_minor_units": 12500,
        "currency": "INR",
        "customer_alias": "NOT_REAL_DATA",
    }

    scenario_names = [
        "Fixed PQC (paper-inspired)",
        "DARP-PQC without tier gate",
        "Full DARP-PQC with tier gate",
    ]
    samples = {name: [] for name in scenario_names}
    bytes_by_scenario = {name: [] for name in scenario_names}
    checks = []

    with OpenSSLPQC() as crypto:
        recipient = {alg: crypto.keypair(alg) for alg in ("ML-KEM-768", "ML-KEM-1024")}
        bank_signer = crypto.keypair("ML-DSA-87")
        access = PostQuantumAccessControl(crypto)
        access.register("research_teller", "teller", bank_signer)
        gate = CrossTierAssuranceGate(crypto, requirements)
        gateway = RiskBoundBankingGateway(crypto, access, registry, recipient, gate)
        provider_signers = {}
        for req in selected:
            provider_signers[req.asset_id] = crypto.keypair("ML-DSA-65")
            gate.register_provider_key(req.asset_id, provider_signers[req.asset_id])

        def fixed():
            env = create_transaction_envelope(
                crypto, access, recipient[policy.kem], bank_signer,
                actor="research_teller", service_id=sid, action=action, transaction=record,
            )
            result = accept_transaction_envelope(
                crypto, access, recipient[policy.kem],
                service_id=sid, action=action, envelope=env,
            )
            assert result["accepted"] and result["transaction"] == record
            return env

        def policy_bound():
            env = create_protected_record(
                crypto, access, registry, recipient, bank_signer,
                actor="research_teller", service_id=sid, action=action, record=record,
            )
            result = accept_protected_record(
                crypto, access, registry, recipient,
                service_id=sid, action=action, envelope=env,
            )
            assert result["accepted"] and result["record"] == record
            return env

        def external_acknowledgements():
            binding = registry.get(sid).binding(action=action)
            return [
                gate.issue(req, provider_signers[req.asset_id], binding=binding, record=record)
                for req in selected
            ]

        def cross_tier():
            env = gateway.protect(
                bank_signer, actor="research_teller", service_id=sid,
                action=action, record=record,
                external_attestations=external_acknowledgements(),
            )
            result = gateway.accept(service_id=sid, action=action, envelope=env)
            assert result["accepted"] and result["record"] == record
            assert result["cross_tier_assurance"]["sub_tier"] >= 1
            assert result["cross_tier_assurance"]["third_party"] >= 1
            return env

        functions = [fixed, policy_bound, cross_tier]
        # Warm-up, not counted. Rotated order reduces systematic order bias.
        for f in functions:
            for _ in range(2):
                f()
        for iteration in range(n):
            for idx in [(iteration+j) % 3 for j in range(3)]:
                begin = time.perf_counter_ns()
                envelope = functions[idx]()
                elapsed_ms = (time.perf_counter_ns() - begin) / 1_000_000
                name = scenario_names[idx]
                samples[name].append(elapsed_ms)
                bytes_by_scenario[name].append(len(canon(envelope)))

        # Verify actual cases, not a made-up "security %". Where there is no
        # cross-tier protocol, the check is NOT IMPLEMENTED, not "cryptography failed".
        checks.extend([
            {"check": "Valid encrypted signed transaction", "fixed_pqc": "ACCEPT", "darp_policy": "ACCEPT", "full_darp": "ACCEPT"},
            {"check": "Enforce third-party acknowledgement", "fixed_pqc": "NOT_IMPLEMENTED", "darp_policy": "NOT_IMPLEMENTED", "full_darp": "ENFORCED"},
            {"check": "Enforce sub-tier acknowledgement", "fixed_pqc": "NOT_IMPLEMENTED", "darp_policy": "NOT_IMPLEMENTED", "full_darp": "ENFORCED"},
        ])

        binding = registry.get(sid).binding(action=action)
        both = external_acknowledgements()
        proof_variations = {
            "Missing sub-tier acknowledgement": both[:1],
            "Missing all external acknowledgements": [],
            "Duplicate external acknowledgement": [both[0], both[0]],
        }
        for label, att in proof_variations.items():
            # Crafted invalid envelopes intentionally bypass the gateway's
            # producer-side check, to test whether the receiver rejects them.
            env = create_protected_record(
                crypto, access, registry, recipient, bank_signer,
                actor="research_teller", service_id=sid, action=action,
                record=record, dependency_attestations=att,
            )
            try:
                accept_protected_record(
                    crypto, access, registry, recipient,
                    service_id=sid, action=action, envelope=env, tier_gate=gate,
                )
                outcome = "INCORRECTLY_ACCEPTED"
            except AccessDenied:
                outcome = "REJECT"
            if outcome != "REJECT":
                raise AssertionError(f"Cross-tier gate did not reject {label}")
            checks.append({"check": label, "fixed_pqc": "NOT_IMPLEMENTED",
                           "darp_policy": "NOT_IMPLEMENTED", "full_darp": outcome})

        # Build fresh, never-before-accepted messages under epoch 1. Then issue
        # a trusted synthetic policy revision (same crypto strength) and verify
        # old transaction policy is rejected by the two risk-bound variants.
        fixed_old = create_transaction_envelope(
            crypto, access, recipient[policy.kem], bank_signer,
            actor="research_teller", service_id=sid, action=action, transaction=record,
        )
        bound_old = create_protected_record(
            crypto, access, registry, recipient, bank_signer,
            actor="research_teller", service_id=sid, action=action, record=record,
        )
        full_old = gateway.protect(
            bank_signer, actor="research_teller", service_id=sid,
            action=action, record=record, external_attestations=external_acknowledgements(),
        )
        new_epoch = policy.epoch + 1
        new_policy_digest = hashlib.sha256(canon({
            "simulated_policy_revision": True, "old_digest": policy.policy_digest,
            "new_epoch": new_epoch,
        })).hexdigest()
        registry.replace(replace(policy, epoch=new_epoch, policy_digest=new_policy_digest))

        fixed_accepted = accept_transaction_envelope(
            crypto, access, recipient[policy.kem],
            service_id=sid, action=action, envelope=fixed_old,
        )["accepted"]
        def is_rejected(fn):
            try:
                fn()
                return False
            except AccessDenied:
                return True
        bound_rejected = is_rejected(lambda: accept_protected_record(
            crypto, access, registry, recipient, service_id=sid, action=action,
            envelope=bound_old,
        ))
        full_rejected = is_rejected(lambda: gateway.accept(
            service_id=sid, action=action, envelope=full_old,
        ))
        if not (fixed_accepted and bound_rejected and full_rejected):
            raise AssertionError("Expected policy-epoch comparison outcomes were not observed")
        checks.append({"check": "Old policy epoch after synthetic revision",
                       "fixed_pqc": "NO_POLICY_EPOCH_CHECK",
                       "darp_policy": "REJECT", "full_darp": "REJECT"})
        host = {
            "platform": platform.platform(), "python": platform.python_version(),
            "openssl": crypto.version, "iterations_per_variant": n,
            "algorithm_suite": "ML-KEM-1024 + ML-DSA-87 + AES-256-GCM",
            "service": sid, "input_transaction": "Synthetic only",
        }

    rows = []
    for idx, name in enumerate(scenario_names):
        latency = samples[name]
        sizes = bytes_by_scenario[name]
        rows.append({
            "variant": name,
            "service_id": sid,
            "kem": policy.kem,
            "signature": policy.signature,
            "iterations": n,
            "median_ms": round(statistics.median(latency), 3),
            "mean_ms": round(statistics.mean(latency), 3),
            "p95_ms": round(percentile_95(latency), 3),
            "median_envelope_bytes": int(statistics.median(sizes)),
            "provider_signatures_per_transaction": len(selected) if idx == 2 else 0,
        })

    save_csv(TABLES / "three_way_security_performance.csv", rows)
    save_csv(TABLES / "three_way_security_checks.csv", checks)
    metadata = {"description": "Controlled same-host, same-service and same-suite comparison",
                "host": host, "baseline_is_paper_inspired_not_exact_reproduction": True,
                "scope": "No live customers, vendors, network, TLS, HSM or production keys",
                "security_claims": "Tests demonstrate implemented policy enforcement, not a security proof or vendor PQC deployment",
                "ecosystem_risk_before_simulated_migration": ecosystem_risk}
    (TABLES / "three_way_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    save_performance_chart(rows)
    risk_chart_exists = save_risk_chart()

    markdown = [
        "# Three-way DARP-PQC comparison — controlled local prototype",
        "",
        "Fixed PQC is an **in-project, paper-inspired baseline**; it is NOT the original authors' code.",
        "All versions use synthetic Core Banking (S01), ML-KEM-1024, ML-DSA-87, AES-256-GCM,",
        "the same test payload, the same host and the same number of repetitions.",
        "The cross-tier variant adds signed simulated third-party and sub-tier acknowledgements.",
        "",
        "| Variant | Median time (ms) | p95 (ms) | Envelope (bytes) | Extra provider signatures |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        markdown.append(f'| {r["variant"]} | {r["median_ms"]:.3f} | {r["p95_ms"]:.3f} | {r["median_envelope_bytes"]:,} | {r["provider_signatures_per_transaction"]} |')
    markdown.extend([
        "", "## Security enforcement", "",
        "| Check | Fixed PQC | Risk-bound DARP | Full DARP |",
        "|---|---|---|---|",
    ])
    for c in checks:
        markdown.append(f'| {c["check"]} | {c["fixed_pqc"]} | {c["darp_policy"]} | {c["full_darp"]} |')
    markdown.extend([
        "", "## Research interpretation", "",
        "- Fixed PQC already encrypts and signs data with quantum-resistant algorithms.",
        "- Risk-bound DARP additionally ties transactions to a bank service's authoritative risk policy and epoch.",
        "- Full DARP additionally requires signed acknowledgements from graph-selected third-party and sub-tier dependencies.",
        "- Missing/duplicate acknowledgements are **not protocol checks** in the first two variants; mark N/A, not unsafe.",
        "- These are policy-enforcement differences; they do not prove superior primitive cryptographic strength.",
        "- Median timings include Python/OpenSSL CLI, temp-file I/O, local attestations and JSON serialization.",
        "- No live bank providers, TLS session establishment, network transport or audited identity infrastructure.",
        "- The ecosystem-risk improvement chart is a separate synthetic optimization experiment, not measured in the reference paper.",
        "", "## Reference context", "",
        "Olushola and Meenakshi (2026), *Design and implementation of an authenticated post-quantum session protocol using ML-KEM (Kyber), ML-DSA (Dilithium), and AES-256-GCM*, Frontiers in Physics.",
        "https://doi.org/10.3389/fphy.2025.1723966",
        "Their primitive microbenchmarks are **not directly comparable** to this Python/OpenSSL end-to-end experiment.",
        "The published paper's security-session protocol is not reproduced here; fixed PQC is our own functional comparator.",
        "", "## Plots", "",
        "- `results/figures/three_way_latency_comparison.png`",
        "- `results/figures/three_way_envelope_size.png`",
        "- `results/figures/three_way_migration_baselines.png` (if the prior V1 result table is present)",
    ])
    (TABLES / "three_way_guide_summary.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")

    print("\nTHREE-WAY SECURITY COMPARISON (S01, same ML-KEM-1024 + ML-DSA-87):")
    for row in rows:
        print(f'  {row["variant"]:<33} median {row["median_ms"]:>8.3f} ms  '
              f'p95 {row["p95_ms"]:>8.3f} ms  size {row["median_envelope_bytes"]:,} B')
    print("\nSECURITY FEATURE CHECKS:")
    for item in checks:
        print(f'  {item["check"]}: {item["fixed_pqc"]} / {item["darp_policy"]} / {item["full_darp"]}')
    print("\nSaved tables/markdown to:", TABLES)
    print("Saved charts to:", FIGURES)
    if not risk_chart_exists:
        print("Risk migration chart skipped: run python -m experiments.final_evaluation first")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()
    main(args.iterations)
