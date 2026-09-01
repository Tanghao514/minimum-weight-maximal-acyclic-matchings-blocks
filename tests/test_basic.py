from __future__ import annotations

import networkx as nx
import pytest

from mmacm import UnsupportedBlockError, solve_min_weight_maximal_acyclic_matching, verify_solution
from mmacm.bruteforce import brute_force_min_weight_maximal_acyclic_matching


@pytest.mark.parametrize(
    "graph",
    [
        nx.path_graph(2),
        nx.path_graph(3),
        nx.path_graph(7),
        nx.cycle_graph(3),
        nx.cycle_graph(4),
        nx.cycle_graph(7),
        nx.complete_graph(5),
        nx.complete_bipartite_graph(2, 4),
    ],
)
def test_unweighted_against_bruteforce(graph: nx.Graph) -> None:
    result = solve_min_weight_maximal_acyclic_matching(graph, verify=True)
    optimum, _ = brute_force_min_weight_maximal_acyclic_matching(graph)
    assert result.cost == optimum
    assert verify_solution(graph, result.matching).ok


def test_negative_weights_and_vertex_costs() -> None:
    graph = nx.cycle_graph(6)
    weights = {(u, v): (u - v) * 3 for u, v in graph.edges()}
    vertex_costs = {v: (-1) ** v * v for v in graph}
    result = solve_min_weight_maximal_acyclic_matching(
        graph, weights, vertex_costs, verify=True
    )
    optimum, _ = brute_force_min_weight_maximal_acyclic_matching(
        graph, weights, vertex_costs
    )
    assert result.cost == optimum


def test_disconnected_and_isolated_vertices() -> None:
    graph = nx.disjoint_union_all([nx.cycle_graph(5), nx.path_graph(4), nx.empty_graph(2)])
    result = solve_min_weight_maximal_acyclic_matching(graph, verify=True)
    optimum, _ = brute_force_min_weight_maximal_acyclic_matching(graph)
    assert result.cost == optimum


def test_reject_unsupported_block() -> None:
    with pytest.raises(UnsupportedBlockError):
        solve_min_weight_maximal_acyclic_matching(nx.house_graph())


def test_fast_checker_matches_definition() -> None:
    from mmacm import check_maximal_acyclic_matching, check_maximal_acyclic_matching_fast
    from mmacm.bruteforce import enumerate_matchings

    for graph in (nx.path_graph(5), nx.cycle_graph(6), nx.complete_bipartite_graph(2, 3)):
        for matching in enumerate_matchings(graph):
            assert check_maximal_acyclic_matching_fast(graph, matching) == check_maximal_acyclic_matching(graph, matching)
