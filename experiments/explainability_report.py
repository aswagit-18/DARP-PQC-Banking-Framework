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
from remediation import evaluate_ecosystem, calculate_all_remediation_impacts
from prioritization import calculate_static_priorities

TOP_N = 15


def path_to_names(graph, path):
    return " -> ".join(str(graph.nodes[n].get("name", n)) for n in path)


def main():
    assets, services, dependencies = load_data()
    evaluated = evaluate_ecosystem(assets, services, dependencies)
    graph = evaluated["graph"]
    paths = pd.DataFrame(evaluated["path_results"])

    impacts = calculate_all_remediation_impacts(assets, services, dependencies)
    priorities = calculate_static_priorities(impacts).head(TOP_N).copy()

    rows = []
    for _, p in priorities.iterrows():
        asset_id = str(p["asset_id"])
        if paths.empty:
            subset = pd.DataFrame()
        else:
            subset = paths[paths["source_asset"].astype(str) == asset_id].copy()

        if subset.empty:
            affected_services = []
            strongest_path = ""
            max_path_risk = 0.0
            avg_path_risk = 0.0
            max_path_length = 0
            path_count = 0
        else:
            affected_services = sorted(subset["service_name"].dropna().astype(str).unique().tolist())
            strongest_idx = subset["path_risk"].astype(float).idxmax()
            strongest_path = path_to_names(graph, subset.loc[strongest_idx, "path"])
            max_path_risk = float(subset["path_risk"].max())
            avg_path_risk = float(subset["path_risk"].mean())
            max_path_length = int(subset["path_length"].max())
            path_count = len(subset)

        rows.append({
            "priority_rank": int(p["priority_rank"]),
            "asset_id": asset_id,
            "asset_name": p["asset_name"],
            "tier": p["tier"],
            "algorithm": p["algorithm"],
            "delta_er": float(p["delta_er"]),
            "migration_cost": float(p["migration_cost"]),
            "priority_score": float(p["priority_score"]),
            "affected_service_count": len(affected_services),
            "affected_services": "; ".join(affected_services),
            "strongest_path_risk": max_path_risk,
            "average_path_risk": avg_path_risk,
            "max_path_length": max_path_length,
            "path_count": path_count,
            "strongest_dependency_path": strongest_path,
        })

    report = pd.DataFrame(rows)
    out = TABLE_DIR / "explainable_priorities.csv"
    report.to_csv(out, index=False)

    print("\nEXPLAINABLE TOP PQC MIGRATION PRIORITIES\n")
    display_cols = [
        "priority_rank", "asset_id", "asset_name", "tier", "algorithm",
        "delta_er", "migration_cost", "priority_score",
        "affected_service_count", "max_path_length", "strongest_path_risk"
    ]
    print(report[display_cols].round(6).to_string(index=False))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
