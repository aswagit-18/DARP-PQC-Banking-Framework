import pandas as pd
from risk_model import calculate_direct_risk
from graph_builder import build_graph
from propagation import calculate_service_propagation
from ecosystem_risk import calculate_baseline_ecosystem_risk

def evaluate_ecosystem(assets, services, dependencies):
    risk_assets = calculate_direct_risk(assets)

    graph = build_graph(
        risk_assets,
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
        risk_assets
    )

    (
        service_risk_results,
        ecosystem_risk
    ) = calculate_baseline_ecosystem_risk(
        risk_assets,
        services,
        propagation_results
    )

    return {
        "assets": risk_assets,
        "graph": graph,
        "propagation_results": propagation_results,
        "path_results": path_results,
        "asset_details": asset_details,
        "service_risk_results": service_risk_results,
        "ecosystem_risk": ecosystem_risk
    }

def simulate_asset_remediation(
    assets,
    asset_id,
    remediated_quantum_vulnerability=0.0
):
    if not 0 <= remediated_quantum_vulnerability <= 1:
        raise ValueError(
            "remediated_quantum_vulnerability must be between 0 and 1."
        )

    if asset_id not in assets["asset_id"].values:
        raise ValueError(f"Unknown asset_id: {asset_id}")

    remediated_assets = assets.copy()

    remediated_assets.loc[
        remediated_assets["asset_id"] == asset_id,
        "quantum_vulnerability"
    ] = remediated_quantum_vulnerability

    return remediated_assets

def evaluate_single_remediation(
    assets,
    services,
    dependencies,
    asset_id,
    baseline_ecosystem_risk=None
):
    asset_rows = assets[
        assets["asset_id"] == asset_id
    ]

    if asset_rows.empty:
        raise ValueError(f"Unknown asset_id: {asset_id}")

    original_asset = asset_rows.iloc[0]

    if baseline_ecosystem_risk is None:
        baseline_results = evaluate_ecosystem(
            assets,
            services,
            dependencies
        )
        baseline_ecosystem_risk = baseline_results[
            "ecosystem_risk"
        ]

    remediated_assets = simulate_asset_remediation(
        assets,
        asset_id
    )

    remediated_results = evaluate_ecosystem(
        remediated_assets,
        services,
        dependencies
    )

    ecosystem_risk_after = remediated_results[
        "ecosystem_risk"
    ]

    delta_er = (
        baseline_ecosystem_risk
        - ecosystem_risk_after
    )

    if abs(delta_er) < 1e-12:
        delta_er = 0.0

    return {
        "asset_id": asset_id,
        "asset_name": original_asset["asset_name"],
        "tier": original_asset["tier"],
        "algorithm": original_asset["algorithm"],
        "original_quantum_vulnerability": original_asset[
            "quantum_vulnerability"
        ],
        "migration_complexity": original_asset[
            "migration_complexity"
        ],
        "business_criticality": original_asset[
            "business_criticality"
        ],
        "hndl_exposure": original_asset["hndl_exposure"],
        "ecosystem_risk_before": baseline_ecosystem_risk,
        "ecosystem_risk_after": ecosystem_risk_after,
        "delta_er": delta_er
    }

def get_remediation_candidates(
    assets,
    vulnerability_threshold=0.25
):
    return assets[
        assets["quantum_vulnerability"]
        > vulnerability_threshold
    ].copy()

def calculate_all_remediation_impacts(
    assets,
    services,
    dependencies,
    vulnerability_threshold=0.25
):
    print("\nCalculating baseline ecosystem risk...")

    baseline_results = evaluate_ecosystem(
        assets,
        services,
        dependencies
    )

    baseline_er = baseline_results[
        "ecosystem_risk"
    ]

    print(f"Baseline ER: {baseline_er:.6f}")

    candidates = get_remediation_candidates(
        assets,
        vulnerability_threshold
    )

    print(
        f"Remediation candidates: "
        f"{len(candidates)}"
    )

    results = []

    for index, (_, asset) in enumerate(
        candidates.iterrows(),
        start=1
    ):
        asset_id = asset["asset_id"]

        print(
            f"[{index}/{len(candidates)}] "
            f"Simulating {asset_id} - "
            f"{asset['asset_name']}"
        )

        result = evaluate_single_remediation(
            assets=assets,
            services=services,
            dependencies=dependencies,
            asset_id=asset_id,
            baseline_ecosystem_risk=baseline_er
        )

        results.append(result)

    remediation_results = pd.DataFrame(
        results
    )

    if not remediation_results.empty:
        remediation_results = remediation_results.sort_values(
            by="delta_er",
            ascending=False
        ).reset_index(drop=True)

        remediation_results["delta_er_rank"] = range(
            1,
            len(remediation_results) + 1
        )

    return remediation_results

def print_remediation_results(
    remediation_results,
    top_n=15
):
    if remediation_results.empty:
        print("\nNo remediation candidates found.")
        return

    display_columns = [
        "delta_er_rank",
        "asset_id",
        "asset_name",
        "tier",
        "algorithm",
        "ecosystem_risk_before",
        "ecosystem_risk_after",
        "delta_er",
        "migration_complexity"
    ]

    display_results = remediation_results[
        display_columns
    ].head(top_n).copy()

    numeric_columns = [
        "ecosystem_risk_before",
        "ecosystem_risk_after",
        "delta_er",
        "migration_complexity"
    ]

    for column in numeric_columns:
        display_results[column] = (
            display_results[column].round(6)
        )

    print("\n")
    print("=" * 95)
    print(
        "            ECOSYSTEM RISK REDUCTION "
        "FROM INDIVIDUAL REMEDIATION"
    )
    print("=" * 95)

    print(
        f"\nTop {min(top_n, len(display_results))} "
        f"Remediation Candidates:\n"
    )

    print(
        display_results.to_string(
            index=False
        )
    )

if __name__ == "__main__":
    print("\nremediation.py created successfully.")
    print("Run remediation experiments through main.py.")