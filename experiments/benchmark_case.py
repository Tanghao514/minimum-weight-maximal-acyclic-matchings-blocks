#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
import resource
import sys
import time
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from generator import generate_block_tree, generate_dense_complete_graph  # noqa: E402
from mmacm import (  # noqa: E402
    check_maximal_acyclic_matching_fast,
    solve_min_weight_maximal_acyclic_matching,
)


def _weighted_cycle(order: int, seed: int):
    rng = random.Random(seed)
    graph = nx.cycle_graph(order)
    weights = {(u, v): rng.randint(-10, 20) for u, v in graph.edges()}
    vertex_costs = {v: rng.randint(-5, 8) for v in graph}
    return graph, weights, vertex_costs


def _weighted_k2n(order: int, seed: int):
    if order < 4:
        raise ValueError("single_K2n requires order >= 4")
    rng = random.Random(seed)
    graph = nx.complete_bipartite_graph(2, order - 2)
    weights = {(u, v): rng.randint(-10, 20) for u, v in graph.edges()}
    vertex_costs = {v: rng.randint(-5, 8) for v in graph}
    return graph, weights, vertex_costs


def build_instance(family: str, order: int, seed: int, mode: str):
    if family == "mixed_block_tree":
        item = generate_block_tree(order, seed=seed, family="mixed")
        graph, weights, costs = item.graph, item.edge_weights, item.vertex_costs
    elif family == "block_graph_tree":
        item = generate_block_tree(order, seed=seed, family="block_graph")
        graph, weights, costs = item.graph, item.edge_weights, item.vertex_costs
    elif family == "cactus_block_tree":
        item = generate_block_tree(order, seed=seed, family="cactus")
        graph, weights, costs = item.graph, item.edge_weights, item.vertex_costs
    elif family == "multipartite_block_tree":
        item = generate_block_tree(order, seed=seed, family="multipartite")
        graph, weights, costs = item.graph, item.edge_weights, item.vertex_costs
    elif family == "single_cycle":
        graph, weights, costs = _weighted_cycle(order, seed)
    elif family == "single_K2n":
        graph, weights, costs = _weighted_k2n(order, seed)
    elif family == "dense_complete":
        item = generate_dense_complete_graph(order, seed=seed)
        graph, weights, costs = item.graph, item.edge_weights, item.vertex_costs
    else:
        raise ValueError(f"unknown family {family!r}")

    if mode == "unweighted":
        return graph, None, None
    if mode != "weighted":
        raise ValueError(f"unknown mode {mode!r}")
    return graph, weights, costs


def matching_hash(matching) -> str:
    canonical = sorted((min(int(u), int(v)), max(int(u), int(v))) for u, v in matching)
    payload = json.dumps(canonical, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("family")
    parser.add_argument("order", type=int)
    parser.add_argument("mode", choices=("weighted", "unweighted"))
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    generation_start = time.perf_counter()
    graph, weights, vertex_costs = build_instance(args.family, args.order, args.seed, args.mode)
    generation_seconds = time.perf_counter() - generation_start

    solve_start = time.perf_counter()
    result = solve_min_weight_maximal_acyclic_matching(graph, weights, vertex_costs)
    solve_seconds = time.perf_counter() - solve_start

    verify_start = time.perf_counter()
    valid = check_maximal_acyclic_matching_fast(graph, result.matching)
    verify_seconds = time.perf_counter() - verify_start
    if not valid:
        raise AssertionError("independent fast checker rejected the reconstructed witness")

    peak_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    payload = {
        "family": args.family,
        "mode": args.mode,
        "requested_vertices": args.order,
        "vertices": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "n_plus_m": graph.number_of_nodes() + graph.number_of_edges(),
        "blocks": result.blocks,
        "components": result.components,
        "matching_size": result.cardinality,
        "cost": result.cost,
        "seed": args.seed,
        "generation_seconds": generation_seconds,
        "solve_seconds": solve_seconds,
        "verify_seconds": verify_seconds,
        "peak_rss_mib": peak_kib / 1024.0,
        "valid_witness": True,
        "matching_sha256": matching_hash(result.matching),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
