from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import networkx as nx

from .solver import solve_min_weight_maximal_acyclic_matching


def _parse_number(token: str) -> int | float:
    """Parse an exact integer when possible, otherwise a finite float."""
    try:
        return int(token)
    except ValueError:
        value = float(token)
        if not (float("-inf") < value < float("inf")):
            raise ValueError(f"non-finite numeric value {token!r} is not supported")
        return value


def _read_edge_list(path: Path) -> tuple[nx.Graph, dict[tuple[str, str], int | float]]:
    graph = nx.Graph()
    weights: dict[tuple[str, str], int | float] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) not in (2, 3):
            raise ValueError(f"{path}:{line_number}: expected 'u v [weight]'")
        u, v = fields[0], fields[1]
        if u == v:
            raise ValueError(f"{path}:{line_number}: self-loop {u!r} is not supported")
        weight = 1 if len(fields) == 2 else _parse_number(fields[2])
        if graph.has_edge(u, v):
            raise ValueError(f"{path}:{line_number}: duplicate edge {u!r} {v!r}")
        graph.add_edge(u, v)
        weights[(u, v)] = weight
    return graph, weights


def _read_json_graph(path: Path) -> tuple[nx.Graph, dict[tuple[Any, Any], int | float], dict[Any, int | float]]:
    """Read the portable JSON format documented in README.md."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JSON graph input must be an object")

    graph = nx.Graph()
    nodes = payload.get("nodes", [])
    if not isinstance(nodes, list):
        raise ValueError("'nodes' must be a list when present")
    graph.add_nodes_from(nodes)

    edge_weights: dict[tuple[Any, Any], int | float] = {}
    edges = payload.get("edges", [])
    if not isinstance(edges, list):
        raise ValueError("'edges' must be a list")
    for index, item in enumerate(edges):
        if isinstance(item, list):
            if len(item) not in (2, 3):
                raise ValueError(f"edge #{index}: expected [u,v] or [u,v,weight]")
            u, v = item[0], item[1]
            weight = 1 if len(item) == 2 else item[2]
        elif isinstance(item, dict):
            try:
                u, v = item["u"], item["v"]
            except KeyError as exc:
                raise ValueError(f"edge #{index}: object must contain 'u' and 'v'") from exc
            weight = item.get("weight", 1)
        else:
            raise ValueError(f"edge #{index}: expected a list or object")
        if u == v:
            raise ValueError(f"edge #{index}: self-loop is not supported")
        if graph.has_edge(u, v):
            raise ValueError(f"edge #{index}: duplicate edge {(u, v)!r}")
        graph.add_edge(u, v)
        edge_weights[(u, v)] = weight

    raw_costs = payload.get("vertex_costs", {})
    if not isinstance(raw_costs, dict):
        raise ValueError("'vertex_costs' must be a JSON object")
    vertex_costs: dict[Any, int | float] = {}
    by_text = {str(node): node for node in graph.nodes()}
    for key, value in raw_costs.items():
        node = key if key in graph else by_text.get(str(key))
        if node is None:
            raise ValueError(f"vertex-cost key {key!r} does not identify a graph vertex")
        vertex_costs[node] = value
    return graph, edge_weights, vertex_costs


def _read_vertex_costs(path: Path, graph: nx.Graph) -> dict[Any, int | float]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("vertex-cost file must contain a JSON object")
    by_text = {str(node): node for node in graph.nodes()}
    result: dict[Any, int | float] = {}
    for key, value in raw.items():
        node = key if key in graph else by_text.get(str(key))
        if node is None:
            raise ValueError(f"vertex-cost key {key!r} does not identify a graph vertex")
        result[node] = value
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Minimum-weight maximal acyclic matching for graphs whose blocks "
            "are cycles or complete multipartite graphs"
        )
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--edge-list", type=Path, help="text file: u v [weight]")
    group.add_argument("--graph6", help="a single graph6 string (unit edge weights)")
    group.add_argument("--json", type=Path, help="portable JSON graph input")
    parser.add_argument("--vertex-costs", type=Path, help="JSON object mapping node labels to costs")
    parser.add_argument("--verify", action="store_true", help="run the definition-level checker")
    parser.add_argument("--output", type=Path, help="write JSON output to this file")
    args = parser.parse_args()

    if args.edge_list is not None:
        graph, weights = _read_edge_list(args.edge_list)
        vertex_costs = None
    elif args.graph6 is not None:
        graph = nx.from_graph6_bytes(args.graph6.encode("ascii"))
        weights = None
        vertex_costs = None
    else:
        graph, weights, vertex_costs = _read_json_graph(args.json)

    if args.vertex_costs is not None:
        supplied = _read_vertex_costs(args.vertex_costs, graph)
        vertex_costs = {**(vertex_costs or {}), **supplied}

    result = solve_min_weight_maximal_acyclic_matching(
        graph,
        weights,
        vertex_costs,
        verify=args.verify,
    )
    payload = {
        "cost": result.cost,
        "cardinality": result.cardinality,
        "matching": [list(edge) for edge in result.matching],
        "saturated_vertices": list(result.saturated_vertices),
        "components": result.components,
        "blocks": result.blocks,
        "arithmetic_model": result.arithmetic_model,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
