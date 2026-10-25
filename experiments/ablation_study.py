import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
TABLE_DIR = PROJECT_ROOT / "results" / "tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_loader import load_data, validate_data
from remediation import (
    evaluate_ecosystem,
    simulate_asset_remediation,
    calculate_all_remediation_impacts,
)
from prioritization import calculate_static_priorities, calculate_migration_cost
from baselines import run_proposed_under_budget

MIGRATION_BUDGET = 7.5
VULNERABILITY_THRESHOLD = 0.25


def _summarize(name, sequence, initial_er, budget):
    if sequence.empty:
        return {
            "variant": name,
            "migration_budget": budget,
            "budget_used": 0.0,
            "assets_migrated": 0,
            "initial_er": initial_er,
            "final_er": initial_er,
            "risk_reduction": 0.0,
            "risk_reduction_percent": 0.0,
            "risk_reduction_per_cost": 0.0,
        }

    final_er = float(sequence.iloc[-1]["ecosystem_risk_after"])
    budget_used = float(sequence.iloc[-1]["cumulative_cost"])
    reduction = initial_er - final_er
    return {
        "variant": name,
        "migration_budget": budget,
        "budget_used": budget_used,
        "assets_migrated": len(sequence),
        "initial_er": initial_er,
        "final_er": final_er,
        "risk_reduction": reduction,
        "risk_reduction_percent": (100.0 * reduction / initial_er) if initial_er > 0 else 0.0,
        "risk_reduction_per_cost": reduction / budget_used if budget_used > 0 else 0.0,
    }


def run_static_initial_priority(assets, services, dependencies, budget):
    baseline = evaluate_ecosystem(assets, services, dependencies)
    initial_er = float(baseline["ecosystem_risk"])

    impacts = calculate_all_remediation_impacts(
        assets, services, dependencies, VULNERABILITY_THRESHOLD
    )
    priorities = calculate_static_priorities(impacts)

    current_assets = assets.copy()
    current_er = initial_er
    used = 0.0
    rows = []
    step = 1

    for _, candidate in priorities.iterrows():
        if candidate["delta_er"] <= 0:
            continue
        cost = float(candidate["migration_cost"])
        if used + cost > budget + 1e-12:
            continue

        er_before = current_er
        current_assets = simulate_asset_remediation(current_assets, candidate["asset_id"], 0.0)
        current_er = float(evaluate_ecosystem(current_assets, services, dependencies)["ecosystem_risk"])
        used += cost

        rows.append({
            "variant": "Static initial DeltaER/Cost",
            "step": step,
            "asset_id": candidate["asset_id"],
            "asset_name": candidate["asset_name"],
            "migration_cost": cost,
            "cumulative_cost": used,
            "ecosystem_risk_before": er_before,
            "ecosystem_risk_after": current_er,
            "delta_er": er_before - current_er,
        })
        step += 1

    return pd.DataFrame(rows), initial_er


def run_dynamic_delta_only(assets, services, dependencies, budget):
    baseline = evaluate_ecosystem(assets, services, dependencies)
    initial_er = float(baseline["ecosystem_risk"])
    current_assets = assets.copy()
    current_er = initial_er
    used = 0.0
    rows = []
    step = 1

    while True:
        remaining = budget - used
        if remaining <= 1e-12:
            break

        impacts = calculate_all_remediation_impacts(
            current_assets, services, dependencies, VULNERABILITY_THRESHOLD
        )
        if impacts.empty:
            break

        impacts = impacts.copy()
        impacts["migration_cost"] = impacts["migration_complexity"].apply(calculate_migration_cost)
        affordable = impacts[
            (impacts["delta_er"] > 0)
            & (impacts["migration_cost"] <= remaining + 1e-12)
        ].sort_values(by=["delta_er", "asset_id"], ascending=[False, True])

        if affordable.empty:
            break

        selected = affordable.iloc[0]
        er_before = current_er
        cost = float(selected["migration_cost"])
        current_assets = simulate_asset_remediation(current_assets, selected["asset_id"], 0.0)
        current_er = float(evaluate_ecosystem(current_assets, services, dependencies)["ecosystem_risk"])
        used += cost

        rows.append({
            "variant": "Dynamic DeltaER only (no cost normalization)",
            "step": step,
            "asset_id": selected["asset_id"],
            "asset_name": selected["asset_name"],
            "migration_cost": cost,
            "cumulative_cost": used,
            "ecosystem_risk_before": er_before,
            "ecosystem_risk_after": current_er,
            "delta_er": er_before - current_er,
        })
        step += 1

    return pd.DataFrame(rows), initial_er


