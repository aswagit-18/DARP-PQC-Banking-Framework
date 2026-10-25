import pandas as pd

WEIGHTS = {
    "quantum_vulnerability": 0.20,
    "data_sensitivity": 0.20,
    "data_lifetime": 0.20,
    "business_criticality": 0.20,
    "external_exposure": 0.20
}

def calculate_direct_risk(assets, weights=None):
    assets = assets.copy()

    if weights is None:
        weights = WEIGHTS

    required_weights = [
        "quantum_vulnerability",
        "data_sensitivity",
        "data_lifetime",
        "business_criticality",
        "external_exposure"
    ]

    for key in required_weights:
        if key not in weights:
            raise ValueError(f"Missing weight: {key}")

    total_weight = sum(
        weights[key]
        for key in required_weights
    )

    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(
            f"Weights must sum to 1.0. Current sum = {total_weight}"
        )

    assets["direct_risk"] = (
        weights["quantum_vulnerability"]
        * assets["quantum_vulnerability"]
        + weights["data_sensitivity"]
        * assets["data_sensitivity"]
        + weights["data_lifetime"]
        * assets["data_lifetime"]
        + weights["business_criticality"]
        * assets["business_criticality"]
        + weights["external_exposure"]
        * assets["external_exposure"]
    )

    return assets

def classify_risk(risk):
    if risk < 0.25:
        return "Low"
    elif risk < 0.50:
        return "Moderate"
    elif risk < 0.75:
        return "High"
    else:
        return "Critical"

def add_risk_categories(assets):
    assets = assets.copy()
    assets["risk_category"] = assets["direct_risk"].apply(
        classify_risk
    )
    return assets

def generate_risk_table(assets):
    columns = [
        "asset_id",
        "asset_name",
        "tier",
        "algorithm",
        "quantum_vulnerability",
        "business_criticality",
        "hndl_exposure",
        "migration_complexity",
        "direct_risk",
        "risk_category"
    ]

    return assets[columns].sort_values(
        by="direct_risk",
        ascending=False
    )

if __name__ == "__main__":
    from data_loader import load_data

    assets, services, dependencies = load_data()

    assets = calculate_direct_risk(assets)
    assets = add_risk_categories(assets)
    risk_table = generate_risk_table(assets)

    print("\n==============================================")
    print("       DIRECT QUANTUM RISK ASSESSMENT")
    print("==============================================")
    print(risk_table.to_string(index=False))

    print("\n==============================================")
    print("             RISK SUMMARY")
    print("==============================================")
    print(risk_table["risk_category"].value_counts())

    print("\nTop 10 highest-risk assets:")

    print(
        risk_table[
            [
                "asset_id",
                "asset_name",
                "tier",
                "algorithm",
                "direct_risk",
                "risk_category"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )