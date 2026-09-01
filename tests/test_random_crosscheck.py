from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

from generator import generate_block_tree  # noqa: E402
from mmacm import solve_min_weight_maximal_acyclic_matching, verify_solution  # noqa: E402
from mmacm.bruteforce import brute_force_min_weight_maximal_acyclic_matching  # noqa: E402


def test_random_small_instances() -> None:
    for family in ("cactus", "block_graph", "multipartite", "mixed"):
        for order in range(2, 10):
            for seed in range(4):
                instance = generate_block_tree(
                    order,
                    seed=10_000 + 101 * order + seed,
                    family=family,
                    min_weight=-5,
                    max_weight=7,
                    min_vertex_cost=-3,
                    max_vertex_cost=4,
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
                assert result.cost == optimum
                assert verify_solution(instance.graph, result.matching).ok
