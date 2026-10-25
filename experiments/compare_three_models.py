from pathlib import Path
import sys
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
TABLE_DIR = PROJECT_ROOT / "results" / "tables"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from data_loader import load_data, validate_data
from graph_builder import build_graph
from remediation import evaluate_ecosystem, simulate_asset_remediation

MIGRATION_BUDGET = 7.5
VULNERABILITY_THRESHOLD = 0.25
MAX_PATH_LENGTH = 6

EXISTING_MODEL = "Existing Probability x Impact"
BASE_PAPER_MODEL = "Base-Paper-Inspired Dependency"
PROPOSED_MODEL = "Proposed Banking Ecosystem Model"

def check_required_columns(assets):
    required = [
        "asset_id",
        "asset_name",
        "tier",
        "quantum_vulnerability",
        "external_exposure",
        "data_sensitivity",
        "data_lifetime",
        "business_criticality",
        "hndl_exposure",
        "migration_complexity"
    ]

    missing = [
        column
        for column in required
        if column not in assets.columns
    ]

    if missing:
        raise ValueError(
            "Missing required asset columns: "
            + ", ".join(missing)
        )

def get_migration_cost(asset_row):
    cost = float(
        asset_row["migration_complexity"]
    )

    if cost <= 0:
        raise ValueError(
            "migration_complexity must be greater than zero."
        )

    return cost

def calculate_existing_model_scores(assets):
    result = assets.copy()

    result["probability_proxy"] = (
        0.50 * result["quantum_vulnerability"]
        + 0.50 * result["external_exposure"]
    )

    result["impact_proxy"] = (
        0.50 * result["data_sensitivity"]
        + 0.50 * result["business_criticality"]
    )

    result["model_score"] = (
        result["probability_proxy"]
        * result["impact_proxy"]
    )

    result = result.sort_values(
        by=["model_score", "asset_id"],
        ascending=[False, True]
    ).reset_index(drop=True)

    return result

def calculate_path_strength(graph, path):
    strength = 1.0

    for index in range(len(path) - 1):
        source = path[index]
        target = path[index + 1]

        edge = graph.get_edge_data(
            source,
            target
        )

        if edge is None:
            return 0.0

        edge_strength = float(
            edge.get(
                "dependency_strength",
                1.0
            )
        )

        strength *= edge_strength

    return strength

def calculate_base_paper_scores(
    assets,
    services,
    dependencies
):
    graph = build_graph(
        assets,
        services,
        dependencies
    )

    service_ids = (
        services["service_id"]
        .astype(str)
        .tolist()
    )

    result = assets.copy()
    dependency_scores = []

    for _, asset in result.iterrows():
        asset_id = str(
            asset["asset_id"]
        )

        service_strengths = []

        for service_id in service_ids:
            strongest_path = 0.0

            if service_id not in graph:
                service_strengths.append(0.0)
                continue

            if asset_id not in graph:
                service_strengths.append(0.0)
                continue

            try:
                paths = nx.all_simple_paths(
                    graph,
                    source=service_id,
                    target=asset_id,
                    cutoff=MAX_PATH_LENGTH
                )

                for path in paths:
                    strength = calculate_path_strength(
                        graph,
                        path
                    )

                    if strength > strongest_path:
                        strongest_path = strength

            except nx.NetworkXNoPath:
                strongest_path = 0.0

            service_strengths.append(
                strongest_path
            )

        if service_strengths:
            dependency_exposure = (
                sum(service_strengths)
                / len(service_strengths)
            )
        else:
            dependency_exposure = 0.0

        dependency_scores.append(
            dependency_exposure
        )

    result["dependency_exposure"] = (
        dependency_scores
    )

    result["security_requirement"] = (
        result[
            [
                "data_sensitivity",
                "data_lifetime"
            ]
        ].mean(axis=1)
    )

    result["security_gap"] = (
        result["quantum_vulnerability"]
        * result["security_requirement"]
    )

    result["model_score"] = (
        result["security_gap"]
        * result["dependency_exposure"]
    )

    result = result.sort_values(
        by=["model_score", "asset_id"],
        ascending=[False, True]
    ).reset_index(drop=True)

    return result

