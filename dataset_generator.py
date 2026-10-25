from pathlib import Path
import random
import pandas as pd

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "data_v2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

NUMBER_OF_SERVICES = 20
INTERNAL_ASSETS_PER_SERVICE = 7
NUMBER_OF_INTERNAL_ASSETS = NUMBER_OF_SERVICES * INTERNAL_ASSETS_PER_SERVICE
NUMBER_OF_THIRD_PARTY_ASSETS = 70
NUMBER_OF_SUB_TIER_ASSETS = 40
TARGET_DEPENDENCIES = 720

def clamp(value, minimum=0.0, maximum=1.0):
    return max(minimum, min(maximum, value))

def round_score(value):
    return round(clamp(value), 2)

def random_between(low, high):
    return random.uniform(low, high)

SERVICE_TEMPLATES = [
    ("Core Banking", 1.00, 0.95, 0.95),
    ("Mobile Banking", 0.95, 0.90, 0.75),
    ("Internet Banking", 0.95, 0.90, 0.75),
    ("ATM Network", 0.90, 0.80, 0.65),
    ("Card Payments", 0.98, 0.90, 0.75),
    ("Instant Payments", 0.98, 0.90, 0.75),
    ("Customer Authentication", 0.95, 0.95, 0.80),
    ("Loan Processing", 0.85, 0.90, 0.90),
    ("KYC Service", 0.90, 1.00, 1.00),
    ("Fraud Detection", 0.92, 0.90, 0.75),
    ("Treasury Management", 0.95, 0.90, 0.85),
    ("SWIFT and Interbank", 1.00, 0.95, 0.90),
    ("Customer Data Platform", 0.85, 1.00, 0.95),
    ("Customer Relationship Management", 0.75, 0.85, 0.80),
    ("Open Banking APIs", 0.90, 0.85, 0.70),
    ("Merchant Acquiring", 0.90, 0.85, 0.70),
    ("Bill Payments", 0.88, 0.80, 0.70),
    ("Data Warehouse and Analytics", 0.82, 0.95, 0.95),
    ("Regulatory Reporting", 0.85, 0.90, 0.95),
    ("Document Management", 0.75, 0.90, 0.95)
]

def generate_services():
    services = []
    service_profiles = {}

    for index, template in enumerate(SERVICE_TEMPLATES, start=1):
        service_name, criticality, sensitivity, lifetime = template
        service_id = f"S{index:02d}"

        services.append({
            "service_id": service_id,
            "service_name": service_name,
            "criticality": criticality,
            "data_sensitivity": sensitivity
        })

        service_profiles[service_id] = {
            "service_name": service_name,
            "criticality": criticality,
            "sensitivity": sensitivity,
            "lifetime": lifetime
        }

    return pd.DataFrame(services), service_profiles

QUANTUM_VULNERABILITY = {
    "RSA-2048": 0.98,
    "RSA-3072": 0.97,
    "ECDSA-256": 0.98,
    "ECDH-256": 0.98,
    "ECC-256": 0.98,
    "AES-128": 0.45,
    "AES-256": 0.18,
    "ML-KEM": 0.05,
    "ML-DSA": 0.05
}

KEY_SIZE = {
    "RSA-2048": 2048,
    "RSA-3072": 3072,
    "ECDSA-256": 256,
    "ECDH-256": 256,
    "ECC-256": 256,
    "AES-128": 128,
    "AES-256": 256,
    "ML-KEM": 768,
    "ML-DSA": 65
}

INTERNAL_ASSET_TYPES = [
    "API Gateway",
    "Application Server",
    "Database",
    "Authentication Server",
    "HSM",
    "PKI",
    "Message Broker",
    "Key Management Server",
    "Transaction Processor",
    "Identity Service",
    "Integration Gateway",
    "Secure File Transfer"
]

THIRD_PARTY_ASSET_TYPES = [
    "Cloud KMS",
    "Cloud HSM",
    "Payment Processor",
    "Identity Provider",
    "Certificate Authority",
    "Managed PKI",
    "API Platform",
    "Fraud Data Provider",
    "Security Gateway",
    "Cloud Database",
    "Tokenization Service",
    "Messaging Platform"
]

