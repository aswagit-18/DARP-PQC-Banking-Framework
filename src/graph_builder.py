import networkx as nx
import matplotlib.pyplot as plt
from data_loader import load_data

def build_graph(assets, services, dependencies):
    graph = nx.DiGraph()

    for _, row in services.iterrows():
        graph.add_node(
            row["service_id"],
            node_type="Banking Service",
            name=row["service_name"],
            tier="Service",
            criticality=row["criticality"],
            data_sensitivity=row["data_sensitivity"]
        )

    for _, row in assets.iterrows():
        graph.add_node(
            row["asset_id"],
            node_type="Cryptographic/System Asset",
            name=row["asset_name"],
            asset_type=row["asset_type"],
            tier=row["tier"],
            service_id=row["service_id"],
            algorithm=row["algorithm"],
            key_size=row["key_size"],
            crypto_function=row["crypto_function"],
            data_sensitivity=row["data_sensitivity"],
            data_lifetime=row["data_lifetime"],
            business_criticality=row["business_criticality"],
            external_exposure=row["external_exposure"],
            hndl_exposure=row["hndl_exposure"],
            migration_complexity=row["migration_complexity"],
            quantum_vulnerability=row["quantum_vulnerability"],
            provider=row["provider"]
        )

    for _, row in dependencies.iterrows():
        source_id = row["source_id"]
        target_id = row["target_id"]
        new_strength = float(row["dependency_strength"])

        # A DiGraph can store only one edge per source-target pair.
        # If the input contains duplicate endpoint pairs, retain the strongest
        # observed dependency rather than silently allowing a later, weaker
        # row to overwrite it. This keeps V1 reproducible and V2 unchanged.
        existing = graph.get_edge_data(source_id, target_id)
        if existing is not None:
            if new_strength <= float(existing.get("dependency_strength", 0.0)):
                existing["crypto_dependency"] = max(
                    int(existing.get("crypto_dependency", 0)),
                    int(row["crypto_dependency"])
                )
                existing["data_dependency"] = max(
                    int(existing.get("data_dependency", 0)),
                    int(row["data_dependency"])
                )
                existing["critical_dependency"] = max(
                    int(existing.get("critical_dependency", 0)),
                    int(row["critical_dependency"])
                )
                continue

        graph.add_edge(
            source_id,
            target_id,
            dependency_type=row["dependency_type"],
            dependency_strength=new_strength,
            crypto_dependency=row["crypto_dependency"],
            data_dependency=row["data_dependency"],
            critical_dependency=row["critical_dependency"]
        )

    return graph

def print_graph_statistics(graph):
    print("\n========== GRAPH STATISTICS ==========")
    print(f"Number of nodes : {graph.number_of_nodes()}")
    print(f"Number of edges : {graph.number_of_edges()}")
    print("\nNode types:")

    node_types = {}

    for _, data in graph.nodes(data=True):
        node_type = data.get("node_type", "Unknown")
        node_types[node_type] = node_types.get(node_type, 0) + 1

    for node_type, count in node_types.items():
        print(f"{node_type}: {count}")

    print("\nTier distribution:")

    tiers = {}

    for _, data in graph.nodes(data=True):
        tier = data.get("tier", "Unknown")
        tiers[tier] = tiers.get(tier, 0) + 1

    for tier, count in tiers.items():
        print(f"{tier}: {count}")

    print("\n========== GRAPH CREATED ==========")

def find_multi_tier_paths(graph, max_length=4):
    print("\n========== MULTI-TIER PATHS ==========")

    paths_found = []

    service_nodes = [
        node
        for node, data in graph.nodes(data=True)
        if data.get("node_type") == "Banking Service"
    ]

    sub_tier_nodes = [
        node
        for node, data in graph.nodes(data=True)
        if data.get("tier") == "Sub-Tier"
    ]

    for source in service_nodes:
        for target in sub_tier_nodes:
            try:
                paths = nx.all_simple_paths(
                    graph,
                    source=source,
                    target=target,
                    cutoff=max_length
                )

                for path in paths:
                    tiers = []

                    for node in path:
                        tier = graph.nodes[node].get("tier")

                        if tier not in tiers:
                            tiers.append(tier)

                    if (
                        "Internal" in tiers
                        and "Third-Party" in tiers
                        and "Sub-Tier" in tiers
                    ):
                        paths_found.append(path)

            except nx.NetworkXNoPath:
                continue

    print(f"Multi-tier paths found: {len(paths_found)}")

    for i, path in enumerate(paths_found[:10], start=1):
        names = []

        for node in path:
            name = graph.nodes[node].get("name", node)
            names.append(name)

        print(f"\nPath {i}:")
        print(" → ".join(names))

    return paths_found

def visualize_graph(graph, output_path):
    plt.figure(figsize=(18, 12))

    positions = nx.spring_layout(
        graph,
        seed=42,
        k=1.2
    )

    nx.draw_networkx_nodes(
        graph,
        positions,
        node_size=700
    )

    nx.draw_networkx_edges(
        graph,
        positions,
        arrows=True,
        arrowsize=15,
        alpha=0.6
    )

    labels = {}

    for node, data in graph.nodes(data=True):
        labels[node] = data.get("name", node)

    nx.draw_networkx_labels(
        graph,
        positions,
        labels,
        font_size=7
    )

    plt.title("Multi-Tier Digital Banking Cryptographic Dependency Graph")
    plt.axis("off")
    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print("\nGraph visualization saved to:")
    print(output_path)

if __name__ == "__main__":
    assets, services, dependencies = load_data()

    graph = build_graph(
        assets,
        services,
        dependencies
    )

    print_graph_statistics(graph)

    paths = find_multi_tier_paths(graph)

    output_path = "../results/figures/multi_tier_dependency_graph.png"

    visualize_graph(
        graph,
        output_path
    )