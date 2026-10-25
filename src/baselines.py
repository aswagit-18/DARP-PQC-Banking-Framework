import pandas as pd
from risk_model import calculate_direct_risk
from remediation import evaluate_ecosystem, simulate_asset_remediation, calculate_all_remediation_impacts
from prioritization import calculate_static_priorities, calculate_migration_cost

DIRECT_RISK_STRATEGY = "Direct Risk First"
BUSINESS_CRITICALITY_STRATEGY = "Business Criticality First"
HNDL_STRATEGY = "HNDL Risk First"
PROPOSED_STRATEGY = "Proposed Dynamic DeltaER/Cost"

def get_vulnerable_candidates(assets, vulnerability_threshold=0.25):
    return assets[assets["quantum_vulnerability"] > vulnerability_threshold].copy()

def rank_direct_risk_first(assets, vulnerability_threshold=0.25):
    risk_assets = calculate_direct_risk(assets)
    candidates = get_vulnerable_candidates(risk_assets, vulnerability_threshold)
    candidates = candidates.sort_values(
        by=["direct_risk", "asset_id"],
        ascending=[False, True]
    ).reset_index(drop=True)
    candidates["strategy_score"] = candidates["direct_risk"]
    return candidates

def rank_business_criticality_first(assets, vulnerability_threshold=0.25):
    candidates = get_vulnerable_candidates(assets, vulnerability_threshold)
    candidates = candidates.sort_values(
        by=["business_criticality", "asset_id"],
        ascending=[False, True]
    ).reset_index(drop=True)
    candidates["strategy_score"] = candidates["business_criticality"]
    return candidates

def rank_hndl_first(assets, vulnerability_threshold=0.25):
    candidates = get_vulnerable_candidates(assets, vulnerability_threshold)
    candidates = candidates.sort_values(
        by=["hndl_exposure", "asset_id"],
        ascending=[False, True]
    ).reset_index(drop=True)
    candidates["strategy_score"] = candidates["hndl_exposure"]
    return candidates

def select_baseline_candidate(assets, strategy, remaining_budget, vulnerability_threshold=0.25):
    if strategy == DIRECT_RISK_STRATEGY:
        ranked = rank_direct_risk_first(assets, vulnerability_threshold)
    elif strategy == BUSINESS_CRITICALITY_STRATEGY:
        ranked = rank_business_criticality_first(assets, vulnerability_threshold)
    elif strategy == HNDL_STRATEGY:
        ranked = rank_hndl_first(assets, vulnerability_threshold)
    else:
        raise ValueError(f"Unknown baseline strategy: {strategy}")

    for _, candidate in ranked.iterrows():
        migration_cost = calculate_migration_cost(candidate["migration_complexity"])
        if migration_cost <= remaining_budget:
            candidate = candidate.copy()
            candidate["migration_cost"] = migration_cost
            return candidate
    return None

def run_baseline_under_budget(
    assets,
    services,
    dependencies,
    strategy,
    migration_budget,
    vulnerability_threshold=0.25
):
    if migration_budget <= 0:
        raise ValueError("migration_budget must be greater than zero.")

    current_assets = assets.copy()
    initial_results = evaluate_ecosystem(current_assets, services, dependencies)
    initial_er = float(initial_results["ecosystem_risk"])
    current_er = initial_er
    budget_used = 0.0
    sequence = []
    step = 1

    while True:
        remaining_budget = migration_budget - budget_used
        if remaining_budget <= 1e-12:
            break

        candidate = select_baseline_candidate(
            assets=current_assets,
            strategy=strategy,
            remaining_budget=remaining_budget,
            vulnerability_threshold=vulnerability_threshold
        )

        if candidate is None:
            break

        asset_id = candidate["asset_id"]
        migration_cost = float(candidate["migration_cost"])
        er_before = current_er

        current_assets = simulate_asset_remediation(
            current_assets,
            asset_id,
            remediated_quantum_vulnerability=0.0
        )

        after_results = evaluate_ecosystem(current_assets, services, dependencies)
        er_after = float(after_results["ecosystem_risk"])
        delta_er = er_before - er_after
        budget_used += migration_cost

        sequence.append({
            "strategy": strategy,
            "step": step,
            "asset_id": asset_id,
            "asset_name": candidate["asset_name"],
            "tier": candidate["tier"],
            "algorithm": candidate["algorithm"],
            "strategy_score": candidate["strategy_score"],
            "migration_cost": migration_cost,
            "cumulative_cost": budget_used,
            "ecosystem_risk_before": er_before,
            "ecosystem_risk_after": er_after,
            "delta_er": delta_er,
            "cumulative_delta_er": initial_er - er_after
        })

        current_er = er_after
        step += 1

    return pd.DataFrame(sequence)

