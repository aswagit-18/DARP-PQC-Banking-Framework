import os
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
from remediation import evaluate_ecosystem, calculate_all_remediation_impacts
from prioritization import calculate_static_priorities
from baselines import compare_strategies

BUDGET = 7.5


def main():
    os.environ.setdefault("PQC_DATASET", "v1")
    assets, services, dependencies = load_data()
    validate_data(assets, services, dependencies)

    baseline = evaluate_ecosystem(assets, services, dependencies)
    baseline["service_risk_results"].to_csv(
        TABLE_DIR / "final_service_risks_v1.csv", index=False
    )
    pd.DataFrame(baseline["path_results"]).to_csv(
        TABLE_DIR / "final_path_contributions_v1.csv", index=False
    )

    remediation = calculate_all_remediation_impacts(assets, services, dependencies)
    priorities = calculate_static_priorities(remediation)
    remediation.to_csv(TABLE_DIR / "final_remediation_impacts_v1.csv", index=False)
    priorities.to_csv(TABLE_DIR / "final_static_priorities_v1.csv", index=False)

    comparison, sequences = compare_strategies(
        assets, services, dependencies, migration_budget=BUDGET
    )
    comparison = comparison.copy()
    comparison["risk_reduction_percent"] = (
        100.0 * comparison["cumulative_delta_er"] / comparison["initial_er"]
    )
    comparison.to_csv(TABLE_DIR / "final_strategy_comparison_v1.csv", index=False)

    for strategy, sequence in sequences.items():
        safe = (
            strategy.lower()
            .replace("/", "_")
            .replace(" ", "_")
            .replace("-", "_")
        )
        sequence.to_csv(TABLE_DIR / f"final_sequence_{safe}.csv", index=False)

    print("\nFINAL V1 RESULTS\n")
    print(f"Baseline ER: {baseline['ecosystem_risk']:.6f}")
    print(comparison.round(6).to_string(index=False))
    print("\nTop 10 static priorities:\n")
    print(priorities[[
        "priority_rank", "asset_id", "asset_name", "tier", "algorithm",
        "delta_er", "migration_cost", "priority_score"
    ]].head(10).round(6).to_string(index=False))
    print("\nSaved final evaluation CSVs to results/tables/.")


if __name__ == "__main__":
    main()
