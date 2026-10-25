import pandas as pd
from remediation import evaluate_ecosystem, calculate_all_remediation_impacts, simulate_asset_remediation

def calculate_migration_cost(migration_complexity):
    migration_complexity = float(migration_complexity)
    if not 0 <= migration_complexity <= 1:
        raise ValueError("migration_complexity must be between 0 and 1.")
    if migration_complexity <= 0:
        raise ValueError("migration_complexity must be greater than zero for cost-aware prioritization.")
    return migration_complexity

def calculate_priority_score(delta_er, migration_cost):
    delta_er = float(delta_er)
    migration_cost = float(migration_cost)
    if migration_cost <= 0:
        raise ValueError("migration_cost must be greater than zero.")
    return delta_er / migration_cost

def classify_remediation_effect(delta_er, tolerance=1e-12):
    delta_er = float(delta_er)
    if delta_er > tolerance:
        return "Risk Reduction"
    elif delta_er < -tolerance:
        return "Risk Increase"
    else:
        return "No Change"

def calculate_static_priorities(remediation_results):
    required_columns = [
        "asset_id",
        "asset_name",
        "tier",
        "algorithm",
        "delta_er",
        "migration_complexity"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in remediation_results.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required prioritization columns: "
            + ", ".join(missing_columns)
        )

    results = remediation_results.copy()

    results["migration_cost"] = results[
        "migration_complexity"
    ].apply(calculate_migration_cost)

    results["priority_score"] = results.apply(
        lambda row: calculate_priority_score(
            row["delta_er"],
            row["migration_cost"]
        ),
        axis=1
    )

    results["remediation_effect"] = results[
        "delta_er"
    ].apply(classify_remediation_effect)

    results = results.sort_values(
        by=["priority_score", "delta_er"],
        ascending=[False, False]
    ).reset_index(drop=True)

    results["priority_rank"] = range(1, len(results) + 1)

    return results

def print_priority_results(priority_results, top_n=15):
    if priority_results.empty:
        print("\nNo prioritization results available.")
        return

    display_columns = [
        "priority_rank",
        "asset_id",
        "asset_name",
        "tier",
        "algorithm",
        "delta_er",
        "migration_cost",
        "priority_score",
        "remediation_effect"
    ]

    display_columns = [
        column for column in display_columns
        if column in priority_results.columns
    ]

    display = priority_results[
        display_columns
    ].head(top_n).copy()

    numeric_columns = [
        "delta_er",
        "migration_cost",
        "priority_score"
    ]

    for column in numeric_columns:
        if column in display.columns:
            display[column] = display[column].round(6)

    print("\n")
    print("=" * 110)
    print("              COST-AWARE PQC MIGRATION PRIORITIZATION")
    print("=" * 110)
    print(f"\nTop {min(top_n, len(display))} Priority Candidates:\n")
    print(display.to_string(index=False))

    if "remediation_effect" in priority_results.columns:
        print("\nRemediation Effect Summary:\n")
        print(priority_results["remediation_effect"].value_counts().to_string())

def apply_remediation(assets, asset_id):
    return simulate_asset_remediation(
        assets=assets,
        asset_id=asset_id,
        remediated_quantum_vulnerability=0.0
    )

def get_remaining_candidates(assets, vulnerability_threshold=0.25):
    return assets[
        assets["quantum_vulnerability"] > vulnerability_threshold
    ].copy()

