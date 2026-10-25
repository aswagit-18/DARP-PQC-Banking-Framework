import pandas as pd
from data_loader import load_data
from risk_model import calculate_direct_risk

DEFAULT_MAX_PATH_LENGTH = 6
DEFAULT_VULNERABILITY_THRESHOLD = 0.25

def calculate_path_risk(graph, path, direct_risk_lookup):
    if not path:
        return 0.0

    source_asset = str(path[-1])

    if source_asset not in direct_risk_lookup:
        return 0.0

    direct_risk = float(direct_risk_lookup[source_asset])
    propagation_factor = 1.0

    for index in range(len(path) - 1):
        source = path[index]
        target = path[index + 1]

        edge_data = graph.get_edge_data(source, target)

        if edge_data is None:
            return 0.0

        dependency_strength = float(
            edge_data.get("dependency_strength", 1.0)
        )

        propagation_factor *= dependency_strength

    path_risk = direct_risk * propagation_factor
    return float(path_risk)

def find_service_paths(
    graph,
    service_id,
    max_path_length=DEFAULT_MAX_PATH_LENGTH
):
    service_id = str(service_id)

    if service_id not in graph:
        return []

    current_level = {
        service_id: (
            1.0,
            [service_id]
        )
    }

    best_asset_paths = {}

    for _ in range(max_path_length):
        next_level = {}

        for current_node, current_data in current_level.items():
            current_strength, current_path = current_data

            if current_node not in graph:
                continue

            for target in graph.successors(current_node):
                if target in current_path:
                    continue

                edge_data = graph.get_edge_data(
                    current_node,
                    target
                )

                if edge_data is None:
                    continue

                dependency_strength = float(
                    edge_data.get(
                        "dependency_strength",
                        1.0
                    )
                )

                candidate_strength = (
                    current_strength
                    * dependency_strength
                )

                candidate_path = (
                    current_path
                    + [target]
                )

                existing_result = next_level.get(target)

                if (
                    existing_result is None
                    or candidate_strength > existing_result[0]
                ):
                    next_level[target] = (
                        candidate_strength,
                        candidate_path
                    )

        for node, result in next_level.items():
            strength, path = result

            node_type = graph.nodes[node].get(
                "node_type",
                ""
            )

            if node_type != "Cryptographic/System Asset":
                continue

            existing_best = best_asset_paths.get(node)

            if (
                existing_best is None
                or strength > existing_best[0]
            ):
                best_asset_paths[node] = (
                    strength,
                    path
                )

        current_level = next_level

        if not current_level:
            break

    return [
        result[1]
        for result in best_asset_paths.values()
    ]

def calculate_dependency_weight(graph, path):
    if not path:
        return 0.0

    dependency_weight = 1.0

    for index in range(len(path) - 1):
        source = path[index]
        target = path[index + 1]

        edge_data = graph.get_edge_data(
            source,
            target
        )

        if edge_data is None:
            return 0.0

        dependency_strength = float(
            edge_data.get(
                "dependency_strength",
                1.0
            )
        )

        dependency_weight *= dependency_strength

    return float(dependency_weight)

