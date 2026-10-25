import os
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_data():
    dataset_version = os.getenv("PQC_DATASET", "v1").lower()

    if dataset_version == "v1":
        data_dir = PROJECT_ROOT / "data"
    elif dataset_version == "v2":
        data_dir = PROJECT_ROOT / "data_v2"
    elif dataset_version == "v3":
        data_dir = PROJECT_ROOT / "data_v3"
    else:
        raise ValueError("Invalid PQC_DATASET value. Use v1, v2 or v3.")

    print(f"\nUsing dataset: {dataset_version.upper()}")
    print(f"Data directory: {data_dir}")

    assets_path = data_dir / "banking_assets.csv"
    services_path = data_dir / "banking_services.csv"
    dependencies_path = data_dir / "banking_dependencies.csv"

    assets = pd.read_csv(assets_path)
    services = pd.read_csv(services_path)
    dependencies = pd.read_csv(dependencies_path)

    return assets, services, dependencies

def validate_data(assets, services, dependencies):
    print("\n========== DATA VALIDATION ==========")
    print(f"Number of assets       : {len(assets)}")
    print(f"Number of services     : {len(services)}")
    print(f"Number of dependencies : {len(dependencies)}")

    required_asset_columns = [
        "asset_id",
        "asset_name",
        "tier",
        "algorithm",
        "business_criticality",
        "hndl_exposure",
        "migration_complexity",
        "quantum_vulnerability"
    ]

    required_service_columns = [
        "service_id",
        "service_name",
        "criticality"
    ]

    required_dependency_columns = [
        "dependency_id",
        "source_id",
        "target_id",
        "dependency_strength"
    ]

    for column in required_asset_columns:
        assert column in assets.columns, f"Missing asset column: {column}"

    for column in required_service_columns:
        assert column in services.columns, f"Missing service column: {column}"

    for column in required_dependency_columns:
        assert column in dependencies.columns, f"Missing dependency column: {column}"

    print("\nRequired columns: PASS")
    print("\nAsset tiers:")
    print(assets["tier"].value_counts())

    assert not assets["asset_id"].duplicated().any(), "Duplicate asset IDs found"
    assert not services["service_id"].duplicated().any(), "Duplicate service IDs found"
    assert not dependencies["dependency_id"].duplicated().any(), "Duplicate dependency IDs found"

    print("\nDuplicate ID check: PASS")

    duplicate_pairs = dependencies.duplicated(
        subset=["source_id", "target_id"],
        keep=False
    )
    duplicate_pair_count = (
        dependencies.loc[duplicate_pairs, ["source_id", "target_id"]]
        .drop_duplicates()
        .shape[0]
    )

    if duplicate_pair_count:
        print(
            f"Dependency pair warning: {duplicate_pair_count} duplicate "
            "source-target pair(s) detected. Graph construction will retain "
            "the strongest dependency strength for each pair."
        )
    else:
        print("Dependency source-target pair check: PASS")

    assert dependencies["dependency_strength"].between(0, 1).all(), (
        "Dependency strength must be between 0 and 1"
    )

    risk_columns = [
        "data_sensitivity",
        "data_lifetime",
        "business_criticality",
        "external_exposure",
        "hndl_exposure",
        "migration_complexity",
        "quantum_vulnerability"
    ]

    for column in risk_columns:
        assert assets[column].between(0, 1).all(), (
            f"{column} contains values outside 0-1"
        )

    print("Range validation: PASS")

    valid_nodes = set(assets["asset_id"].astype(str)) | set(
        services["service_id"].astype(str)
    )

    assert set(dependencies["source_id"].astype(str)).issubset(valid_nodes), (
        "Invalid dependency source detected"
    )

    assert set(dependencies["target_id"].astype(str)).issubset(valid_nodes), (
        "Invalid dependency target detected"
    )

    print("Dependency endpoint check: PASS")
    print("\n========== VALIDATION COMPLETE ==========")

if __name__ == "__main__":
    assets, services, dependencies = load_data()
    validate_data(assets, services, dependencies)