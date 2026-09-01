from __future__ import annotations

from collections import deque
from math import inf
from typing import Any, Mapping, Sequence

import networkx as nx

from .blocks import analyze_graph
from .core import (
    Block,
    ComponentAnalysis,
    Edge,
    INF,
    I,
    O,
    STATES,
    U00,
    U01,
    U10,
    U11,
    InfeasibleStateError,
    Node,
    Number,
    SolveResult,
    edge_key,
    normalize_edge_weights,
    normalize_vertex_costs,
)
from .signatures import block_signature


def _fixed_states(
    child_nodes: Sequence[tuple[str, Any]],
    messages: Mapping[tuple[str, Any], Sequence[Number | float]],
    state: int,
) -> tuple[Number | float, list[int]]:
    total: Number | float = 0
    selected: list[int] = []
    for child in child_nodes:
        value = messages[child][state]
        if value == INF:
            return INF, []
        total = total + value
        selected.append(state)
    return total, selected


def _choose_pattern(
    child_nodes: Sequence[tuple[str, Any]],
    messages: Mapping[tuple[str, Any], Sequence[Number | float]],
    special_state: int,
    base_state: int,
    threshold: int,
    exact: bool,
) -> tuple[Number | float, list[int]]:
    """Choose special/base per child with exact or at-least cardinality.

    For an exact threshold t, counts are capped at t+1 and state t is
    accepted. For an at-least threshold, counts are capped at t and state t is
    accepted. Since the only thresholds used are 1 and 2, this is linear with
    a small constant.
    """

    cap = threshold + 1 if exact else threshold
    dp: dict[int, Number | float] = {0: 0}
    predecessors: list[dict[int, tuple[int, int]]] = []
    for child in child_nodes:
        next_dp: dict[int, Number | float] = {}
        pred: dict[int, tuple[int, int]] = {}
        for count, base_cost in dp.items():
            for chosen_state, increment in ((base_state, 0), (special_state, 1)):
                state_cost = messages[child][chosen_state]
                if state_cost == INF:
                    continue
                new_count = min(cap, count + increment)
                value = base_cost + state_cost
                if value < next_dp.get(new_count, INF):
                    next_dp[new_count] = value
                    pred[new_count] = (count, chosen_state)
        dp = next_dp
        predecessors.append(pred)

    target = threshold
    best = dp.get(target, INF)
    if best == INF:
        return INF, []

    states = [base_state] * len(child_nodes)
    count = target
    for index in range(len(child_nodes) - 1, -1, -1):
        previous_count, chosen_state = predecessors[index][count]
        states[index] = chosen_state
        count = previous_count
    return best, states


def _vertex_transition(
    child_nodes: Sequence[tuple[str, Any]],
    messages: Mapping[tuple[str, Any], Sequence[Number | float]],
    vertex_cost: Number,
    parent_state: int,
) -> tuple[Number | float, list[int]]:
    if parent_state == I:
        base, states = _fixed_states(child_nodes, messages, O)
        return (INF, []) if base == INF else (base + vertex_cost, states)
    if parent_state == O:
        base, states = _choose_pattern(child_nodes, messages, I, O, 1, exact=True)
        return (INF, []) if base == INF else (base + vertex_cost, states)
    if parent_state == U00:
        return _fixed_states(child_nodes, messages, U00)
    if parent_state == U10:
        return _fixed_states(child_nodes, messages, U01)
    if parent_state == U01:
        one_cost, one_states = _choose_pattern(child_nodes, messages, U10, U01, 1, exact=True)
        two_cost, two_states = _choose_pattern(child_nodes, messages, U11, U01, 2, exact=False)
        return (one_cost, one_states) if one_cost <= two_cost else (two_cost, two_states)
    if parent_state == U11:
        return _choose_pattern(child_nodes, messages, U11, U01, 1, exact=False)
    raise ValueError(f"unknown parent state {parent_state}")


def _root_transition(
    child_nodes: Sequence[tuple[str, Any]],
    messages: Mapping[tuple[str, Any], Sequence[Number | float]],
    vertex_cost: Number,
) -> tuple[Number | float, list[int], bool]:
    sat_cost, sat_states = _choose_pattern(child_nodes, messages, I, O, 1, exact=True)
    if sat_cost != INF:
        sat_cost = sat_cost + vertex_cost

    zero_cost, zero_states = _fixed_states(child_nodes, messages, U00)
    one_cost, one_states = _choose_pattern(child_nodes, messages, U10, U01, 1, exact=True)
    two_cost, two_states = _choose_pattern(child_nodes, messages, U11, U01, 2, exact=False)

    candidates = [
        (sat_cost, sat_states, True),
        (zero_cost, zero_states, False),
        (one_cost, one_states, False),
        (two_cost, two_states, False),
    ]
    return min(candidates, key=lambda item: item[0])


def _orient_tree(
    analysis: ComponentAnalysis,
) -> tuple[
    dict[tuple[str, Any], tuple[str, Any] | None],
    list[tuple[str, Any]],
]:
    parent: dict[tuple[str, Any], tuple[str, Any] | None] = {analysis.root: None}
    order: list[tuple[str, Any]] = [analysis.root]
    for node in order:
        for neighbor in analysis.incidence[node]:
            if neighbor == parent[node]:
                continue
            if neighbor in parent:
                raise RuntimeError("incidence structure is not a tree")
            parent[neighbor] = node
            order.append(neighbor)
    return parent, order


