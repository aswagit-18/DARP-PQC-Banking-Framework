import pandas as pd

def calculate_total_service_risk(direct_risk, inherited_risk):
    if not 0 <= direct_risk <= 1:
        raise ValueError("Direct risk must be between 0 and 1.")
    if not 0 <= inherited_risk <= 1:
        raise ValueError("Inherited risk must be between 0 and 1.")
    total_risk = 1 - (1 - direct_risk) * (1 - inherited_risk)
    return max(0.0, min(1.0, total_risk))

def calculate_service_direct_risk(
    assets,
    service_id,
    vulnerability_threshold=0.25
):
    """
    Calculate the service's local/direct *quantum* risk.

    The contextual direct-risk score can remain non-zero for an asset with
    low quantum vulnerability because it also contains impact/exposure terms.
    For service-level quantum risk, assets at or below the configured quantum
    vulnerability threshold therefore contribute zero. The denominator remains
    the full set of internal service assets, so remediation is monotonic rather
    than changing the average by removing rows.
    """
    if "direct_risk" not in assets.columns:
        raise ValueError(
            "Assets DataFrame does not contain 'direct_risk'. "
            "Run calculate_direct_risk() first."
        )

    service_assets = assets[
        (assets["service_id"] == service_id)
        & (assets["tier"] == "Internal")
    ].copy()

    if service_assets.empty:
        return 0.0

    vulnerable_mask = (
        service_assets["quantum_vulnerability"]
        > vulnerability_threshold
    )

    local_quantum_scores = service_assets["direct_risk"].where(
        vulnerable_mask,
        0.0
    )

    return float(local_quantum_scores.mean())

def calculate_all_service_direct_risks(assets, services):
    results = []
    for _, service in services.iterrows():
        service_id = service["service_id"]
        direct_risk = calculate_service_direct_risk(assets, service_id)
        results.append({
            "service_id": service_id,
            "direct_service_risk": direct_risk
        })
    return pd.DataFrame(results)

def calculate_service_risks(assets, services, propagation_results):
    required_propagation_columns = [
        "service_id",
        "inherited_quantum_risk"
    ]
    for column in required_propagation_columns:
        if column not in propagation_results.columns:
            raise ValueError(f"Missing propagation column: {column}")

    direct_service_risks = calculate_all_service_direct_risks(assets, services)

    service_results = services[
        ["service_id", "service_name", "criticality"]
    ].copy()

    service_results = service_results.merge(
        direct_service_risks,
        on="service_id",
        how="left"
    )

    service_results = service_results.merge(
        propagation_results[
            ["service_id", "inherited_quantum_risk"]
        ],
        on="service_id",
        how="left"
    )

    service_results["direct_service_risk"] = (
        service_results["direct_service_risk"].fillna(0.0)
    )

    service_results["inherited_quantum_risk"] = (
        service_results["inherited_quantum_risk"].fillna(0.0)
    )

    service_results["total_service_risk"] = service_results.apply(
        lambda row: calculate_total_service_risk(
            row["direct_service_risk"],
            row["inherited_quantum_risk"]
        ),
        axis=1
    )

    return service_results

def calculate_ecosystem_risk(service_results):
    required_columns = [
        "criticality",
        "total_service_risk"
    ]

    for column in required_columns:
        if column not in service_results.columns:
            raise ValueError(f"Missing required column: {column}")

    total_criticality = service_results["criticality"].sum()

    if total_criticality <= 0:
        raise ValueError("Total service criticality must be greater than zero.")

    weighted_risk = (
        service_results["criticality"]
        * service_results["total_service_risk"]
    )

    ecosystem_risk = weighted_risk.sum() / total_criticality
    return float(ecosystem_risk)

def calculate_baseline_ecosystem_risk(assets, services, propagation_results):
    service_results = calculate_service_risks(
        assets,
        services,
        propagation_results
    )

    ecosystem_risk = calculate_ecosystem_risk(service_results)

    return service_results, ecosystem_risk

def print_ecosystem_results(service_results, ecosystem_risk):
    print("\n")
    print("=" * 75)
    print("         ECOSYSTEM-WIDE QUANTUM RISK ANALYSIS")
    print("=" * 75)

    display_results = service_results.copy()

    risk_columns = [
        "direct_service_risk",
        "inherited_quantum_risk",
        "total_service_risk"
    ]

    for column in risk_columns:
        display_results[column] = display_results[column].round(6)

    display_results = display_results.sort_values(
        by="total_service_risk",
        ascending=False
    )

    print("\nService-Level Risk Results:\n")
    print(display_results.to_string(index=False))
    print("\n")
    print("=" * 75)
    print("          BASELINE ECOSYSTEM QUANTUM RISK")
    print("=" * 75)
    print(f"\nEcosystem Risk (ER): {ecosystem_risk:.6f}")

if __name__ == "__main__":
    print("\necosystem_risk.py created successfully.")
    print("Run the complete framework using main.py.")