def filter_vulnerable_assets(ranking):
    return ranking[
        ranking["quantum_vulnerability"]
        > VULNERABILITY_THRESHOLD
    ].copy()

def run_static_model(
    model_name,
    rank_function,
    assets,
    services,
    dependencies
):
    current_assets = assets.copy()

    baseline = evaluate_ecosystem(
        current_assets,
        services,
        dependencies
    )

    initial_er = float(
        baseline["ecosystem_risk"]
    )

    current_er = initial_er
    budget_used = 0.0
    sequence = []
    step = 1

    while True:
        remaining_budget = (
            MIGRATION_BUDGET
            - budget_used
        )

        if remaining_budget <= 1e-12:
            break

        if model_name == EXISTING_MODEL:
            ranking = rank_function(
                current_assets
            )
        else:
            ranking = rank_function(
                current_assets,
                services,
                dependencies
            )

        ranking = filter_vulnerable_assets(
            ranking
        )

        if ranking.empty:
            break

        selected = None

        for _, candidate in ranking.iterrows():
            cost = get_migration_cost(
                candidate
            )

            if cost <= remaining_budget + 1e-12:
                selected = candidate
                break

        if selected is None:
            break

        asset_id = selected["asset_id"]
        migration_cost = get_migration_cost(
            selected
        )
        er_before = current_er

        current_assets = simulate_asset_remediation(
            current_assets,
            asset_id,
            remediated_quantum_vulnerability=0.0
        )

        after = evaluate_ecosystem(
            current_assets,
            services,
            dependencies
        )

        er_after = float(
            after["ecosystem_risk"]
        )

        delta_er = er_before - er_after
        budget_used += migration_cost

        sequence.append({
            "model": model_name,
            "step": step,
            "asset_id": asset_id,
            "asset_name": selected["asset_name"],
            "tier": selected["tier"],
            "algorithm": selected["algorithm"],
            "ranking_score": float(
                selected["model_score"]
            ),
            "migration_cost": migration_cost,
            "cumulative_cost": budget_used,
            "ecosystem_risk_before": er_before,
            "ecosystem_risk_after": er_after,
            "delta_er": delta_er,
            "cumulative_delta_er": initial_er - er_after
        })

        current_er = er_after
        step += 1

    return pd.DataFrame(sequence), initial_er

def run_proposed_model(
    assets,
    services,
    dependencies
):
    current_assets = assets.copy()

    baseline = evaluate_ecosystem(
        current_assets,
        services,
        dependencies
    )

    initial_er = float(
        baseline["ecosystem_risk"]
    )

    current_er = initial_er
    budget_used = 0.0
    sequence = []
    step = 1

    while True:
        remaining_budget = (
            MIGRATION_BUDGET
            - budget_used
        )

        if remaining_budget <= 1e-12:
            break

        vulnerable = current_assets[
            current_assets["quantum_vulnerability"]
            > VULNERABILITY_THRESHOLD
        ].copy()

        if vulnerable.empty:
            break

        candidate_results = []

        for _, candidate in vulnerable.iterrows():
            migration_cost = get_migration_cost(
                candidate
            )

            if migration_cost > remaining_budget + 1e-12:
                continue

            candidate_assets = simulate_asset_remediation(
                current_assets,
                candidate["asset_id"],
                remediated_quantum_vulnerability=0.0
            )

            after = evaluate_ecosystem(
                candidate_assets,
                services,
                dependencies
            )

            er_after = float(
                after["ecosystem_risk"]
            )

            delta_er = current_er - er_after
            priority = delta_er / migration_cost

            candidate_results.append({
                "asset_id": candidate["asset_id"],
                "asset_name": candidate["asset_name"],
                "tier": candidate["tier"],
                "algorithm": candidate["algorithm"],
                "migration_cost": migration_cost,
                "er_after": er_after,
                "delta_er": delta_er,
                "priority": priority
            })

        if not candidate_results:
            break

        candidate_df = pd.DataFrame(
            candidate_results
        )

        candidate_df = candidate_df[
            candidate_df["delta_er"] > 0
        ]

        if candidate_df.empty:
            break

        candidate_df = (
            candidate_df
            .sort_values(
                by=["priority", "delta_er"],
                ascending=[False, False]
            )
            .reset_index(drop=True)
        )

        selected = candidate_df.iloc[0]

        asset_id = selected["asset_id"]
        migration_cost = float(
            selected["migration_cost"]
        )
        er_before = current_er
        er_after = float(
            selected["er_after"]
        )
        delta_er = float(
            selected["delta_er"]
        )
        priority = float(
            selected["priority"]
        )

        current_assets = simulate_asset_remediation(
            current_assets,
            asset_id,
            remediated_quantum_vulnerability=0.0
        )

        budget_used += migration_cost

        sequence.append({
            "model": PROPOSED_MODEL,
            "step": step,
            "asset_id": asset_id,
            "asset_name": selected["asset_name"],
            "tier": selected["tier"],
            "algorithm": selected["algorithm"],
            "ranking_score": priority,
            "migration_cost": migration_cost,
            "cumulative_cost": budget_used,
            "ecosystem_risk_before": er_before,
            "ecosystem_risk_after": er_after,
            "delta_er": delta_er,
            "cumulative_delta_er": initial_er - er_after
        })

        current_er = er_after
        step += 1

    return pd.DataFrame(sequence), initial_er