def _solve_component(
    analysis: ComponentAnalysis,
    edge_weights: Mapping[frozenset[Node], Number],
    vertex_costs: Mapping[Node, Number],
) -> tuple[Number | float, list[Edge]]:
    if not analysis.blocks:
        return 0, []

    block_map = {block.block_id: block for block in analysis.blocks}
    parent, order = _orient_tree(analysis)
    messages: dict[tuple[str, Any], tuple[Number | float, ...]] = {}

    for node in reversed(order[1:]):
        parent_node = parent[node]
        assert parent_node is not None
        children = [x for x in analysis.incidence[node] if x != parent_node]
        if node[0] == "v":
            vertex = node[1]
            values: list[Number | float] = []
            for parent_state in range(6):
                cost, _ = _vertex_transition(
                    children, messages, vertex_costs[vertex], parent_state
                )
                values.append(cost)
            messages[node] = tuple(values)
        else:
            block = block_map[node[1]]
            if parent_node[0] != "v":
                raise RuntimeError("a block parent must be a vertex")
            parent_vertex = parent_node[1]
            child_messages = {child[1]: messages[child] for child in children}
            values: list[Number | float] = []
            for parent_state in range(6):
                result = block_signature(
                    block,
                    parent_vertex,
                    parent_state,
                    child_messages,
                    edge_weights,
                    want_witness=False,
                )
                values.append(result.cost)
            messages[node] = tuple(values)

    root = analysis.root
    root_vertex = root[1]
    root_children = list(analysis.incidence[root])
    optimum, root_states, _ = _root_transition(
        root_children, messages, vertex_costs[root_vertex]
    )
    if optimum == INF:
        raise InfeasibleStateError("no maximal acyclic matching was represented by the DP")

    matching: list[Edge] = []
    stack: list[tuple[tuple[str, Any], int | None]] = []
    for child, state in zip(root_children, root_states):
        stack.append((child, state))

    while stack:
        node, boundary_state = stack.pop()
        parent_node = parent[node]
        assert parent_node is not None
        children = [x for x in analysis.incidence[node] if x != parent_node]
        if node[0] == "v":
            if boundary_state is None:
                raise RuntimeError("a non-root vertex must have a boundary state")
            vertex = node[1]
            cost, child_states = _vertex_transition(
                children, messages, vertex_costs[vertex], boundary_state
            )
            if cost == INF:
                raise InfeasibleStateError("failed to reconstruct a vertex message")
            for child, state in zip(children, child_states):
                stack.append((child, state))
        else:
            if boundary_state is None or parent_node[0] != "v":
                raise RuntimeError("a block reconstruction needs a parent vertex state")
            block = block_map[node[1]]
            parent_vertex = parent_node[1]
            child_messages = {child[1]: messages[child] for child in children}
            local = block_signature(
                block,
                parent_vertex,
                boundary_state,
                child_messages,
                edge_weights,
                want_witness=True,
            )
            if local.cost == INF or local.states is None:
                raise InfeasibleStateError("failed to reconstruct a block signature")
            matching.extend(local.matching)
            for child in children:
                stack.append((child, local.states[child[1]]))

    return optimum, matching


def solve_min_weight_maximal_acyclic_matching(
    graph: nx.Graph,
    edge_weights: Mapping[Any, Number] | None = None,
    vertex_costs: Mapping[Node, Number] | None = None,
    *,
    default_edge_weight: Number = 1,
    verify: bool = False,
) -> SolveResult:
    """Solve minimum-weight maximal acyclic matching on the target block class.

    Parameters
    ----------
    graph:
        A finite simple undirected NetworkX graph. Every nontrivial block must
        be either a cycle or a complete multipartite graph.
    edge_weights:
        Optional mapping keyed by ``(u,v)``, ``(v,u)``, or ``frozenset({u,v})``.
    vertex_costs:
        Optional cost paid once for every saturated vertex.
    default_edge_weight:
        Weight used for edges absent from ``edge_weights``. The default 1
        yields the minimum-cardinality problem when vertex costs are zero.
    verify:
        Run the independent definition-level checker after reconstruction.
        This can be expensive on large graphs.
    """

    analyses = analyze_graph(graph)
    weights = normalize_edge_weights(graph.edges(), edge_weights, default_edge_weight)
    vcosts = normalize_vertex_costs(graph.nodes(), vertex_costs)

    total_cost: Number | float = 0
    all_matching: list[Edge] = []
    for analysis in analyses:
        component_cost, component_matching = _solve_component(analysis, weights, vcosts)
        total_cost = total_cost + component_cost
        all_matching.extend(component_matching)

    # The reconstructed matching determines its own exact cost; use it as an
    # internal consistency check and as the returned value.
    saturated = frozenset(v for edge in all_matching for v in edge)
    reconstructed_cost: Number | float = 0
    for u, v in all_matching:
        reconstructed_cost = reconstructed_cost + weights[edge_key(u, v)]
    for v in saturated:
        reconstructed_cost = reconstructed_cost + vcosts[v]
    if reconstructed_cost != total_cost:
        # For floating-point inputs, tolerate roundoff at the scale of the result.
        if not (
            isinstance(reconstructed_cost, float)
            or isinstance(total_cost, float)
        ) or abs(float(reconstructed_cost) - float(total_cost)) > 1e-9 * max(
            1.0, abs(float(reconstructed_cost)), abs(float(total_cost))
        ):
            raise RuntimeError(
                f"reconstruction cost mismatch: DP={total_cost!r}, witness={reconstructed_cost!r}"
            )

    result = SolveResult(
        cost=reconstructed_cost,
        matching=tuple(all_matching),
        saturated_vertices=saturated,
        components=len(analyses),
        blocks=sum(len(a.blocks) for a in analyses),
    )

    if verify:
        from .checker import verify_solution

        verification = verify_solution(graph, result.matching)
        if not verification.ok:
            raise RuntimeError(f"reconstructed solution failed verification: {verification.message}")
    return result
