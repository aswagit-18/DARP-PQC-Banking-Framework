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

from data_loader import load_data
from baselines import compare_strategies

BUDGETS = [2.5, 5.0, 7.5]


def main():
    os.environ.setdefault("PQC_DATASET", "v1")
    assets, services, dependencies = load_data()
    rows = []

    for budget in BUDGETS:
        print(f"\nRunning equal-budget comparison for budget={budget}...")
        comparison, _ = compare_strategies(
            assets, services, dependencies, migration_budget=budget
        )
        comparison = comparison.copy()
        comparison["budget_scenario"] = budget
        rows.append(comparison)

    out_df = pd.concat(rows, ignore_index=True)
    out_df["risk_reduction_percent"] = (
        100.0 * out_df["cumulative_delta_er"] / out_df["initial_er"]
    )
    out = TABLE_DIR / "budget_sweep.csv"
    out_df.to_csv(out, index=False)

    print("\nBUDGET SWEEP SUMMARY\n")
    cols = [
        "budget_scenario", "strategy", "budget_used",
        "number_of_assets_migrated", "final_er", "cumulative_delta_er",
        "risk_reduction_percent", "risk_reduction_per_cost"
    ]
    print(out_df[cols].round(6).to_string(index=False))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
