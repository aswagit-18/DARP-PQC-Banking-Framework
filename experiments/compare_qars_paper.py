"""Literature-derived QARS baseline vs DARP-PQC on the same synthetic banking dataset.

Reference: Grigaliunas & Bruzgiene, 'Towards a Unified Quantum Risk Assessment',
Electronics 2025, 14(17), 3338, doi:10.3390/electronics14173338.

QARS ranking model: Equations (2) to (4), paper-authorized linear timing
surrogate; asset vulnerability/harvestability from Equation (8).

Synthetic mappings not present in the published paper:
* 0..1 data_lifetime --> 1..15 years of confidentiality (X)
* 0..1 migration_complexity --> 1..5 years of migration (Y)
* fixed CRQC horizon Z = 12 years (illustrative assumption, NOT prediction)
* normalized data_sensitivity --> S
* binary algorithm vulnerability (over 0.25) and external_exposure --> E
These mappings must be disclosed. Sensitivity tests recommended.

QARS produces a ranking ONLY. We apply exactly the SAME simulated remediation
operator, cost budget, and ecosystem-risk evaluation to both strategies.
No claim is made that this reproduces the original authors' experiments.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from data_loader import load_data, validate_data
from remediation import evaluate_ecosystem, simulate_asset_remediation
from baselines import run_proposed_under_budget, summarize_strategy
from prioritization import calculate_migration_cost

BUDGET = 7.5
CRQC_HORIZON_YEARS = 12.0
VULNERABILITY_THRESHOLD = 0.25


def qars_scores(assets: pd.DataFrame, weights=(1/3, 1/3, 1/3)) -> pd.DataFrame:
    """Published QARS formula with explicitly declared synthetic input mapping."""
    df = assets.copy()
    x = 1.0 + 14.0 * df["data_lifetime"].astype(float)
    y = 1.0 + 4.0 * df["migration_complexity"].astype(float)
    # f_time(r) = min(1, r), a simplified surrogate explicitly allowed in paper.
    t = np.minimum(1.0, (x+y) / CRQC_HORIZON_YEARS)
    s = df["data_sensitivity"].astype(float)
    visibility = (df["quantum_vulnerability"] > VULNERABILITY_THRESHOLD).astype(float)
    e = visibility * df["external_exposure"].astype(float)
    df["qars_timeline"] = t
    df["qars_sensitivity"] = s
    df["qars_exposure"] = e
    df["qars_score"] = weights[0]*t + weights[1]*s + weights[2]*e
    return df


def run_qars_strategy(assets, services, dependencies, budget: float, strategy_name: str, weights):
    current = assets.copy()
    first = float(evaluate_ecosystem(current, services, dependencies)["ecosystem_risk"])
    current_er = first
    used = 0.0
    records = []
    while budget - used > 1e-12:
        ranked = qars_scores(current, weights)
        ranked = ranked[ranked["quantum_vulnerability"] > VULNERABILITY_THRESHOLD]
        ranked = ranked.sort_values(["qars_score", "asset_id"], ascending=[False, True])
        chosen = None
        for _, candidate in ranked.iterrows():
            cost = calculate_migration_cost(candidate["migration_complexity"])
            if cost <= budget - used + 1e-12:
                chosen = candidate
                break
        if chosen is None:
            break
        cost = float(calculate_migration_cost(chosen["migration_complexity"]))
        current = simulate_asset_remediation(current, chosen["asset_id"], 0.0)
        after = float(evaluate_ecosystem(current, services, dependencies)["ecosystem_risk"])
        used += cost
        records.append({
            "strategy": strategy_name, "step": len(records)+1,
            "asset_id": chosen["asset_id"], "asset_name": chosen["asset_name"],
            "tier": chosen["tier"], "qars_score": float(chosen["qars_score"]),
            "migration_cost": cost, "cumulative_cost": used,
            "ecosystem_risk_before": current_er, "ecosystem_risk_after": after,
            "delta_er": current_er-after, "cumulative_delta_er": first-after,
        })
        current_er = after
    return pd.DataFrame(records)


def main():
    os.environ["PQC_DATASET"] = "v1"
    assets, services, deps = load_data()
    validate_data(assets, services, deps)
    before = float(evaluate_ecosystem(assets, services, deps)["ecosystem_risk"])
    output_dir = PROJECT_ROOT / "results" / "tables"
    figure_dir = PROJECT_ROOT / "results" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    profiles = [
        ("Published QARS (equal weights)", (1/3, 1/3, 1/3)),
        ("Published QARS (finance weights)", (.4, .4, .2)),
    ]
    sequences = {}
    for name, weights in profiles:
        sequences[name] = run_qars_strategy(assets, services, deps, BUDGET, name, weights)
        sequences[name].to_csv(output_dir / ("qars_equal_sequence.csv" if name.endswith("equal weights)") else "qars_finance_sequence.csv"), index=False)

    # Retain the original DARP-PQC implementation unmodified.
    print("\nRunning existing DARP-PQC dynamic DeltaER/cost strategy...")
    name = "Proposed DARP-PQC DeltaER/Cost"
    sequences[name] = run_proposed_under_budget(assets, services, deps, BUDGET)
    sequences[name].to_csv(output_dir / "qars_comparison_proposed_sequence.csv", index=False)

    rows=[]
    for strategy, sequence in sequences.items():
        row = summarize_strategy(sequence, strategy, before, BUDGET)
        row["risk_reduction_percent"] = 100*(row["initial_er"]-row["final_er"])/row["initial_er"]
        rows.append(row)
    summary = pd.DataFrame(rows)
    summary.to_csv(output_dir / "qars_paper_vs_darp_comparison.csv", index=False)
    qars_scores(assets).sort_values("qars_score", ascending=False).to_csv(output_dir / "qars_literature_derived_asset_scores.csv",index=False)

    fig, ax = plt.subplots(figsize=(9,5))
    bars = ax.bar(summary["strategy"], summary["risk_reduction_percent"])
    ax.set_ylabel("Modeled ecosystem-risk reduction (%)")
    ax.set_title("Published QARS ranking vs DARP-PQC: common V1 dataset, 7.5 cost budget")
    ax.tick_params(axis='x', labelrotation=14)
    ax.set_ylim(0,max(summary['risk_reduction_percent'])*1.2)
    for bar, value in zip(bars,summary['risk_reduction_percent']):
        ax.annotate(f"{value:.2f}%", (bar.get_x()+bar.get_width()/2,bar.get_height()), ha="center",va="bottom")
    fig.tight_layout()
    fig.savefig(figure_dir / "qars_paper_vs_darp_risk_reduction.png",dpi=180)
    plt.close(fig)

    print("\n================ LITERATURE-DERIVED HEAD-TO-HEAD COMPARISON ================")
    print(summary[["strategy","budget_used","number_of_assets_migrated","initial_er","final_er","risk_reduction_percent"]].round(6).to_string(index=False))
    print("\nSaved results/tables/qars_paper_vs_darp_comparison.csv")
    print("Saved results/figures/qars_paper_vs_darp_risk_reduction.png")
    print("\nCAVEAT: This is QARS from the published paper REIMPLEMENTED on OUR data;")
    print("the QARS numeric result is NOT a number reported by its authors.")
    print("Inputs X/Y/Z are illustrative synthetic assumptions, not real estimates.")


if __name__ == "__main__":
    main()