def calculate_service_propagation(
    graph,
    services,
    assets,
    max_path_length=DEFAULT_MAX_PATH_LENGTH,
    vulnerability_threshold=DEFAULT_VULNERABILITY_THRESHOLD
):
    if "direct_risk" in assets.columns:
        risk_assets = assets.copy()
    else:
        risk_assets = calculate_direct_risk(assets)

    risk_assets["asset_id"] = (
        risk_assets["asset_id"].astype(str)
    )

    direct_risk_lookup = dict(
        zip(
            risk_assets["asset_id"],
            risk_assets["direct_risk"]
        )
    )

    vulnerability_lookup = dict(
        zip(
            risk_assets["asset_id"],
            risk_assets["quantum_vulnerability"]
        )
    )

    asset_id_set = set(
        risk_assets["asset_id"]
    )

    service_results = []
    all_path_results = []
    all_asset_details = []

    for _, service in services.iterrows():
        service_id = str(
            service["service_id"]
        )

        service_name = str(
            service["service_name"]
        )

        paths = find_service_paths(
            graph,
            service_id,
            max_path_length
        )

        asset_contributions = {}

        for path in paths:
            if not path:
                continue

            asset_id = str(path[-1])

            if asset_id not in asset_id_set:
                continue

            dependency_weight = calculate_dependency_weight(
                graph,
                path
            )

            if dependency_weight <= 0:
                continue

            existing = asset_contributions.get(
                asset_id
            )

            if (
                existing is None
                or dependency_weight
                > existing["dependency_weight"]
            ):
                asset_contributions[asset_id] = {
                    "path": path,
                    "path_length": len(path) - 1,
                    "dependency_weight": dependency_weight
                }

        weighted_risk_sum = 0.0
        dependency_weight_sum = 0.0
        vulnerable_asset_count = 0
        vulnerable_path_count = 0

        for asset_id, contribution in asset_contributions.items():
            dependency_weight = float(
                contribution["dependency_weight"]
            )

            dependency_weight_sum += dependency_weight

            quantum_vulnerability = float(
                vulnerability_lookup.get(
                    asset_id,
                    0.0
                )
            )

            if (
                quantum_vulnerability
                <= vulnerability_threshold
            ):
                continue

            vulnerable_asset_count += 1
            vulnerable_path_count += 1

            direct_risk = float(
                direct_risk_lookup.get(
                    asset_id,
                    0.0
                )
            )

            path_risk = (
                direct_risk
                * dependency_weight
            )

            weighted_contribution = (
                path_risk
                * dependency_weight
            )

            weighted_risk_sum += weighted_contribution

            detail = {
                "service_id": service_id,
                "service_name": service_name,
                "source_asset": asset_id,
                "path": contribution["path"],
                "path_length": contribution["path_length"],
                "path_risk": path_risk,
                "dependency_weight": dependency_weight,
                "weighted_contribution": weighted_contribution
            }

            all_path_results.append(detail)
            all_asset_details.append(detail)

        if dependency_weight_sum > 0:
            inherited_risk = (
                weighted_risk_sum
                / dependency_weight_sum
            )
        else:
            inherited_risk = 0.0

        inherited_risk = max(
            0.0,
            min(
                1.0,
                inherited_risk
            )
        )

        service_results.append({
            "service_id": service_id,
            "service_name": service_name,
            "number_of_paths": vulnerable_path_count,
            "number_of_vulnerable_assets": vulnerable_asset_count,
            "number_of_reachable_assets": len(
                asset_contributions
            ),
            "dependency_weight_sum": dependency_weight_sum,
            "inherited_quantum_risk": inherited_risk
        })

    return (
        pd.DataFrame(service_results),
        all_path_results,
        all_asset_details
    )

if __name__ == "__main__":
    from graph_builder import build_graph

    print("\n")
    print("=" * 75)
    print("       OPTIMIZED PATH-AWARE QUANTUM RISK PROPAGATION")
    print("=" * 75)

    assets, services, dependencies = load_data()

    print(f"\nAssets       : {len(assets)}")
    print(f"Services     : {len(services)}")
    print(f"Dependencies : {len(dependencies)}")

    risk_assets = calculate_direct_risk(
        assets
    )

    graph = build_graph(
        risk_assets,
        services,
        dependencies
    )

    print(f"\nGraph nodes : {graph.number_of_nodes()}")
    print(f"Graph edges : {graph.number_of_edges()}")

    (
        service_results,
        path_results,
        asset_details
    ) = calculate_service_propagation(
        graph,
        services,
        risk_assets
    )

    print("\n")
    print("=" * 75)
    print("SERVICE-LEVEL INHERITED QUANTUM RISK")
    print("=" * 75)

    print(
        "\n"
        + service_results.to_string(
            index=False
        )
    )

    print("\n")
    print("=" * 75)
    print("PROPAGATION SUMMARY")
    print("=" * 75)

    print(
        f"\nTotal services analyzed: "
        f"{len(service_results)}"
    )

    print(
        f"Total strongest vulnerable paths: "
        f"{len(path_results)}"
    )

    print(
        f"Total asset contributions: "
        f"{len(asset_details)}"
    )

    if not service_results.empty:
        top_services = service_results.sort_values(
            by="inherited_quantum_risk",
            ascending=False
        )

        print(
            "\nTop inherited-risk services:\n"
        )

        print(
            top_services[
                [
                    "service_id",
                    "service_name",
                    "number_of_reachable_assets",
                    "number_of_vulnerable_assets",
                    "inherited_quantum_risk"
                ]
            ].to_string(
                index=False
            )
        )

    print("\n")
    print("=" * 75)
    print("SAMPLE STRONGEST PROPAGATION PATHS")
    print("=" * 75)

    for index, result in enumerate(
        path_results[:10],
        start=1
    ):
        names = []

        for node in result["path"]:
            node_name = graph.nodes[node].get(
                "name",
                node
            )
            names.append(str(node_name))

        print(f"\nPath {index}:")
        print(" -> ".join(names))
        print(f"Asset: {result['source_asset']}")
        print(
            f"Dependency Weight: "
            f"{result['dependency_weight']:.6f}"
        )
        print(
            f"Path Risk: "
            f"{result['path_risk']:.6f}"
        )

    print("\n")
    print("=" * 75)
    print("PROPAGATION COMPLETE")
    print("=" * 75)