def summarize_model(
    model_name,
    sequence,
    initial_er
):
    if sequence.empty:
        return {
            "model": model_name,
            "migration_budget": MIGRATION_BUDGET,
            "budget_used": 0.0,
            "assets_migrated": 0,
            "initial_er": initial_er,
            "final_er": initial_er,
            "risk_reduction": 0.0,
            "risk_reduction_percent": 0.0,
            "risk_reduction_per_cost": 0.0
        }

    final_er = float(
        sequence.iloc[-1]["ecosystem_risk_after"]
    )

    budget_used = float(
        sequence.iloc[-1]["cumulative_cost"]
    )

    reduction = initial_er - final_er

    if initial_er > 0:
        reduction_percent = (
            reduction
            / initial_er
            * 100
        )
    else:
        reduction_percent = 0.0

    if budget_used > 0:
        efficiency = (
            reduction
            / budget_used
        )
    else:
        efficiency = 0.0

    return {
        "model": model_name,
        "migration_budget": MIGRATION_BUDGET,
        "budget_used": budget_used,
        "assets_migrated": len(sequence),
        "initial_er": initial_er,
        "final_er": final_er,
        "risk_reduction": reduction,
        "risk_reduction_percent": reduction_percent,
        "risk_reduction_per_cost": efficiency
    }

def print_sequence(title, sequence):
    print("\n")
    print("=" * 110)
    print(title)
    print("=" * 110)

    if sequence.empty:
        print("No migrations selected.")
        return

    display_columns = [
        "step",
        "asset_id",
        "asset_name",
        "tier",
        "algorithm",
        "ranking_score",
        "migration_cost",
        "cumulative_cost",
        "ecosystem_risk_after",
        "cumulative_delta_er"
    ]

    display = sequence[
        display_columns
    ].copy()

    numeric_columns = [
        "ranking_score",
        "migration_cost",
        "cumulative_cost",
        "ecosystem_risk_after",
        "cumulative_delta_er"
    ]

    for column in numeric_columns:
        display[column] = (
            display[column].round(6)
        )

    print(
        display.to_string(
            index=False
        )
    )

def save_results(
    comparison,
    existing_sequence,
    base_sequence,
    proposed_sequence
):
    comparison.to_csv(
        TABLE_DIR / "three_model_comparison.csv",
        index=False
    )

    existing_sequence.to_csv(
        TABLE_DIR / "existing_model_sequence.csv",
        index=False
    )

    base_sequence.to_csv(
        TABLE_DIR / "base_paper_model_sequence.csv",
        index=False
    )

    proposed_sequence.to_csv(
        TABLE_DIR / "proposed_model_sequence.csv",
        index=False
    )