SUB_TIER_ASSET_TYPES = [
    "Sub-tier KMS",
    "HSM Backend",
    "Certificate Validation Service",
    "Tokenization Module",
    "Network Transit Provider",
    "Identity Federation Backend",
    "Managed Database Backend",
    "Hardware Security Module",
    "Signing Service",
    "Cloud Storage Backend"
]

THIRD_PARTY_PROVIDERS = [
    "CloudSecure Systems",
    "GlobalPay Network",
    "TrustID Services",
    "SecureCertificate Ltd",
    "FinCloud Technologies",
    "BankAPI Services",
    "PaymentHub Global",
    "CyberTrust Platform",
    "SecureData Cloud",
    "IdentityCloud",
    "TransactionNet",
    "DigitalTrust Services"
]

SUB_TIER_PROVIDERS = [
    "CryptoInfra Systems",
    "SecureHardware Labs",
    "CloudCore Infrastructure",
    "TrustChain Services",
    "NetworkSecure Global",
    "KeyVault Technologies",
    "CertificateBackend",
    "DataCore Services",
    "SecureCompute Systems",
    "TokenCloud Infrastructure"
]

def choose_crypto_function(asset_type):
    if "HSM" in asset_type or "KMS" in asset_type or "Key Management" in asset_type:
        return "Key Management"

    if "PKI" in asset_type or "Certificate" in asset_type or "Signing" in asset_type:
        return "Digital Signature"

    if "Database" in asset_type or "Storage" in asset_type:
        return "Data Encryption"

    if "Authentication" in asset_type or "Identity" in asset_type:
        return "Authentication"

    if "Token" in asset_type:
        return "Tokenization"

    return random.choice([
        "TLS",
        "Encryption",
        "Authentication",
        "Digital Signature"
    ])

def choose_algorithm(asset_type):
    if "Database" in asset_type or "Storage" in asset_type:
        return random.choices(
            ["AES-256", "AES-128"],
            weights=[0.75, 0.25],
            k=1
        )[0]

    if "PKI" in asset_type or "Certificate" in asset_type or "Signing" in asset_type:
        return random.choices(
            ["RSA-2048", "RSA-3072", "ECDSA-256", "ML-DSA"],
            weights=[0.30, 0.25, 0.35, 0.10],
            k=1
        )[0]

    if "HSM" in asset_type or "KMS" in asset_type or "Key Management" in asset_type:
        return random.choices(
            ["RSA-2048", "RSA-3072", "ECC-256", "ECDH-256", "ML-KEM"],
            weights=[0.25, 0.20, 0.25, 0.20, 0.10],
            k=1
        )[0]

    return random.choices(
        ["RSA-2048", "RSA-3072", "ECDSA-256", "ECDH-256", "ECC-256", "ML-KEM"],
        weights=[0.20, 0.15, 0.25, 0.20, 0.12, 0.08],
        k=1
    )[0]

def calculate_external_exposure(tier, asset_type):
    if tier == "Internal":
        base = random_between(0.25, 0.65)
        if "API" in asset_type or "Gateway" in asset_type:
            base += 0.20
    elif tier == "Third-Party":
        base = random_between(0.65, 0.95)
    else:
        base = random_between(0.60, 0.90)

    return round_score(base)

def calculate_migration_complexity(tier, asset_type, algorithm):
    if tier == "Internal":
        complexity = random_between(0.45, 0.85)
    elif tier == "Third-Party":
        complexity = random_between(0.50, 0.85)
    else:
        complexity = random_between(0.55, 0.90)

    if "HSM" in asset_type or "PKI" in asset_type or "Transaction Processor" in asset_type:
        complexity += 0.08

    if algorithm in ["ML-KEM", "ML-DSA"]:
        complexity -= 0.10

    return round_score(complexity)

def calculate_hndl_exposure(
    data_lifetime,
    data_sensitivity,
    quantum_vulnerability
):
    information_value = (
        0.55 * data_lifetime
        + 0.45 * data_sensitivity
    )

    crypto_factor = (
        0.35
        + 0.65 * quantum_vulnerability
    )

    hndl = information_value * crypto_factor
    return round_score(hndl)

