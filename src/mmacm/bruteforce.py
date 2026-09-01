from __future__ import annotations

from math import inf
from typing import Any, Iterable, Mapping

import networkx as nx

from .checker import check_maximal_acyclic_matching
from .core import Edge, Node, Number, edge_key, normalize_edge_weights, normalize_vertex_costs


def enumerate_matchings(graph: nx.Graph) -> Iterable[tuple[Edge, ...]]:
    edges = tuple(graph.edges())

    def rec(index: int, used: set[Node], chosen: list[Edge]):
        if index == len(edges):
            yield tuple(chosen)
            return
        yield from rec(index + 1, used, chosen)
        u, v = edges[index]
        if u not in used and v not in used:
            used.add(u)
            used.add(v)
            chosen.append((u, v))
            yield from rec(index + 1, used, chosen)
            chosen.pop()
            used.remove(u)
            used.remove(v)

    yield from rec(0, set(), [])


def brute_force_min_weight_maximal_acyclic_matching(
    graph: nx.Graph,
    edge_weights: Mapping[Any, Number] | None = None,
    vertex_costs: Mapping[Node, Number] | None = None,
    *,
    default_edge_weight: Number = 1,
) -> tuple[Number | float, tuple[Edge, ...]]:
    weights = normalize_edge_weights(graph.edges(), edge_weights, default_edge_weight)
    vcosts = normalize_vertex_costs(graph.nodes(), vertex_costs)
    best: Number | float = inf
    best_matching: tuple[Edge, ...] = tuple()
    for matching in enumerate_matchings(graph):
        if not check_maximal_acyclic_matching(graph, matching):
            continue
        saturated = {v for edge in matching for v in edge}
        value: Number | float = 0
        for u, v in matching:
            value = value + weights[edge_key(u, v)]
        for v in saturated:
            value = value + vcosts[v]
        if value < best:
            best = value
            best_matching = matching
    return best, best_matching