def run_proposed_under_budget(
    assets,
    services,
    dependencies,
    migration_budget,
    vulnerability_threshold=0.25
):
    if migration_budget <= 0:
        raise ValueError("migration_budget must be greater than zero.")

    current_assets = assets.copy()
    initial_results = evaluate_ecosystem(current_assets, services, dependencies)
    initial_er = float(initial_results["ecosystem_risk"])
    current_er = initial_er
    budget_used = 0.0
    sequence = []
    step = 1

    while True:
        remaining_budget = migration_budget - budget_used

        if remaining_budget <= 1e-12:
            break

        vulnerable = get_vulnerable_candidates(current_assets, vulnerability_threshold)

        if vulnerable.empty:
            break

        remediation_results = calculate_all_remediation_impacts(
            current_assets,
            services,
            dependencies,
            vulnerability_threshold
        )

        if remediation_results.empty:
            break

        priorities = calculate_static_priorities(remediation_results)
        priorities = priorities[priorities["delta_er"] > 0].copy()
        priorities = priorities[priorities["migration_cost"] <= remaining_budget].copy()

        if priorities.empty:
            break

        selected = priorities.iloc[0]
        asset_id = selected["asset_id"]
        migration_cost = float(selected["migration_cost"])
        priority_score = float(selected["priority_score"])
        er_before = current_er

        current_assets = simulate_asset_remediation(
            current_assets,
            asset_id,
            remediated_quantum_vulnerability=0.0
        )

        after_results = evaluate_ecosystem(current_assets, services, dependencies)
        er_after = float(after_results["ecosystem_risk"])
        delta_er = er_before - er_after
        budget_used += migration_cost

        sequence.append({
            "strategy": PROPOSED_STRATEGY,
            "step": step,
            "asset_id": asset_id,
            "asset_name": selected["asset_name"],
            "tier": selected["tier"],
            "algorithm": selected["algorithm"],
            "strategy_score": priority_score,
            "migration_cost": migration_cost,
            "cumulative_cost": budget_used,
            "ecosystem_risk_before": er_before,
            "ecosystem_risk_after": er_after,
            "delta_er": delta_er,
            "cumulative_delta_er": initial_er - er_after
        })

        current_er = er_after
        step += 1

    return pd.DataFrame(sequence)

def summarize_strategy(sequence, strategy_name, initial_er, migration_budget):
    if sequence.empty:
        return {
            "strategy": strategy_name,
            "migration_budget": migration_budget,
            "budget_used": 0.0,
            "number_of_assets_migrated": 0,
            "initial_er": initial_er,
            "final_er": initial_er,
            "cumulative_delta_er": 0.0,
            "risk_reduction_per_cost": 0.0
        }

    final_er = float(sequence.iloc[-1]["ecosystem_risk_after"])
    budget_used = float(sequence.iloc[-1]["cumulative_cost"])
    cumulative_delta_er = initial_er - final_er
    efficiency = cumulative_delta_er / budget_used if budget_used > 0 else 0.0

    return {
        "strategy": strategy_name,
        "migration_budget": migration_budget,
        "budget_used": budget_used,
        "number_of_assets_migrated": len(sequence),
        "initial_er": initial_er,
        "final_er": final_er,
        "cumulative_delta_er": cumulative_delta_er,
        "risk_reduction_per_cost": efficiency
    }

def compare_strategies(
    assets,
    services,
    dependencies,
    migration_budget,
    vulnerability_threshold=0.25
):
    baseline = evaluate_ecosystem(assets, services, dependencies)
    initial_er = float(baseline["ecosystem_risk"])
    sequences = {}

    print("\nRunning B1: Direct Risk First...")
    sequences[DIRECT_RISK_STRATEGY] = run_baseline_under_budget(
        assets,
        services,
        dependencies,
        DIRECT_RISK_STRATEGY,
        migration_budget,
        vulnerability_threshold
    )

    print("\nRunning B2: Business Criticality First...")
    sequences[BUSINESS_CRITICALITY_STRATEGY] = run_baseline_under_budget(
        assets,
        services,
        dependencies,
        BUSINESS_CRITICALITY_STRATEGY,
        migration_budget,
        vulnerability_threshold
    )

    print("\nRunning B3: HNDL Risk First...")
    sequences[HNDL_STRATEGY] = run_baseline_under_budget(
        assets,
        services,
        dependencies,
        HNDL_STRATEGY,
        migration_budget,
        vulnerability_threshold
    )

    print("\nRunning B4: Proposed Dynamic DeltaER/Cost...")
    sequences[PROPOSED_STRATEGY] = run_proposed_under_budget(
        assets,
        services,
        dependencies,
        migration_budget,
        vulnerability_threshold
    )

    summaries = [
        summarize_strategy(sequence, strategy_name, initial_er, migration_budget)
        for strategy_name, sequence in sequences.items()
    ]

    comparison_df = pd.DataFrame(summaries)
    comparison_df = comparison_df.sort_values(
        by="cumulative_delta_er",
        ascending=False
    ).reset_index(drop=True)

    comparison_df["performance_rank"] = range(1, len(comparison_df) + 1)
    return comparison_df, sequences

def print_strategy_comparison(comparison_df):
    display = comparison_df.copy()

    numeric_columns = [
        "migration_budget",
        "budget_used",
        "initial_er",
        "final_er",
        "cumulative_delta_er",
        "risk_reduction_per_cost"
    ]

    for column in numeric_columns:
        if column in display.columns:
            display[column] = display[column].round(6)

    columns = [
        "performance_rank",
        "strategy",
        "migration_budget",
        "budget_used",
        "number_of_assets_migrated",
        "initial_er",
        "final_er",
        "cumulative_delta_er",
        "risk_reduction_per_cost"
    ]

    print("\n")
    print("=" * 125)
    print("                       EQUAL-BUDGET MIGRATION STRATEGY COMPARISON")
    print("=" * 125)
    print("\n" + display[columns].to_string(index=False))

if __name__ == "__main__":
    print("\nbaselines.py created successfully.")
    print("Run baseline comparison through main.py.")