from __future__ import annotations

from fractions import Fraction

import networkx as nx
import pytest

from mmacm import solve_min_weight_maximal_acyclic_matching, verify_solution
from mmacm.bruteforce import brute_force_min_weight_maximal_acyclic_matching


def test_empty_graph_and_only_isolates() -> None:
    for graph in (nx.Graph(), nx.empty_graph(7)):
        result = solve_min_weight_maximal_acyclic_matching(graph, verify=True)
        assert result.cost == 0
        assert result.matching == tuple()


def test_fraction_weights_are_exact_in_arithmetic_model() -> None:
    graph = nx.cycle_graph(5)
    weights = {(u, v): Fraction(u + v + 1, 7) for u, v in graph.edges()}
    costs = {v: Fraction((-1) ** v, 11) for v in graph}
    result = solve_min_weight_maximal_acyclic_matching(graph, weights, costs, verify=True)
    optimum, _ = brute_force_min_weight_maximal_acyclic_matching(graph, weights, costs)
    assert result.cost == optimum


def test_heterogeneous_hashable_labels() -> None:
    graph = nx.Graph()
    graph.add_edges_from([("a", 1), (1, (2,)), ((2,), "a")])
    result = solve_min_weight_maximal_acyclic_matching(graph, verify=True)
    assert verify_solution(graph, result.matching).ok


def test_invalid_graph_types_are_rejected() -> None:
    directed = nx.DiGraph([(0, 1)])
    with pytest.raises(ValueError):
        solve_min_weight_maximal_acyclic_matching(directed)

    multigraph = nx.MultiGraph()
    multigraph.add_edge(0, 1)
    with pytest.raises(ValueError):
        solve_min_weight_maximal_acyclic_matching(multigraph)

    looped = nx.Graph()
    looped.add_edge(0, 0)
    with pytest.raises(ValueError):
        solve_min_weight_maximal_acyclic_matching(looped)