def create_asset(
    asset_id,
    asset_name,
    asset_type,
    tier,
    service_id,
    provider_type,
    provider,
    service_profile
):
    algorithm = choose_algorithm(asset_type)
    quantum_vulnerability = QUANTUM_VULNERABILITY[algorithm]
    crypto_function = choose_crypto_function(asset_type)

    data_sensitivity = round_score(
        service_profile["sensitivity"]
        + random_between(-0.12, 0.05)
    )

    data_lifetime = round_score(
        service_profile["lifetime"]
        + random_between(-0.12, 0.05)
    )

    business_criticality = round_score(
        service_profile["criticality"]
        + random_between(-0.12, 0.04)
    )

    external_exposure = calculate_external_exposure(
        tier,
        asset_type
    )

    migration_complexity = calculate_migration_complexity(
        tier,
        asset_type,
        algorithm
    )

    hndl_exposure = calculate_hndl_exposure(
        data_lifetime,
        data_sensitivity,
        quantum_vulnerability
    )

    return {
        "asset_id": asset_id,
        "asset_name": asset_name,
        "asset_type": asset_type,
        "tier": tier,
        "service_id": service_id,
        "provider_type": provider_type,
        "algorithm": algorithm,
        "key_size": KEY_SIZE[algorithm],
        "crypto_function": crypto_function,
        "data_sensitivity": data_sensitivity,
        "data_lifetime": data_lifetime,
        "business_criticality": business_criticality,
        "external_exposure": external_exposure,
        "hndl_exposure": hndl_exposure,
        "migration_complexity": migration_complexity,
        "quantum_vulnerability": quantum_vulnerability,
        "provider": provider
    }

def generate_assets(service_profiles):
    assets = []
    asset_number = 1

    for service_id, profile in service_profiles.items():
        selected_types = random.sample(
            INTERNAL_ASSET_TYPES,
            INTERNAL_ASSETS_PER_SERVICE
        )

        for local_index, asset_type in enumerate(
            selected_types,
            start=1
        ):
            asset_id = f"A{asset_number:03d}"

            asset_name = (
                f"{profile['service_name']} "
                f"{asset_type} "
                f"{local_index}"
            )

            assets.append(
                create_asset(
                    asset_id=asset_id,
                    asset_name=asset_name,
                    asset_type=asset_type,
                    tier="Internal",
                    service_id=service_id,
                    provider_type="Internal",
                    provider="Bank Internal",
                    service_profile=profile
                )
            )

            asset_number += 1

    service_ids = list(service_profiles.keys())

    for index in range(
        1,
        NUMBER_OF_THIRD_PARTY_ASSETS + 1
    ):
        service_id = random.choice(service_ids)
        profile = service_profiles[service_id]
        asset_type = random.choice(THIRD_PARTY_ASSET_TYPES)
        provider = random.choice(THIRD_PARTY_PROVIDERS)
        asset_id = f"A{asset_number:03d}"

        asset_name = (
            f"{provider} "
            f"{asset_type} "
            f"{index:02d}"
        )

        assets.append(
            create_asset(
                asset_id=asset_id,
                asset_name=asset_name,
                asset_type=asset_type,
                tier="Third-Party",
                service_id=service_id,
                provider_type="External Vendor",
                provider=provider,
                service_profile=profile
            )
        )

        asset_number += 1

    for index in range(
        1,
        NUMBER_OF_SUB_TIER_ASSETS + 1
    ):
        service_id = random.choice(service_ids)
        profile = service_profiles[service_id]
        asset_type = random.choice(SUB_TIER_ASSET_TYPES)
        provider = random.choice(SUB_TIER_PROVIDERS)
        asset_id = f"A{asset_number:03d}"

        asset_name = (
            f"{provider} "
            f"{asset_type} "
            f"{index:02d}"
        )

        assets.append(
            create_asset(
                asset_id=asset_id,
                asset_name=asset_name,
                asset_type=asset_type,
                tier="Sub-Tier",
                service_id=service_id,
                provider_type="Sub-Tier Vendor",
                provider=provider,
                service_profile=profile
            )
        )

        asset_number += 1

    return pd.DataFrame(assets)