def plot_final_risk(comparison):
    data = comparison.sort_values(
        "final_er",
        ascending=True
    )

    plt.figure(figsize=(11, 6))

    bars = plt.barh(
        data["model"],
        data["final_er"]
    )

    plt.xlabel("Final Ecosystem Quantum Risk")
    plt.ylabel("Model")
    plt.title("Existing vs Base Paper vs Proposed Model")

    for bar, value in zip(
        bars,
        data["final_er"]
    ):
        plt.text(
            value + 0.002,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.4f}",
            va="center"
        )

    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "three_model_final_risk.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

def plot_risk_reduction(comparison):
    data = comparison.sort_values(
        "risk_reduction",
        ascending=False
    )

    plt.figure(figsize=(11, 6))

    bars = plt.barh(
        data["model"],
        data["risk_reduction"]
    )

    plt.xlabel("Ecosystem Risk Reduction")
    plt.ylabel("Model")
    plt.title("Risk Reduction Under Equal Migration Budget")
    plt.gca().invert_yaxis()

    for bar, value in zip(
        bars,
        data["risk_reduction"]
    ):
        plt.text(
            value + 0.0001,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.5f}",
            va="center"
        )

    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "three_model_risk_reduction.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

def plot_risk_vs_cost(
    comparison,
    sequences
):
    plt.figure(figsize=(11, 7))

    for model_name, sequence in sequences.items():
        summary = comparison[
            comparison["model"] == model_name
        ]

        if summary.empty:
            continue

        initial_er = float(
            summary.iloc[0]["initial_er"]
        )

        costs = [0.0]
        risks = [initial_er]

        if not sequence.empty:
            costs.extend(
                sequence["cumulative_cost"].tolist()
            )

            risks.extend(
                sequence["ecosystem_risk_after"].tolist()
            )

        plt.plot(
            costs,
            risks,
            marker="o",
            label=model_name
        )

    plt.xlabel("Cumulative Migration Cost")
    plt.ylabel("Ecosystem Quantum Risk")
    plt.title("Risk Reduction as Migration Budget is Consumed")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        FIGURE_DIR / "three_model_risk_vs_cost.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

def save_initial_rankings(
    assets,
    services,
    dependencies
):
    existing = calculate_existing_model_scores(
        assets
    )

    base = calculate_base_paper_scores(
        assets,
        services,
        dependencies
    )

    existing_table = existing[
        [
            "asset_id",
            "asset_name",
            "model_score"
        ]
    ].copy()

    existing_table = existing_table.rename(
        columns={
            "model_score": "existing_PI_score"
        }
    )

    base_table = base[
        [
            "asset_id",
            "model_score",
            "dependency_exposure",
            "security_gap"
        ]
    ].copy()

    base_table = base_table.rename(
        columns={
            "model_score": "base_dependency_score"
        }
    )

    ranking = existing_table.merge(
        base_table,
        on="asset_id",
        how="left"
    )

    ranking.to_csv(
        TABLE_DIR / "initial_model_scores.csv",
        index=False
    )

