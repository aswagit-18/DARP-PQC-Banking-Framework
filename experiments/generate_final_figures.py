from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TABLE_DIR = PROJECT_ROOT / "results" / "tables"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)


def budget_sweep_plot():
    df = pd.read_csv(TABLE_DIR / "budget_sweep.csv")
    fig, ax = plt.subplots(figsize=(9, 6))
    for strategy, group in df.groupby("strategy"):
        group = group.sort_values("budget_scenario")
        ax.plot(
            group["budget_scenario"],
            group["risk_reduction_percent"],
            marker="o",
            label=strategy,
        )
    ax.set_xlabel("Migration budget (normalized cost units)")
    ax.set_ylabel("Ecosystem risk reduction (%)")
    ax.set_title("Equal-Budget PQC Migration Strategy Comparison")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "budget_sweep_risk_reduction.png", dpi=220)
    plt.close(fig)


def topology_ablation_plot():
    df = pd.read_csv(TABLE_DIR / "ablation_topology.csv")
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.bar(df["topology_variant"], df["ecosystem_risk"])
    ax.set_ylabel("Calculated ecosystem quantum risk")
    ax.set_title("Topology Ablation: Risk Hidden by Excluding External Tiers")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "topology_ablation.png", dpi=220)
    plt.close(fig)


def priority_ablation_plot():
    df = pd.read_csv(TABLE_DIR / "ablation_prioritization.csv")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.bar(df["variant"], df["risk_reduction_percent"])
    ax.set_ylabel("Risk reduction under equal budget (%)")
    ax.set_title("Prioritization Ablation")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "prioritization_ablation.png", dpi=220)
    plt.close(fig)


def scalability_plot():
    df = pd.read_csv(TABLE_DIR / "scalability_analysis.csv")
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.bar(df["dataset"], df["initial_all_candidate_ranking_seconds"])
    ax.set_xlabel("Synthetic dataset")
    ax.set_ylabel("Initial all-candidate ranking time (seconds)")
    ax.set_title("Prototype Scalability Benchmark")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "scalability_runtime.png", dpi=220)
    plt.close(fig)


def main():
    budget_sweep_plot()
    topology_ablation_plot()
    priority_ablation_plot()
    scalability_plot()
    print("Generated final figures in results/figures/.")


if __name__ == "__main__":
    main()
