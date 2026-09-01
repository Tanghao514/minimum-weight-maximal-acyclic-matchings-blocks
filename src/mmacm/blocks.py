from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Hashable, Iterable

import networkx as nx

from .core import Block, ComponentAnalysis, Node, UnsupportedBlockError


def _cycle_order(vertices: tuple[Node, ...], adjacency: dict[Node, set[Node]]) -> tuple[Node, ...]:
    if len(vertices) < 3:
        raise ValueError("a cycle block must have at least three vertices")
    start = vertices[0]
    neighbors = list(adjacency[start])
    if len(neighbors) != 2:
        raise ValueError("not a cycle")
    order = [start]
    previous: Node | None = None
    current = start
    next_vertex = neighbors[0]
    while len(order) < len(vertices):
        previous, current = current, next_vertex
        order.append(current)
        candidates = [x for x in adjacency[current] if x != previous]
        if len(candidates) != 1:
            raise ValueError("not a simple cycle")
        next_vertex = candidates[0]
    if next_vertex != start:
        raise ValueError("cycle order does not close")
    return tuple(order)


def _complete_multipartite_parts(
    vertices: tuple[Node, ...],
    adjacency: dict[Node, set[Node]],
) -> tuple[tuple[Node, ...], ...] | None:
    """Recognize a complete multipartite graph and recover its parts.

    The implementation follows the proof: for a representative x, its
    non-neighbors in the current remainder must be exactly its part. Each
    vertex is verified once when its part is removed. The scans of the
    remainder are chargeable to vertices plus cross-part edges on accepted
    inputs, yielding O(|V|+|E|) work in the promised class.
    """

    remaining_order = list(vertices)
    remaining = set(vertices)
    parts: list[tuple[Node, ...]] = []

    while remaining:
        x = next(v for v in remaining_order if v in remaining)
        part = tuple(v for v in remaining_order if v in remaining and (v == x or v not in adjacency[x]))
        part_set = set(part)
        outside = remaining - part_set
        expected = len(outside)

        for y in part:
            count_inside_remainder = 0
            for z in adjacency[y]:
                if z in remaining:
                    count_inside_remainder += 1
                    if z in part_set:
                        return None
            if count_inside_remainder != expected:
                return None

        parts.append(part)
        remaining.difference_update(part_set)

    if len(parts) < 2:
        return None
    return tuple(parts)


def classify_block(
    graph: nx.Graph,
    block_id: int,
    edge_list: Iterable[tuple[Node, Node]],
) -> Block:
    edges = tuple((u, v) for u, v in edge_list)
    vertices_list: list[Node] = []
    seen: set[Node] = set()
    adjacency: dict[Node, set[Node]] = defaultdict(set)
    for u, v in edges:
        if u not in seen:
            seen.add(u)
            vertices_list.append(u)
        if v not in seen:
            seen.add(v)
            vertices_list.append(v)
        adjacency[u].add(v)
        adjacency[v].add(u)
    vertices = tuple(vertices_list)

    if len(vertices) >= 3 and len(edges) == len(vertices) and all(len(adjacency[v]) == 2 for v in vertices):
        order = _cycle_order(vertices, adjacency)
        return Block(
            block_id=block_id,
            vertices=vertices,
            edges=edges,
            kind="cycle",
            cycle_order=order,
            parts=None,
        )

    parts = _complete_multipartite_parts(vertices, adjacency)
    if parts is None:
        raise UnsupportedBlockError(
            f"block {block_id} on {len(vertices)} vertices and {len(edges)} edges "
            "is neither a cycle nor a complete multipartite graph"
        )
    return Block(
        block_id=block_id,
        vertices=vertices,
        edges=edges,
        kind="complete_multipartite",
        cycle_order=None,
        parts=parts,
    )


def analyze_component(graph: nx.Graph, vertices: set[Node], start_block_id: int = 0) -> ComponentAnalysis:
    subgraph = graph.subgraph(vertices)
    if subgraph.number_of_edges() == 0:
        root_vertex = next(iter(vertices))
        root = ("v", root_vertex)
        return ComponentAnalysis(
            vertices=tuple(vertices),
            blocks=tuple(),
            incidence={root: tuple()},
            root=root,
        )

    block_edges = list(nx.biconnected_component_edges(subgraph))
    blocks: list[Block] = []
    incidence_mut: dict[tuple[str, Any], list[tuple[str, Any]]] = defaultdict(list)
    for v in vertices:
        incidence_mut[("v", v)]

    for local_id, edges in enumerate(block_edges):
        block = classify_block(graph, start_block_id + local_id, edges)
        blocks.append(block)
        block_node = ("b", block.block_id)
        incidence_mut[block_node]
        for v in block.vertices:
            vertex_node = ("v", v)
            incidence_mut[block_node].append(vertex_node)
            incidence_mut[vertex_node].append(block_node)

    root_vertex = next(iter(vertices))
    root = ("v", root_vertex)

    # Validate that the extended incidence graph is a tree.
    parent: dict[tuple[str, Any], tuple[str, Any] | None] = {root: None}
    queue = deque([root])
    while queue:
        x = queue.popleft()
        for y in incidence_mut[x]:
            if y == parent[x]:
                continue
            if y in parent:
                raise RuntimeError("block-vertex incidence graph is not a tree")
            parent[y] = x
            queue.append(y)
    if len(parent) != len(incidence_mut):
        raise RuntimeError("block-vertex incidence graph is disconnected")

    incidence = {node: tuple(neighbors) for node, neighbors in incidence_mut.items()}
    return ComponentAnalysis(
        vertices=tuple(vertices),
        blocks=tuple(blocks),
        incidence=incidence,
        root=root,
    )


def analyze_graph(graph: nx.Graph) -> tuple[ComponentAnalysis, ...]:
    if graph.is_directed():
        raise ValueError("the solver accepts only undirected graphs")
    if graph.is_multigraph():
        raise ValueError("the solver accepts only simple graphs")
    if nx.number_of_selfloops(graph):
        raise ValueError("self-loops are not supported")

    analyses: list[ComponentAnalysis] = []
    next_block_id = 0
    for component_vertices in nx.connected_components(graph):
        analysis = analyze_component(graph, set(component_vertices), next_block_id)
        analyses.append(analysis)
        next_block_id += len(analysis.blocks)
    return tuple(analyses)