def main():
    print("\n")
    print("=" * 110)
    print("            PQC BANKING RISK FRAMEWORK")
    print("        EXISTING vs BASE PAPER vs PROPOSED")
    print("=" * 110)

    print(
        f"\nMigration Budget        : "
        f"{MIGRATION_BUDGET}"
    )

    print(
        f"Vulnerability Threshold : "
        f"{VULNERABILITY_THRESHOLD}"
    )

    print("\n[1] Loading banking dataset...")

    assets, services, dependencies = load_data()

    check_required_columns(assets)

    validate_data(
        assets,
        services,
        dependencies
    )

    print("\nDataset ready.")

    print("\n[2] Calculating initial model scores...")

    save_initial_rankings(
        assets,
        services,
        dependencies
    )

    print(
        "\n[3] Running Existing Probability x Impact Model..."
    )

    (
        existing_sequence,
        initial_er_1
    ) = run_static_model(
        EXISTING_MODEL,
        calculate_existing_model_scores,
        assets,
        services,
        dependencies
    )

    print(
        "\n[4] Running Base-Paper-Inspired Dependency Model..."
    )

    (
        base_sequence,
        initial_er_2
    ) = run_static_model(
        BASE_PAPER_MODEL,
        calculate_base_paper_scores,
        assets,
        services,
        dependencies
    )

    print(
        "\n[5] Running Proposed Banking Ecosystem Model..."
    )

    (
        proposed_sequence,
        initial_er_3
    ) = run_proposed_model(
        assets,
        services,
        dependencies
    )

    print_sequence(
        "MODEL 1 - EXISTING PROBABILITY x IMPACT",
        existing_sequence
    )

    print_sequence(
        "MODEL 2 - BASE-PAPER-INSPIRED DEPENDENCY",
        base_sequence
    )

    print_sequence(
        "MODEL 3 - PROPOSED BANKING ECOSYSTEM MODEL",
        proposed_sequence
    )

    comparison = pd.DataFrame([
        summarize_model(
            EXISTING_MODEL,
            existing_sequence,
            initial_er_1
        ),
        summarize_model(
            BASE_PAPER_MODEL,
            base_sequence,
            initial_er_2
        ),
        summarize_model(
            PROPOSED_MODEL,
            proposed_sequence,
            initial_er_3
        )
    ])

    comparison = (
        comparison
        .sort_values(
            by="risk_reduction",
            ascending=False
        )
        .reset_index(drop=True)
    )

    comparison["performance_rank"] = range(
        1,
        len(comparison) + 1
    )

    comparison = comparison[
        [
            "performance_rank",
            "model",
            "migration_budget",
            "budget_used",
            "assets_migrated",
            "initial_er",
            "final_er",
            "risk_reduction",
            "risk_reduction_percent",
            "risk_reduction_per_cost"
        ]
    ]

    print("\n")
    print("=" * 130)
    print("                         THREE-MODEL COMPARISON")
    print("=" * 130)

    display = comparison.copy()

    numeric_columns = [
        "migration_budget",
        "budget_used",
        "initial_er",
        "final_er",
        "risk_reduction",
        "risk_reduction_percent",
        "risk_reduction_per_cost"
    ]

    for column in numeric_columns:
        display[column] = (
            display[column].round(6)
        )

    print(
        display.to_string(
            index=False
        )
    )

    save_results(
        comparison,
        existing_sequence,
        base_sequence,
        proposed_sequence
    )

    print("\n[6] Generating figures...")

    plot_final_risk(
        comparison
    )

    plot_risk_reduction(
        comparison
    )

    plot_risk_vs_cost(
        comparison,
        {
            EXISTING_MODEL: existing_sequence,
            BASE_PAPER_MODEL: base_sequence,
            PROPOSED_MODEL: proposed_sequence
        }
    )

    winner = comparison.iloc[0]["model"]

    print("\n")
    print("=" * 110)
    print("                    EXPERIMENT COMPLETE")
    print("=" * 110)

    print(
        f"\nBest model for this dataset "
        f"under the equal-budget experiment:\n\n"
        f"    {winner}"
    )

    print("\nIMPORTANT:")

    print(
        "The result must be reported exactly as produced. "
        "Do not alter weights merely to force the proposed "
        "model to rank first."
    )

    print("\nGenerated files:")
    print("  results/tables/three_model_comparison.csv")
    print("  results/tables/initial_model_scores.csv")
    print("  results/tables/existing_model_sequence.csv")
    print("  results/tables/base_paper_model_sequence.csv")
    print("  results/tables/proposed_model_sequence.csv")
    print("\n  results/figures/three_model_final_risk.png")
    print("  results/figures/three_model_risk_reduction.png")
    print("  results/figures/three_model_risk_vs_cost.png")

if __name__ == "__main__":
    main()