def generate_dependencies(assets, services):
    dependencies = []
    used_edges = set()
    dependency_number = 1

    def add_dependency(
        source,
        target,
        dependency_type,
        strength
    ):
        nonlocal dependency_number

        if source == target:
            return False

        edge = (
            str(source),
            str(target)
        )

        if edge in used_edges:
            return False

        used_edges.add(edge)

        crypto_dependency = (
            1 if random.random() < 0.80 else 0
        )

        data_dependency = (
            1 if random.random() < 0.70 else 0
        )

        critical_dependency = (
            1 if strength >= 0.82 else 0
        )

        dependencies.append({
            "dependency_id": f"D{dependency_number:04d}",
            "source_id": source,
            "target_id": target,
            "dependency_type": dependency_type,
            "dependency_strength": round(strength, 2),
            "crypto_dependency": crypto_dependency,
            "data_dependency": data_dependency,
            "critical_dependency": critical_dependency
        })

        dependency_number += 1
        return True

    internal = assets[
        assets["tier"] == "Internal"
    ].copy()

    third_party = assets[
        assets["tier"] == "Third-Party"
    ].copy()

    sub_tier = assets[
        assets["tier"] == "Sub-Tier"
    ].copy()

    for _, asset in internal.iterrows():
        add_dependency(
            asset["service_id"],
            asset["asset_id"],
            "Uses",
            random_between(0.82, 1.00)
        )

    for _, external_asset in third_party.iterrows():
        same_service_internal = internal[
            internal["service_id"]
            == external_asset["service_id"]
        ]

        if same_service_internal.empty:
            source_asset = internal.sample(
                1,
                random_state=random.randint(
                    1,
                    100000
                )
            ).iloc[0]
        else:
            source_asset = same_service_internal.sample(
                1,
                random_state=random.randint(
                    1,
                    100000
                )
            ).iloc[0]

        add_dependency(
            source_asset["asset_id"],
            external_asset["asset_id"],
            "Third-Party Dependency",
            random_between(0.65, 0.95)
        )

    for _, internal_asset in internal.iterrows():
        same_service_external = third_party[
            third_party["service_id"]
            == internal_asset["service_id"]
        ]

        candidate_pool = (
            same_service_external
            if not same_service_external.empty
            else third_party
        )

        sample_size = min(
            2,
            len(candidate_pool)
        )

        selected = candidate_pool.sample(
            sample_size,
            random_state=random.randint(
                1,
                100000
            )
        )

        for _, external_asset in selected.iterrows():
            add_dependency(
                internal_asset["asset_id"],
                external_asset["asset_id"],
                "Vendor Dependency",
                random_between(0.62, 0.94)
            )

    for _, sub_asset in sub_tier.iterrows():
        same_service_tp = third_party[
            third_party["service_id"]
            == sub_asset["service_id"]
        ]

        candidate_pool = (
            same_service_tp
            if not same_service_tp.empty
            else third_party
        )

        source_asset = candidate_pool.sample(
            1,
            random_state=random.randint(
                1,
                100000
            )
        ).iloc[0]

        add_dependency(
            source_asset["asset_id"],
            sub_asset["asset_id"],
            "Sub-Tier Dependency",
            random_between(0.60, 0.94)
        )

    for _, tp_asset in third_party.iterrows():
        same_service_sub = sub_tier[
            sub_tier["service_id"]
            == tp_asset["service_id"]
        ]

        candidate_pool = (
            same_service_sub
            if not same_service_sub.empty
            else sub_tier
        )

        sample_size = min(
            2,
            len(candidate_pool)
        )

        selected = candidate_pool.sample(
            sample_size,
            random_state=random.randint(
                1,
                100000
            )
        )

        for _, sub_asset in selected.iterrows():
            add_dependency(
                tp_asset["asset_id"],
                sub_asset["asset_id"],
                "Sub-Tier Dependency",
                random_between(0.58, 0.92)
            )

    for service_id in services["service_id"]:
        service_assets = internal[
            internal["service_id"] == service_id
        ].sort_values("asset_id")

        ids = service_assets[
            "asset_id"
        ].tolist()

        if len(ids) >= 4:
            add_dependency(
                ids[0],
                ids[3],
                "Internal Dependency",
                random_between(0.68, 0.90)
            )

            add_dependency(
                ids[2],
                ids[5],
                "Internal Dependency",
                random_between(0.68, 0.90)
            )

    internal_ids = internal[
        "asset_id"
    ].tolist()

    third_party_ids = third_party[
        "asset_id"
    ].tolist()

    sub_tier_ids = sub_tier[
        "asset_id"
    ].tolist()

    attempts = 0
    maximum_attempts = 100000

    while (
        len(dependencies) < TARGET_DEPENDENCIES
        and attempts < maximum_attempts
    ):
        attempts += 1

        if random.random() < 0.65:
            source = random.choice(internal_ids)
            target = random.choice(third_party_ids)
            dependency_type = "External Service Dependency"
            strength = random_between(0.60, 0.92)
        else:
            source = random.choice(third_party_ids)
            target = random.choice(sub_tier_ids)
            dependency_type = "Supply Chain Dependency"
            strength = random_between(0.58, 0.90)

        add_dependency(
            source,
            target,
            dependency_type,
            strength
        )

    return pd.DataFrame(dependencies)

