from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from generator import generate_block_tree  # noqa: E402
from mmacm import (  # noqa: E402
    UnsupportedBlockError,
    check_maximal_acyclic_matching,
    check_maximal_acyclic_matching_fast,
    solve_min_weight_maximal_acyclic_matching,
    verify_solution,
)
from mmacm.blocks import analyze_graph  # noqa: E402
from mmacm.bruteforce import (  # noqa: E402
    brute_force_min_weight_maximal_acyclic_matching,
    enumerate_matchings,
)


def target_class(graph: nx.Graph) -> bool:
    try:
        analyze_graph(graph)
        return True
    except UnsupportedBlockError:
        return False


def main() -> None:
    start = time.perf_counter()
    rng = random.Random(20260829)
    atlas_graphs = [nx.convert_node_labels_to_integers(g) for g in nx.graph_atlas_g() if len(g) > 0]
    target_graphs = [g for g in atlas_graphs if target_class(g)]

    checks = 0
    witnesses = 0
    weighted_instances = 0
    max_order = 0
    max_edges = 0

    for index, graph in enumerate(target_graphs):
        max_order = max(max_order, len(graph))
        max_edges = max(max_edges, graph.number_of_edges())
        scenarios = [(None, None, "unweighted")]
        for rep in range(2):
            edge_weights = {(u, v): rng.randint(-8, 11) for u, v in graph.edges()}
            vertex_costs = {v: rng.randint(-5, 7) for v in graph.nodes()}
            scenarios.append((edge_weights, vertex_costs, f"weighted-{rep}"))

        for edge_weights, vertex_costs, label in scenarios:
            result = solve_min_weight_maximal_acyclic_matching(
                graph,
                edge_weights,
                vertex_costs,
                verify=True,
            )
            optimum, brute_matching = brute_force_min_weight_maximal_acyclic_matching(
                graph,
                edge_weights,
                vertex_costs,
            )
            if result.cost != optimum:
                raise AssertionError(
                    f"atlas mismatch at graph {index}, {label}: "
                    f"solver={result.cost}, brute={optimum}, "
                    f"edges={sorted(graph.edges())}, witness={result.matching}, brute={brute_matching}"
                )
            if not verify_solution(graph, result.matching).ok:
                raise AssertionError(f"invalid reconstructed witness at atlas graph {index}")
            checks += 1
            witnesses += 1
            if edge_weights is not None:
                weighted_instances += 1

    # Verify the fast independent checker against the definition-level checker
    # on every matching of every connected target atlas graph.
    checker_matchings = 0
    for graph in target_graphs:
        if not nx.is_connected(graph):
            continue
        for matching in enumerate_matchings(graph):
            direct = check_maximal_acyclic_matching(graph, matching)
            fast = check_maximal_acyclic_matching_fast(graph, matching)
            if direct != fast:
                raise AssertionError(
                    f"fast checker mismatch on edges={sorted(graph.edges())}, matching={matching}"
                )
            checker_matchings += 1

    # Random glued-block instances with mixed block types.
    random_instances = 0
    for family in ("cactus", "block_graph", "multipartite", "mixed"):
        for order in range(2, 11):
            for rep in range(10):
                instance = generate_block_tree(
                    order,
                    seed=500_000 + 10_000 * order + 101 * rep + len(family),
                    family=family,
                    min_weight=-8,
                    max_weight=12,
                    min_vertex_cost=-5,
                    max_vertex_cost=7,
                )
                result = solve_min_weight_maximal_acyclic_matching(
                    instance.graph,
                    instance.edge_weights,
                    instance.vertex_costs,
                    verify=True,
                )
                optimum, _ = brute_force_min_weight_maximal_acyclic_matching(
                    instance.graph,
                    instance.edge_weights,
                    instance.vertex_costs,
                )
                if result.cost != optimum:
                    raise AssertionError(
                        f"random mismatch family={family}, order={order}, rep={rep}, "
                        f"solver={result.cost}, brute={optimum}"
                    )
                random_instances += 1

    # Unsupported biconnected block must be rejected.
    rejected = False
    try:
        solve_min_weight_maximal_acyclic_matching(nx.house_graph())
    except UnsupportedBlockError:
        rejected = True
    if not rejected:
        raise AssertionError("unsupported house block was not rejected")

    elapsed = time.perf_counter() - start
    payload = {
        "status": "PASS",
        "date": "2026-08-29",
        "atlas_nonempty_graphs": len(atlas_graphs),
        "atlas_target_class_graphs": len(target_graphs),
        "atlas_solver_vs_bruteforce_instances": checks,
        "atlas_weighted_instances": weighted_instances,
        "atlas_reconstructed_witnesses_checked": witnesses,
        "checker_definition_equivalence_matchings": checker_matchings,
        "random_small_instances": random_instances,
        "unsupported_block_rejection": rejected,
        "maximum_atlas_order": max_order,
        "maximum_atlas_edges": max_edges,
        "elapsed_seconds": elapsed,
        "python": sys.version,
        "networkx": nx.__version__,
    }
    output = ROOT / "experiments" / "results" / "correctness_audit.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
