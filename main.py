import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from data_loader import load_data, validate_data
from risk_model import calculate_direct_risk
from graph_builder import build_graph, print_graph_statistics
from propagation import calculate_service_propagation
from ecosystem_risk import calculate_baseline_ecosystem_risk, print_ecosystem_results
from remediation import calculate_all_remediation_impacts, print_remediation_results
from prioritization import calculate_static_priorities, print_priority_results, dynamic_prioritization, print_dynamic_sequence
from baselines import compare_strategies, print_strategy_comparison

def main():
    print("\n")
    print("=" * 75)
    print("             PQC BANKING RISK FRAMEWORK")
    print("=" * 75)

    print("\n[1] Loading banking ecosystem dataset...")
    assets, services, dependencies = load_data()
    print("Dataset loaded successfully.")

    print("\n[2] Validating dataset...")
    validate_data(
        assets,
        services,
        dependencies
    )

    print("\n[3] Calculating direct quantum risk...")
    assets = calculate_direct_risk(assets)

    print(
        "Direct quantum risk calculated "
        f"for {len(assets)} assets."
    )

    top_direct_risk = (
        assets[
            [
                "asset_id",
                "asset_name",
                "tier",
                "algorithm",
                "direct_risk"
            ]
        ]
        .sort_values(
            by="direct_risk",
            ascending=False
        )
        .head(10)
    )

    print("\nTop 10 Direct-Risk Assets:\n")
    print(top_direct_risk.to_string(index=False))

    print("\n[4] Building multi-tier dependency graph...")

    graph = build_graph(
        assets,
        services,
        dependencies
    )

    print_graph_statistics(graph)

    print("\n[5] Calculating path-aware inherited risk...")

    (
        propagation_results,
        path_results,
        asset_details
    ) = calculate_service_propagation(
        graph,
        services,
        assets
    )

    print("\nService-Level Inherited Quantum Risk:\n")

    propagation_display = (
        propagation_results
        .sort_values(
            by="inherited_quantum_risk",
            ascending=False
        )
        .copy()
    )

    propagation_display["inherited_quantum_risk"] = (
        propagation_display["inherited_quantum_risk"].round(6)
    )

    print(propagation_display.to_string(index=False))

    print(
        f"\nTotal vulnerable dependency paths: "
        f"{len(path_results)}"
    )

    print(
        "\n[6] Calculating ecosystem-wide "
        "quantum risk..."
    )

    (
        service_risk_results,
        ecosystem_risk
    ) = calculate_baseline_ecosystem_risk(
        assets,
        services,
        propagation_results
    )

    print_ecosystem_results(
        service_risk_results,
        ecosystem_risk
    )

    print(
        "\n[7] Simulating individual "
        "PQC remediation actions..."
    )

    remediation_results = calculate_all_remediation_impacts(
        assets,
        services,
        dependencies
    )

    print_remediation_results(
        remediation_results,
        top_n=15
    )

    print(
        "\n[8] Calculating cost-aware "
        "migration priorities..."
    )

    priority_results = calculate_static_priorities(
        remediation_results
    )

    print_priority_results(
        priority_results,
        top_n=15
    )

    print(
        "\n[9] Running dynamic migration prioritization..."
    )

    dynamic_sequence = dynamic_prioritization(
        assets,
        services,
        dependencies,
        max_steps=10
    )

    print_dynamic_sequence(dynamic_sequence)

    print(
        "\n[10] Running equal-budget strategy comparison..."
    )

    MIGRATION_BUDGET = 7.5

    (
        strategy_comparison,
        strategy_sequences
    ) = compare_strategies(
        assets,
        services,
        dependencies,
        migration_budget=MIGRATION_BUDGET
    )

    print_strategy_comparison(strategy_comparison)

    print("\n")
    print("=" * 75)
    print("             FRAMEWORK EXECUTION COMPLETE")
    print("=" * 75)

    print(
        "\nBaseline Ecosystem Quantum Risk (ER): "
        f"{ecosystem_risk:.6f}"
    )

    print("\nCompleted:")
    print("  - Direct quantum risk")
    print("  - Path-aware inherited risk")
    print("  - Ecosystem-wide risk")
    print("  - Remediation simulation")
    print("  - Delta ER calculation")
    print("  - Static cost-aware prioritization")
    print("  - Dynamic migration prioritization")
    print("  - Equal-budget baseline strategy comparison")

    print(
        "\nNext stage: Ablation study and model validation"
    )

if __name__ == "__main__":
    main()