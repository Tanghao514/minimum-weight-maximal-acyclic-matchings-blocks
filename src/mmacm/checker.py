from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import networkx as nx

from .core import Edge, Node, edge_key


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    is_matching: bool
    is_acyclic: bool
    is_maximal: bool
    message: str


def check_matching(graph: nx.Graph, matching: Iterable[Edge]) -> bool:
    used: set[Node] = set()
    for u, v in matching:
        if u == v or not graph.has_edge(u, v):
            return False
        if u in used or v in used:
            return False
        used.add(u)
        used.add(v)
    return True


def check_acyclic_matching(graph: nx.Graph, matching: Iterable[Edge]) -> bool:
    matching_tuple = tuple(matching)
    if not check_matching(graph, matching_tuple):
        return False
    saturated = {v for edge in matching_tuple for v in edge}
    induced = graph.subgraph(saturated)
    return induced.number_of_nodes() == 0 or nx.is_forest(induced)


def check_maximal_acyclic_matching(graph: nx.Graph, matching: Iterable[Edge]) -> bool:
    matching_tuple = tuple(matching)
    if not check_acyclic_matching(graph, matching_tuple):
        return False
    saturated = {v for edge in matching_tuple for v in edge}
    for u, v in graph.edges():
        if u in saturated or v in saturated:
            continue
        induced = graph.subgraph(saturated | {u, v})
        if induced.number_of_nodes() == 0 or nx.is_forest(induced):
            return False
    return True


def verify_solution(graph: nx.Graph, matching: Iterable[Edge]) -> VerificationResult:
    matching_tuple = tuple(matching)
    is_matching = check_matching(graph, matching_tuple)
    if not is_matching:
        return VerificationResult(False, False, False, False, "selected edges are not a matching")
    is_acyclic = check_acyclic_matching(graph, matching_tuple)
    if not is_acyclic:
        return VerificationResult(False, True, False, False, "saturated vertices do not induce a forest")
    is_maximal = check_maximal_acyclic_matching(graph, matching_tuple)
    if not is_maximal:
        return VerificationResult(False, True, True, False, "the acyclic matching is extendable")
    return VerificationResult(True, True, True, True, "valid maximal acyclic matching")


def check_maximal_acyclic_matching_fast(graph: nx.Graph, matching: Iterable[Edge]) -> bool:
    """Definition-equivalent maximality checker using the induced forest.

    Let S be the saturated set and F=G[S]. For an unsaturated vertex x,
    adding x alone creates a cycle exactly when x has two neighbors in the
    same component of F. If neither endpoint of an unsaturated edge uv
    self-blocks, adding uv creates a cycle exactly when u and v attach to a
    common component of F. This gives an efficient full check without invoking
    the block decomposition used by the solver.
    """

    matching_tuple = tuple(matching)
    if not check_acyclic_matching(graph, matching_tuple):
        return False
    saturated = {v for edge in matching_tuple for v in edge}
    forest = graph.subgraph(saturated)

    component_of: dict[Node, int] = {}
    for component_id, component in enumerate(nx.connected_components(forest)):
        for vertex in component:
            component_of[vertex] = component_id

    self_blocked: dict[Node, bool] = {}
    attachments: dict[Node, frozenset[int]] = {}
    for vertex in graph:
        if vertex in saturated:
            continue
        seen_components: set[int] = set()
        duplicate = False
        for neighbor in graph.neighbors(vertex):
            if neighbor not in saturated:
                continue
            component = component_of[neighbor]
            if component in seen_components:
                duplicate = True
            seen_components.add(component)
        self_blocked[vertex] = duplicate
        attachments[vertex] = frozenset(seen_components)

    for u, v in graph.edges():
        if u in saturated or v in saturated:
            continue
        if self_blocked[u] or self_blocked[v]:
            continue
        left, right = attachments[u], attachments[v]
        if len(left) > len(right):
            left, right = right, left
        if any(component in right for component in left):
            continue
        return False
    return True
