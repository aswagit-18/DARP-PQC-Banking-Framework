import os
import sys
import time
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


def run_version(version):
    os.environ["PQC_DATASET"] = version
    assets, services, dependencies = load_data()

    t0 = time.perf_counter()
    evaluated = evaluate_ecosystem(assets, services, dependencies)
    baseline_seconds = time.perf_counter() - t0

    t1 = time.perf_counter()
    impacts = calculate_all_remediation_impacts(assets, services, dependencies)
    priorities = calculate_static_priorities(impacts)
    initial_ranking_seconds = time.perf_counter() - t1

    graph = evaluated["graph"]
    top = priorities.iloc[0] if not priorities.empty else None

    return {
        "dataset": version.upper(),
        "services": len(services),
        "assets": len(assets),
        "dependency_rows": len(dependencies),
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "vulnerable_assets": int((assets["quantum_vulnerability"] > 0.25).sum()),
        "strongest_vulnerable_paths": len(evaluated["path_results"]),
        "baseline_ecosystem_risk": float(evaluated["ecosystem_risk"]),
        "baseline_evaluation_seconds": baseline_seconds,
        "initial_all_candidate_ranking_seconds": initial_ranking_seconds,
        "top_priority_asset": None if top is None else top["asset_id"],
        "top_priority_score": None if top is None else float(top["priority_score"]),
        "top_delta_er": None if top is None else float(top["delta_er"]),
    }


def main():
    original = os.environ.get("PQC_DATASET")
    rows = []
    try:
        for version in ["v1", "v2"]:
            print(f"\nRunning scalability benchmark for {version.upper()}...")
            rows.append(run_version(version))
    finally:
        if original is None:
            os.environ.pop("PQC_DATASET", None)
        else:
            os.environ["PQC_DATASET"] = original

    df = pd.DataFrame(rows)
    out = TABLE_DIR / "scalability_analysis.csv"
    df.to_csv(out, index=False)
    print("\nSCALABILITY SUMMARY\n")
    print(df.round(6).to_string(index=False))
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
