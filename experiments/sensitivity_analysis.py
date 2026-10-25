import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from data_loader import load_data
from risk_model import calculate_direct_risk
from graph_builder import build_graph
from propagation import calculate_service_propagation
from ecosystem_risk import calculate_baseline_ecosystem_risk
from prioritization import calculate_static_priorities

WEIGHT_SCENARIOS = {
    "Equal Weights": {
        "quantum_vulnerability": 0.20,
        "data_sensitivity": 0.20,
        "data_lifetime": 0.20,
        "business_criticality": 0.20,
        "external_exposure": 0.20
    },
    "Quantum Emphasis": {
        "quantum_vulnerability": 0.40,
        "data_sensitivity": 0.15,
        "data_lifetime": 0.15,
        "business_criticality": 0.15,
        "external_exposure": 0.15
    },
    "Business Criticality Emphasis": {
        "quantum_vulnerability": 0.15,
        "data_sensitivity": 0.15,
        "data_lifetime": 0.15,
        "business_criticality": 0.40,
        "external_exposure": 0.15
    },
    "Data Lifetime Emphasis": {
        "quantum_vulnerability": 0.15,
        "data_sensitivity": 0.15,
        "data_lifetime": 0.40,
        "business_criticality": 0.15,
        "external_exposure": 0.15
    },
    "Exposure Emphasis": {
        "quantum_vulnerability": 0.15,
        "data_sensitivity": 0.15,
        "data_lifetime": 0.15,
        "business_criticality": 0.15,
        "external_exposure": 0.40
    }
}

def evaluate_with_weights(
    assets,
    services,
    dependencies,
    weights
):
    weighted_assets = calculate_direct_risk(
        assets,
        weights=weights
    )

    graph = build_graph(
        weighted_assets,
        services,
        dependencies
    )

    (
        propagation_results,
        path_results,
        asset_details
    ) = calculate_service_propagation(
        graph,
        services,
        weighted_assets
    )

    (
        service_risk_results,
        ecosystem_risk
    ) = calculate_baseline_ecosystem_risk(
        weighted_assets,
        services,
        propagation_results
    )

    return {
        "assets": weighted_assets,
        "graph": graph,
        "propagation_results": propagation_results,
        "service_risk_results": service_risk_results,
        "ecosystem_risk": ecosystem_risk
    }

def calculate_remediation_impacts_with_weights(
    assets,
    services,
    dependencies,
    weights,
    vulnerability_threshold=0.25
):
    baseline = evaluate_with_weights(
        assets,
        services,
        dependencies,
        weights
    )

    baseline_er = baseline["ecosystem_risk"]

    candidates = assets[
        assets["quantum_vulnerability"]
        > vulnerability_threshold
    ]

    results = []

    for _, candidate in candidates.iterrows():
        asset_id = candidate["asset_id"]

        remediated_assets = assets.copy()

        remediated_assets.loc[
            remediated_assets["asset_id"] == asset_id,
            "quantum_vulnerability"
        ] = 0.0

        after = evaluate_with_weights(
            remediated_assets,
            services,
            dependencies,
            weights
        )

        er_after = after["ecosystem_risk"]
        delta_er = baseline_er - er_after

        results.append({
            "asset_id": asset_id,
            "asset_name": candidate["asset_name"],
            "tier": candidate["tier"],
            "algorithm": candidate["algorithm"],
            "migration_complexity": candidate["migration_complexity"],
            "ecosystem_risk_before": baseline_er,
            "ecosystem_risk_after": er_after,
            "delta_er": delta_er
        })

    return pd.DataFrame(results)

def run_scenario(
    scenario_name,
    weights,
    assets,
    services,
    dependencies
):
    print("\n")
    print("=" * 75)
    print(f"SENSITIVITY SCENARIO: {scenario_name}")
    print("=" * 75)

    baseline = evaluate_with_weights(
        assets,
        services,
        dependencies,
        weights
    )

    baseline_er = float(
        baseline["ecosystem_risk"]
    )

    print(f"\nBaseline ER: {baseline_er:.6f}")

    remediation_results = calculate_remediation_impacts_with_weights(
        assets,
        services,
        dependencies,
        weights
    )

    priority_results = calculate_static_priorities(
        remediation_results
    )

    if priority_results.empty:
        return {
            "scenario": scenario_name,
            "baseline_er": baseline_er,
            "top_priority_asset": None,
            "top_priority_asset_name": None,
            "top_priority_score": None,
            "top_delta_er": None
        }

    top = priority_results.iloc[0]

    print(
        f"Top Priority Asset: "
        f"{top['asset_id']} - "
        f"{top['asset_name']}"
    )
    print(
        f"Top Priority Score: "
        f"{top['priority_score']:.6f}"
    )
    print(
        f"Top Delta ER: "
        f"{top['delta_er']:.6f}"
    )

    return {
        "scenario": scenario_name,
        "baseline_er": baseline_er,
        "top_priority_asset": top["asset_id"],
        "top_priority_asset_name": top["asset_name"],
        "top_priority_score": top["priority_score"],
        "top_delta_er": top["delta_er"]
    }

def main():
    print("\n")
    print("=" * 75)
    print("     PQC BANKING RISK FRAMEWORK - SENSITIVITY ANALYSIS")
    print("=" * 75)

    assets, services, dependencies = load_data()

    results = []

    for scenario_name, weights in WEIGHT_SCENARIOS.items():
        result = run_scenario(
            scenario_name,
            weights,
            assets,
            services,
            dependencies
        )

        results.append(result)

    results_df = pd.DataFrame(results)

    print("\n")
    print("=" * 100)
    print("                     SENSITIVITY ANALYSIS SUMMARY")
    print("=" * 100)

    display = results_df.copy()

    numeric_columns = [
        "baseline_er",
        "top_priority_score",
        "top_delta_er"
    ]

    for column in numeric_columns:
        if column in display.columns:
            display[column] = (
                display[column].round(6)
            )

    print(
        "\n"
        + display.to_string(
            index=False
        )
    )

    output_dir = (
        PROJECT_ROOT
        / "results"
        / "tables"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        output_dir
        / "sensitivity_analysis.csv"
    )

    results_df.to_csv(
        output_path,
        index=False
    )

    print(
        "\nSensitivity results saved to:"
    )
    print(output_path)

if __name__ == "__main__":
    main()