def filter_topology(assets, services, dependencies, allowed_tiers):
    reduced_assets = assets[assets["tier"].isin(allowed_tiers)].copy()
    valid_nodes = set(reduced_assets["asset_id"].astype(str)) | set(services["service_id"].astype(str))
    reduced_dependencies = dependencies[
        dependencies["source_id"].astype(str).isin(valid_nodes)
        & dependencies["target_id"].astype(str).isin(valid_nodes)
    ].copy()
    return reduced_assets, reduced_dependencies


def main():
    print("=" * 90)
    print("PQC BANKING RISK FRAMEWORK - ABLATION STUDY")
    print("=" * 90)

    assets, services, dependencies = load_data()
    validate_data(assets, services, dependencies)

    full_eval = evaluate_ecosystem(assets, services, dependencies)
    full_er = float(full_eval["ecosystem_risk"])

    topology_rows = [{
        "topology_variant": "Full Internal + Third-Party + Sub-Tier",
        "assets": len(assets),
        "dependencies": len(dependencies),
        "ecosystem_risk": full_er,
        "risk_change_vs_full": 0.0,
    }]

    for name, tiers in [
        ("No Sub-Tier", ["Internal", "Third-Party"]),
        ("Internal Only", ["Internal"]),
    ]:
        reduced_assets, reduced_dependencies = filter_topology(
            assets, services, dependencies, tiers
        )
        er = float(evaluate_ecosystem(reduced_assets, services, reduced_dependencies)["ecosystem_risk"])
        topology_rows.append({
            "topology_variant": name,
            "assets": len(reduced_assets),
            "dependencies": len(reduced_dependencies),
            "ecosystem_risk": er,
            "risk_change_vs_full": er - full_er,
        })

    topology_df = pd.DataFrame(topology_rows)

    print("\nTopology ablation:\n")
    print(topology_df.round(6).to_string(index=False))

    full_sequence = run_proposed_under_budget(
        assets, services, dependencies, MIGRATION_BUDGET, VULNERABILITY_THRESHOLD
    )
    full_summary = _summarize(
        "Full dynamic DeltaER/Cost", full_sequence, full_er, MIGRATION_BUDGET
    )

    static_sequence, static_initial = run_static_initial_priority(
        assets, services, dependencies, MIGRATION_BUDGET
    )
    delta_sequence, delta_initial = run_dynamic_delta_only(
        assets, services, dependencies, MIGRATION_BUDGET
    )

    priority_df = pd.DataFrame([
        full_summary,
        _summarize("Static initial DeltaER/Cost", static_sequence, static_initial, MIGRATION_BUDGET),
        _summarize("Dynamic DeltaER only (no cost normalization)", delta_sequence, delta_initial, MIGRATION_BUDGET),
    ]).sort_values(by="risk_reduction", ascending=False).reset_index(drop=True)
    priority_df["performance_rank"] = range(1, len(priority_df) + 1)

    print("\nPrioritization ablation:\n")
    print(priority_df.round(6).to_string(index=False))

    topology_df.to_csv(TABLE_DIR / "ablation_topology.csv", index=False)
    priority_df.to_csv(TABLE_DIR / "ablation_prioritization.csv", index=False)
    full_sequence.to_csv(TABLE_DIR / "ablation_full_dynamic_sequence.csv", index=False)
    static_sequence.to_csv(TABLE_DIR / "ablation_static_sequence.csv", index=False)
    delta_sequence.to_csv(TABLE_DIR / "ablation_delta_only_sequence.csv", index=False)

    print("\nSaved ablation tables to results/tables/.")


if __name__ == "__main__":
    main()
