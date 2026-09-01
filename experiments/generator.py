from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

import networkx as nx


@dataclass(frozen=True)
class GeneratedInstance:
    graph: nx.Graph
    edge_weights: dict[tuple[int, int], int]
    vertex_costs: dict[int, int]
    family: str
    seed: int


def _add_cycle(graph: nx.Graph, anchor: int, new_vertices: list[int]) -> None:
    vertices = [anchor] + new_vertices
    for i in range(len(vertices)):
        graph.add_edge(vertices[i], vertices[(i + 1) % len(vertices)])


def _add_complete_multipartite(
    graph: nx.Graph,
    anchor: int,
    new_vertices: list[int],
    part_sizes: list[int],
    anchor_part: int = 0,
) -> None:
    if sum(part_sizes) != len(new_vertices) + 1:
        raise ValueError("part sizes do not match block order")
    parts: list[list[int]] = [[] for _ in part_sizes]
    parts[anchor_part].append(anchor)
    cursor = 0
    for i, size in enumerate(part_sizes):
        need = size - (1 if i == anchor_part else 0)
        parts[i].extend(new_vertices[cursor:cursor + need])
        cursor += need
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            for u in parts[i]:
                for v in parts[j]:
                    graph.add_edge(u, v)


def generate_block_tree(
    target_vertices: int,
    *,
    seed: int = 0,
    family: str = "mixed",
    min_weight: int = -10,
    max_weight: int = 20,
    min_vertex_cost: int = -5,
    max_vertex_cost: int = 8,
) -> GeneratedInstance:
    if target_vertices < 1:
        raise ValueError("target_vertices must be positive")
    rng = random.Random(seed)
    graph = nx.Graph()
    graph.add_node(0)
    next_vertex = 1
    attachment_pool = [0]

    cycle_sizes = [3, 4, 5, 6, 7, 8, 10]
    cmp_templates = [
        [1, 1],       # bridge
        [1, 2],       # K1,2
        [1, 3],       # K1,3
        [2, 2],       # K2,2
        [2, 3],       # K2,3
        [1, 1, 1],    # K3
        [1, 1, 2],
        [1, 2, 2],
        [1, 1, 1, 1],# K4
    ]

    while next_vertex < target_vertices:
        anchor = rng.choice(attachment_pool)
        remaining_new = target_vertices - next_vertex

        choices: list[str]
        if family == "cactus":
            choices = ["cycle", "bridge"]
        elif family == "block_graph":
            choices = ["clique", "bridge"]
        elif family == "multipartite":
            choices = ["cmp", "bridge"]
        elif family == "mixed":
            choices = ["cycle", "cmp", "clique", "bridge"]
        else:
            raise ValueError(f"unknown family {family!r}")

        kind = rng.choice(choices)
        if kind == "cycle":
            feasible = [size for size in cycle_sizes if size - 1 <= remaining_new]
            if not feasible:
                kind = "bridge"
            else:
                size = rng.choice(feasible)
                new_vertices = list(range(next_vertex, next_vertex + size - 1))
                next_vertex += size - 1
                graph.add_nodes_from(new_vertices)
                _add_cycle(graph, anchor, new_vertices)
                attachment_pool.extend(new_vertices)
                continue

        if kind == "clique":
            feasible_sizes = [size for size in (3, 4, 5, 6) if size - 1 <= remaining_new]
            if not feasible_sizes:
                kind = "bridge"
            else:
                size = rng.choice(feasible_sizes)
                new_vertices = list(range(next_vertex, next_vertex + size - 1))
                next_vertex += size - 1
                graph.add_nodes_from(new_vertices)
                _add_complete_multipartite(graph, anchor, new_vertices, [1] * size)
                attachment_pool.extend(new_vertices)
                continue

        if kind == "cmp":
            feasible = [template for template in cmp_templates if sum(template) - 1 <= remaining_new]
            if not feasible:
                kind = "bridge"
            else:
                template = list(rng.choice(feasible))
                possible_anchor_parts = [i for i, size in enumerate(template) if size >= 1]
                anchor_part = rng.choice(possible_anchor_parts)
                new_count = sum(template) - 1
                new_vertices = list(range(next_vertex, next_vertex + new_count))
                next_vertex += new_count
                graph.add_nodes_from(new_vertices)
                _add_complete_multipartite(graph, anchor, new_vertices, template, anchor_part)
                attachment_pool.extend(new_vertices)
                continue

        # Bridge fallback.
        new_vertex = next_vertex
        next_vertex += 1
        graph.add_edge(anchor, new_vertex)
        attachment_pool.append(new_vertex)

    edge_weights = {
        (u, v): rng.randint(min_weight, max_weight)
        for u, v in graph.edges()
    }
    vertex_costs = {
        v: rng.randint(min_vertex_cost, max_vertex_cost)
        for v in graph.nodes()
    }
    return GeneratedInstance(graph, edge_weights, vertex_costs, family, seed)


def generate_dense_complete_graph(
    order: int,
    *,
    seed: int = 0,
    min_weight: int = -10,
    max_weight: int = 20,
) -> GeneratedInstance:
    rng = random.Random(seed)
    graph = nx.complete_graph(order)
    weights = {(u, v): rng.randint(min_weight, max_weight) for u, v in graph.edges()}
    vertex_costs = {v: 0 for v in graph}
    return GeneratedInstance(graph, weights, vertex_costs, "dense_complete", seed)
