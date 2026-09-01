from __future__ import annotations

from dataclasses import dataclass
from math import inf, isfinite, isnan
from numbers import Real
from typing import Any, Hashable, Iterable, Mapping, Sequence

Node = Hashable
Edge = tuple[Node, Node]
Number = int | float

STATES: tuple[str, ...] = ("I", "O", "U00", "U01", "U10", "U11")
STATE_INDEX: dict[str, int] = {state: i for i, state in enumerate(STATES)}
I, O, U00, U01, U10, U11 = range(6)
INF = inf


def edge_key(u: Node, v: Node) -> frozenset[Node]:
    if u == v:
        raise ValueError("self-loops are not supported")
    return frozenset((u, v))


def normalize_edge_weights(
    edges: Iterable[Edge],
    weights: Mapping[Any, Number] | None,
    default: Number = 1,
) -> dict[frozenset[Node], Number]:
    result: dict[frozenset[Node], Number] = {}
    for u, v in edges:
        key = edge_key(u, v)
        value: Number = default
        if weights is not None:
            if key in weights:
                value = weights[key]
            elif (u, v) in weights:
                value = weights[(u, v)]
            elif (v, u) in weights:
                value = weights[(v, u)]
            else:
                value = default
        if isinstance(value, float) and isnan(value):
            raise ValueError(f"NaN edge weight on {(u, v)!r}")
        result[key] = value
    return result


def normalize_vertex_costs(
    nodes: Iterable[Node],
    costs: Mapping[Node, Number] | None,
) -> dict[Node, Number]:
    result: dict[Node, Number] = {}
    for node in nodes:
        value: Number = 0 if costs is None else costs.get(node, 0)
        if isinstance(value, float) and isnan(value):
            raise ValueError(f"NaN vertex cost on {node!r}")
        result[node] = value
    return result


def add_costs(*values: Number | float) -> Number | float:
    total: Number | float = 0
    for value in values:
        if value == INF:
            return INF
        total = total + value
    return total


@dataclass(frozen=True)
class Block:
    block_id: int
    vertices: tuple[Node, ...]
    edges: tuple[Edge, ...]
    kind: str  # "cycle" or "complete_multipartite"
    cycle_order: tuple[Node, ...] | None = None
    parts: tuple[tuple[Node, ...], ...] | None = None


@dataclass(frozen=True)
class ComponentAnalysis:
    vertices: tuple[Node, ...]
    blocks: tuple[Block, ...]
    incidence: dict[tuple[str, Any], tuple[tuple[str, Any], ...]]
    root: tuple[str, Any]


@dataclass
class SolveResult:
    cost: Number | float
    matching: tuple[Edge, ...]
    saturated_vertices: frozenset[Node]
    components: int
    blocks: int
    arithmetic_model: str = (
        "O(n+m) arithmetic/comparison operations; ordinary O(n+m) word-RAM "
        "time when weights and intermediate values occupy O(1) machine words"
    )

    @property
    def cardinality(self) -> int:
        return len(self.matching)


class UnsupportedBlockError(ValueError):
    """Raised when a block is neither a cycle nor complete multipartite."""


class InfeasibleStateError(RuntimeError):
    """Raised when reconstruction encounters an infinite DP state."""