def dynamic_prioritization(
    assets,
    services,
    dependencies,
    max_steps=None,
    vulnerability_threshold=0.25
):
    current_assets = assets.copy()
    sequence = []
    step = 1

    while True:
        if max_steps is not None and step > max_steps:
            break

        remaining_candidates = get_remaining_candidates(
            current_assets,
            vulnerability_threshold
        )

        if remaining_candidates.empty:
            print("\nNo remaining vulnerable assets require remediation.")
            break

        current_ecosystem = evaluate_ecosystem(
            current_assets,
            services,
            dependencies
        )

        er_before = float(current_ecosystem["ecosystem_risk"])

        print("\n")
        print("=" * 70)
        print(f"DYNAMIC PRIORITIZATION STEP {step}")
        print("=" * 70)
        print(f"\nCurrent Ecosystem Risk: {er_before:.6f}")
        print(f"Remaining Candidates: {len(remaining_candidates)}")

        remediation_results = calculate_all_remediation_impacts(
            current_assets,
            services,
            dependencies,
            vulnerability_threshold
        )

        if remediation_results.empty:
            print("\nNo remediation results available.")
            break

        priority_results = calculate_static_priorities(
            remediation_results
        )

        if priority_results.empty:
            break

        selected = priority_results.iloc[0]

        if selected["delta_er"] <= 0:
            print(
                "\nNo remaining remediation produces "
                "a positive ecosystem-risk reduction."
            )
            break

        selected_asset_id = selected["asset_id"]
        selected_asset_name = selected["asset_name"]
        migration_cost = float(selected["migration_cost"])
        priority_score = float(selected["priority_score"])
        predicted_er_after = float(
            selected["ecosystem_risk_after"]
        )

        current_assets = apply_remediation(
            current_assets,
            selected_asset_id
        )

        after_results = evaluate_ecosystem(
            current_assets,
            services,
            dependencies
        )

        actual_er_after = float(
            after_results["ecosystem_risk"]
        )

        actual_delta_er = er_before - actual_er_after

        sequence.append({
            "step": step,
            "asset_id": selected_asset_id,
            "asset_name": selected_asset_name,
            "tier": selected["tier"],
            "algorithm": selected["algorithm"],
            "ecosystem_risk_before": er_before,
            "predicted_ecosystem_risk_after": predicted_er_after,
            "ecosystem_risk_after": actual_er_after,
            "delta_er": actual_delta_er,
            "migration_cost": migration_cost,
            "priority_score": priority_score,
            "remediation_effect": classify_remediation_effect(
                actual_delta_er
            )
        })

        print(
            f"\nSelected Asset: "
            f"{selected_asset_id} - {selected_asset_name}"
        )
        print(f"Migration Cost: {migration_cost:.6f}")
        print(f"Delta ER: {actual_delta_er:.6f}")
        print(f"Priority Score: {priority_score:.6f}")
        print(f"ER Before: {er_before:.6f}")
        print(f"ER After: {actual_er_after:.6f}")

        step += 1

    return pd.DataFrame(sequence)

def print_dynamic_sequence(sequence):
    if sequence.empty:
        print("\nNo dynamic remediation sequence generated.")
        return

    display_columns = [
        "step",
        "asset_id",
        "asset_name",
        "tier",
        "algorithm",
        "ecosystem_risk_before",
        "ecosystem_risk_after",
        "delta_er",
        "migration_cost",
        "priority_score",
        "remediation_effect"
    ]

    display_columns = [
        column for column in display_columns
        if column in sequence.columns
    ]

    display = sequence[
        display_columns
    ].copy()

    numeric_columns = [
        "ecosystem_risk_before",
        "ecosystem_risk_after",
        "delta_er",
        "migration_cost",
        "priority_score"
    ]

    for column in numeric_columns:
        if column in display.columns:
            display[column] = display[column].round(6)

    print("\n")
    print("=" * 120)
    print("                 DYNAMIC COST-AWARE PQC MIGRATION SEQUENCE")
    print("=" * 120)
    print("\n" + display.to_string(index=False))

    initial_er = float(
        sequence.iloc[0]["ecosystem_risk_before"]
    )

    final_er = float(
        sequence.iloc[-1]["ecosystem_risk_after"]
    )

    cumulative_delta_er = initial_er - final_er
    cumulative_cost = sequence["migration_cost"].sum()

    print("\n")
    print("=" * 70)
    print("DYNAMIC PRIORITIZATION SUMMARY")
    print("=" * 70)
    print(f"\nNumber of Remediations: {len(sequence)}")
    print(f"Initial Ecosystem Risk: {initial_er:.6f}")
    print(f"Final Ecosystem Risk: {final_er:.6f}")
    print(f"Cumulative Risk Reduction: {cumulative_delta_er:.6f}")
    print(f"Cumulative Migration Cost: {cumulative_cost:.6f}")

    if cumulative_cost > 0:
        print(
            f"Cumulative Risk Reduction / Cost: "
            f"{cumulative_delta_er / cumulative_cost:.6f}"
        )

if __name__ == "__main__":
    print("\nprioritization.py created successfully.")
    print("Run main.py for static prioritization.")
    print(
        "Dynamic prioritization can be enabled "
        "after static results are validated."
    )