def validate_generated_dataset(
    assets,
    services,
    dependencies
):
    print("\n")
    print("=" * 70)
    print("             DATASET V2 VALIDATION")
    print("=" * 70)

    print(f"\nServices     : {len(services)}")
    print(f"Assets       : {len(assets)}")
    print(f"Dependencies : {len(dependencies)}")

    print("\nAsset tier distribution:")
    print(assets["tier"].value_counts())

    print("\nAlgorithm distribution:")
    print(assets["algorithm"].value_counts())

    assert len(services) == NUMBER_OF_SERVICES

    assert len(assets) == (
        NUMBER_OF_INTERNAL_ASSETS
        + NUMBER_OF_THIRD_PARTY_ASSETS
        + NUMBER_OF_SUB_TIER_ASSETS
    )

    assert not assets["asset_id"].duplicated().any()
    assert not services["service_id"].duplicated().any()
    assert not dependencies["dependency_id"].duplicated().any()

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
            f"{column} outside 0-1"
        )

    assert dependencies[
        "dependency_strength"
    ].between(0, 1).all()

    valid_nodes = (
        set(assets["asset_id"])
        | set(services["service_id"])
    )

    assert set(
        dependencies["source_id"]
    ).issubset(valid_nodes)

    assert set(
        dependencies["target_id"]
    ).issubset(valid_nodes)

    print("\nDuplicate ID check : PASS")
    print("Risk range check   : PASS")
    print("Dependency check   : PASS")
    print(
        "\nDataset V2 validation completed successfully."
    )

def save_dataset(
    assets,
    services,
    dependencies
):
    assets_path = OUTPUT_DIR / "banking_assets.csv"
    services_path = OUTPUT_DIR / "banking_services.csv"
    dependencies_path = OUTPUT_DIR / "banking_dependencies.csv"

    assets.to_csv(
        assets_path,
        index=False
    )

    services.to_csv(
        services_path,
        index=False
    )

    dependencies.to_csv(
        dependencies_path,
        index=False
    )

    print("\n")
    print("=" * 70)
    print("              DATASET V2 SAVED")
    print("=" * 70)

    print(f"\n{assets_path}")
    print(f"{services_path}")
    print(f"{dependencies_path}")

def main():
    print("\n")
    print("=" * 70)
    print("       PQC BANKING SYNTHETIC DATASET GENERATOR")
    print("=" * 70)

    print(f"\nRandom seed : {RANDOM_SEED}")
    print("\nGenerating banking services...")

    (
        services,
        service_profiles
    ) = generate_services()

    print("Generating banking assets...")

    assets = generate_assets(
        service_profiles
    )

    print("Generating multi-tier dependencies...")

    dependencies = generate_dependencies(
        assets,
        services
    )

    validate_generated_dataset(
        assets,
        services,
        dependencies
    )

    save_dataset(
        assets,
        services,
        dependencies
    )

    print("\n")
    print("=" * 70)
    print("          GENERATION COMPLETE")
    print("=" * 70)

    print("\nV1 remains unchanged inside data/.")
    print("V2 is available inside data_v2/.")
    print("\nNext step:")
    print(
        "Validate V2 with the existing framework before replacing V1."
    )

if __name__ == "__main__":
    main()