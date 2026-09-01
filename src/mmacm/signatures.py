from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Any, Iterable, Mapping, Sequence

from .core import (
    Block,
    Edge,
    INF,
    I,
    O,
    STATES,
    STATE_INDEX,
    U00,
    U01,
    U10,
    U11,
    Node,
    Number,
    edge_key,
)


@dataclass
class LocalSignatureResult:
    cost: Number | float
    states: dict[Node, int] | None = None
    matching: tuple[Edge, ...] = tuple()
    descriptor: tuple[Any, ...] | None = None


QH = tuple((q, h) for q in range(3) for h in range(2))


def _tidx(q: int, h: int) -> int:
    return 2 * q + h


def _combine_tables(a: Sequence[Number | float], b: Sequence[Number | float]) -> list[Number | float]:
    out: list[Number | float] = [INF] * 6
    for q1, h1 in QH:
        x = a[_tidx(q1, h1)]
        if x == INF:
            continue
        for q2, h2 in QH:
            y = b[_tidx(q2, h2)]
            if y == INF:
                continue
            q = min(2, q1 + q2)
            h = h1 | h2
            value = x + y
            idx = _tidx(q, h)
            if value < out[idx]:
                out[idx] = value
    return out


def _identity_table() -> list[Number | float]:
    table: list[Number | float] = [INF] * 6
    table[_tidx(0, 0)] = 0
    return table


def _atom_table(cost: Sequence[Number | float], a_bit: int) -> list[Number | float]:
    table: list[Number | float] = [INF] * 6
    table[_tidx(1, 0)] = cost[O]
    table[_tidx(0, 1)] = cost[STATE_INDEX[f"U{a_bit}0"]]
    table[_tidx(0, 0)] = cost[STATE_INDEX[f"U{a_bit}1"]]
    return table


def _table_min(
    table: Sequence[Number | float],
    q_values: Iterable[int],
    h_values: Iterable[int] = (0, 1),
) -> Number | float:
    return min(table[_tidx(q, h)] for q in q_values for h in h_values)


@dataclass(frozen=True)
class _FiniteAggregate:
    finite_sum: Number | float
    infinite_count: int
    values: tuple[Number | float, ...]

    @classmethod
    def build(cls, values: Sequence[Number | float]) -> "_FiniteAggregate":
        finite_sum: Number | float = 0
        infinite_count = 0
        for value in values:
            if value == INF:
                infinite_count += 1
            else:
                finite_sum = finite_sum + value
        return cls(finite_sum, infinite_count, tuple(values))

    def excluding(self, indices: Iterable[int]) -> Number | float:
        unique = set(indices)
        finite_sum = self.finite_sum
        infinite_count = self.infinite_count
        for idx in unique:
            value = self.values[idx]
            if value == INF:
                infinite_count -= 1
            else:
                finite_sum = finite_sum - value
        return INF if infinite_count else finite_sum


def _part_summaries(
    parts: Sequence[Sequence[Node]],
    costs: Mapping[Node, Sequence[Number | float]],
) -> tuple[
    dict[tuple[int, int], list[Number | float]],
    dict[tuple[int, int, Node], list[Number | float]],
]:
    full: dict[tuple[int, int], list[Number | float]] = {}
    leave_one_out: dict[tuple[int, int, Node], list[Number | float]] = {}
    ident = _identity_table()

    for part_index, part in enumerate(parts):
        for a_bit in (0, 1):
            atoms = [_atom_table(costs[v], a_bit) for v in part]
            prefix: list[list[Number | float]] = [ident]
            for atom in atoms:
                prefix.append(_combine_tables(prefix[-1], atom))
            suffix: list[list[Number | float]] = [ident for _ in range(len(part) + 1)]
            suffix[len(part)] = ident
            for j in range(len(part) - 1, -1, -1):
                suffix[j] = _combine_tables(atoms[j], suffix[j + 1])
            full[(part_index, a_bit)] = prefix[-1]
            for j, vertex in enumerate(part):
                leave_one_out[(part_index, a_bit, vertex)] = _combine_tables(prefix[j], suffix[j + 1])
    return full, leave_one_out


def _best_candidate(
    current_cost: Number | float,
    current_desc: tuple[Any, ...] | None,
    value: Number | float,
    desc: tuple[Any, ...],
) -> tuple[Number | float, tuple[Any, ...] | None]:
    if value < current_cost:
        return value, desc
    return current_cost, current_desc


def _part_assignment(
    part: Sequence[Node],
    a_bit: int,
    costs: Mapping[Node, Sequence[Number | float]],
    q_allowed: set[int],
    h_allowed: set[int] = {0, 1},
    excluded: set[Node] | None = None,
) -> tuple[Number | float, dict[Node, int]]:
    excluded = excluded or set()
    vertices = [v for v in part if v not in excluded]
    # Each layer maps (q,h) to cost. Backpointers store (previous label, chosen state).
    layers: list[dict[tuple[int, int], Number | float]] = [{(0, 0): 0}]
    preds: list[dict[tuple[int, int], tuple[tuple[int, int], int]]] = []
    options = (O, STATE_INDEX[f"U{a_bit}0"], STATE_INDEX[f"U{a_bit}1"])

    for vertex in vertices:
        previous = layers[-1]
        current: dict[tuple[int, int], Number | float] = {}
        pred: dict[tuple[int, int], tuple[tuple[int, int], int]] = {}
        for (q, h), base in previous.items():
            for state in options:
                state_cost = costs[vertex][state]
                if state_cost == INF:
                    continue
                if state == O:
                    nq, nh = min(2, q + 1), h
                elif state == STATE_INDEX[f"U{a_bit}0"]:
                    nq, nh = q, 1
                else:
                    nq, nh = q, h
                value = base + state_cost
                label = (nq, nh)
                if value < current.get(label, INF):
                    current[label] = value
                    pred[label] = ((q, h), state)
        layers.append(current)
        preds.append(pred)

    best_label: tuple[int, int] | None = None
    best = INF
    for q in q_allowed:
        for h in h_allowed:
            value = layers[-1].get((q, h), INF)
            if value < best:
                best = value
                best_label = (q, h)
    if best_label is None:
        return INF, {}

    assignment: dict[Node, int] = {}
    label = best_label
    for index in range(len(vertices) - 1, -1, -1):
        previous_label, state = preds[index][label]
        assignment[vertices[index]] = state
        label = previous_label
    return best, assignment


def complete_multipartite_signature(
    block: Block,
    parent: Node,
    parent_state: int,
    child_messages: Mapping[Node, Sequence[Number | float]],
    edge_weights: Mapping[frozenset[Node], Number],
    want_witness: bool = False,
) -> LocalSignatureResult:
    assert block.parts is not None
    parts = block.parts
    part_of = {v: i for i, part in enumerate(parts) for v in part}

    costs: dict[Node, tuple[Number | float, ...]] = {}
    for v in block.vertices:
        if v == parent:
            costs[v] = tuple(0 if state == parent_state else INF for state in range(6))
        else:
            costs[v] = tuple(child_messages[v])

    full, loo = _part_summaries(parts, costs)
    r = len(parts)

    z0_any = [_table_min(full[(i, 0)], (0,)) for i in range(r)]
    z0_h0 = [full[(i, 0)][_tidx(0, 0)] for i in range(r)]
    z1_any = [_table_min(full[(i, 1)], (0,)) for i in range(r)]
    agg_z0_any = _FiniteAggregate.build(z0_any)
    agg_z0_h0 = _FiniteAggregate.build(z0_h0)
    agg_z1_any = _FiniteAggregate.build(z1_any)

    best: Number | float = INF
    descriptor: tuple[Any, ...] | None = None

    # Type A0: no U00 anywhere.
    value = agg_z0_h0.excluding(())
    best, descriptor = _best_candidate(best, descriptor, value, ("A0",))
    # Type A1: exactly one part contains at least one U00.
    for i in range(r):
        value = full[(i, 0)][_tidx(0, 1)]
        outside = agg_z0_h0.excluding((i,))
        value = INF if value == INF or outside == INF else value + outside
        best, descriptor = _best_candidate(best, descriptor, value, ("A1", i))

    # Type B: exactly one occupied part.
    for i in range(r):
        occupied_h0 = _table_min(full[(i, 0)], (1, 2), (0,))
        outside_any = agg_z0_any.excluding((i,))
        value = INF if occupied_h0 == INF or outside_any == INF else occupied_h0 + outside_any
        best, descriptor = _best_candidate(best, descriptor, value, ("B_IN", i))

        occupied_any = _table_min(full[(i, 0)], (1, 2))
        outside_h0 = agg_z0_h0.excluding((i,))
        value = INF if occupied_any == INF or outside_h0 == INF else occupied_any + outside_h0
        best, descriptor = _best_candidate(best, descriptor, value, ("B_OUT", i))

    # Type C without an internal edge.
    for i in range(r):
        left = _table_min(full[(i, 0)], (1,))
        for j in range(i + 1, r):
            right = _table_min(full[(j, 0)], (1,))
            outside = agg_z1_any.excluding((i, j))
            value = INF if left == INF or right == INF or outside == INF else left + right + outside
            best, descriptor = _best_candidate(best, descriptor, value, ("C_OO", i, j))

    # Type D without an internal edge: i singleton, j large.
    for i in range(r):
        singleton = _table_min(full[(i, 1)], (1,))
        for j in range(r):
            if i == j:
                continue
            large = _table_min(full[(j, 0)], (2,))
            outside = agg_z1_any.excluding((i, j))
            value = INF if singleton == INF or large == INF or outside == INF else singleton + large + outside
            best, descriptor = _best_candidate(best, descriptor, value, ("D_OO", i, j))

    # Types C and D with the unique internal edge.
    for u, v in block.edges:
        i, j = part_of[u], part_of[v]
        if i == j:
            raise RuntimeError("an edge inside one multipartite part was detected")
        endpoint_cost = costs[u][I]
        if endpoint_cost != INF:
            endpoint_cost = endpoint_cost + costs[v][I]
        if endpoint_cost != INF:
            endpoint_cost = endpoint_cost + edge_weights[edge_key(u, v)]

        outside = agg_z1_any.excluding((i, j))
        ci = _table_min(loo[(i, 0, u)], (0,))
        cj = _table_min(loo[(j, 0, v)], (0,))
        value = INF if endpoint_cost == INF or outside == INF or ci == INF or cj == INF else endpoint_cost + outside + ci + cj
        best, descriptor = _best_candidate(best, descriptor, value, ("C_II", u, v, i, j))

        # i is singleton, j is large.
        si = _table_min(loo[(i, 1, u)], (0,))
        lj = _table_min(loo[(j, 0, v)], (1, 2))
        value = INF if endpoint_cost == INF or outside == INF or si == INF or lj == INF else endpoint_cost + outside + si + lj
        best, descriptor = _best_candidate(best, descriptor, value, ("D_II", u, v, i, j))

        # j is singleton, i is large.
        sj = _table_min(loo[(j, 1, v)], (0,))
        li = _table_min(loo[(i, 0, u)], (1, 2))
        value = INF if endpoint_cost == INF or outside == INF or sj == INF or li == INF else endpoint_cost + outside + sj + li
        best, descriptor = _best_candidate(best, descriptor, value, ("D_II", v, u, j, i))

    if not want_witness or descriptor is None or best == INF:
        return LocalSignatureResult(cost=best, descriptor=descriptor)

    assignment: dict[Node, int] = {}
    matching: list[Edge] = []

    def assign_part(
        index: int,
        a_bit: int,
        q_allowed: set[int],
        h_allowed: set[int] = {0, 1},
        excluded: set[Node] | None = None,
    ) -> None:
        value, local_assignment = _part_assignment(
            parts[index], a_bit, costs, q_allowed, h_allowed, excluded
        )
        if value == INF:
            raise RuntimeError(f"failed to reconstruct part {index} for descriptor {descriptor!r}")
        assignment.update(local_assignment)

    tag = descriptor[0]
    if tag == "A0":
        for i in range(r):
            assign_part(i, 0, {0}, {0})
    elif tag == "A1":
        exceptional = descriptor[1]
        for i in range(r):
            assign_part(i, 0, {0}, {1} if i == exceptional else {0})
    elif tag == "B_IN":
        occupied = descriptor[1]
        for i in range(r):
            assign_part(i, 0, {1, 2} if i == occupied else {0}, {0} if i == occupied else {0, 1})
    elif tag == "B_OUT":
        occupied = descriptor[1]
        for i in range(r):
            assign_part(i, 0, {1, 2} if i == occupied else {0}, {0, 1} if i == occupied else {0})
    elif tag == "C_OO":
        i, j = descriptor[1], descriptor[2]
        for k in range(r):
            if k in (i, j):
                assign_part(k, 0, {1})
            else:
                assign_part(k, 1, {0})
    elif tag == "D_OO":
        singleton, large = descriptor[1], descriptor[2]
        for k in range(r):
            if k == singleton:
                assign_part(k, 1, {1})
            elif k == large:
                assign_part(k, 0, {2})
            else:
                assign_part(k, 1, {0})
    elif tag == "C_II":
        u, v, i, j = descriptor[1:5]
        assignment[u] = I
        assignment[v] = I
        matching.append((u, v))
        for k in range(r):
            if k == i:
                assign_part(k, 0, {0}, excluded={u})
            elif k == j:
                assign_part(k, 0, {0}, excluded={v})
            else:
                assign_part(k, 1, {0})
    elif tag == "D_II":
        u, v, singleton, large = descriptor[1:5]
        assignment[u] = I
        assignment[v] = I
        matching.append((u, v))
        for k in range(r):
            if k == singleton:
                assign_part(k, 1, {0}, excluded={u})
            elif k == large:
                assign_part(k, 0, {1, 2}, excluded={v})
            else:
                assign_part(k, 1, {0})
    else:
        raise RuntimeError(f"unknown multipartite descriptor {descriptor!r}")

    if set(assignment) != set(block.vertices):
        missing = set(block.vertices) - set(assignment)
        raise RuntimeError(f"incomplete local reconstruction; missing {missing!r}")
    return LocalSignatureResult(best, assignment, tuple(matching), descriptor)


def _cycle_key(px: int, zcap: int, prev_u00: int) -> int:
    return (px << 3) | (zcap << 1) | prev_u00


def _decode_cycle_key(key: int) -> tuple[int, int, int]:
    return (key >> 3) & 1, (key >> 1) & 3, key & 1


def cycle_signature(
    block: Block,
    parent: Node,
    parent_state: int,
    child_messages: Mapping[Node, Sequence[Number | float]],
    edge_weights: Mapping[frozenset[Node], Number],
    want_witness: bool = False,
) -> LocalSignatureResult:
    assert block.cycle_order is not None
    order = block.cycle_order
    n = len(order)
    costs: dict[Node, tuple[Number | float, ...]] = {}
    for v in order:
        if v == parent:
            costs[v] = tuple(0 if state == parent_state else INF for state in range(6))
        else:
            costs[v] = tuple(child_messages[v])
    edge_costs = [edge_weights[edge_key(order[i], order[(i + 1) % n])] for i in range(n)]

    modes = (1, 2, 3)  # 3 means at least three unsaturated vertices.
    best: Number | float = INF
    best_desc: tuple[Any, ...] | None = None

    def allowed_states(mode: int) -> tuple[int, ...]:
        return (I, O, U10, U11) if mode == 1 else (I, O, U00, U01)

    # First pass: compute values and retain only a constant-size winning descriptor.
    for mode in modes:
        allowed = allowed_states(mode)
        for closing in (0, 1):
            for s0 in allowed:
                for x0 in (0, 1):
                    if closing + x0 != (1 if s0 == I else 0):
                        continue
                    c0 = costs[order[0]][s0]
                    if c0 == INF:
                        continue
                    z0 = 1 if s0 >= U00 else 0
                    first_u00 = 1 if s0 == U00 else 0
                    initial_key = _cycle_key(x0, min(3, z0), first_u00)
                    dp: dict[int, Number | float] = {
                        initial_key: c0 + closing * edge_costs[-1] + x0 * edge_costs[0]
                    }
                    for i in range(1, n - 1):
                        next_dp: dict[int, Number | float] = {}
                        for key, base in dp.items():
                            previous_x, zcap, previous_u00 = _decode_cycle_key(key)
                            for state in allowed:
                                state_cost = costs[order[i]][state]
                                if state_cost == INF:
                                    continue
                                current_u00 = 1 if state == U00 else 0
                                if mode == 3 and previous_u00 and current_u00:
                                    continue
                                for current_x in (0, 1):
                                    if previous_x + current_x != (1 if state == I else 0):
                                        continue
                                    new_z = min(3, zcap + (1 if state >= U00 else 0))
                                    new_key = _cycle_key(current_x, new_z, current_u00)
                                    value = base + state_cost + current_x * edge_costs[i]
                                    if value < next_dp.get(new_key, INF):
                                        next_dp[new_key] = value
                        dp = next_dp
                    for key, base in dp.items():
                        previous_x, zcap, previous_u00 = _decode_cycle_key(key)
                        for last_state in allowed:
                            if previous_x + closing != (1 if last_state == I else 0):
                                continue
                            state_cost = costs[order[-1]][last_state]
                            if state_cost == INF:
                                continue
                            last_u00 = 1 if last_state == U00 else 0
                            if mode == 3 and (previous_u00 and last_u00 or last_u00 and first_u00):
                                continue
                            zfinal = min(3, zcap + (1 if last_state >= U00 else 0))
                            if zfinal != mode:
                                continue
                            value = base + state_cost
                            if value < best:
                                best = value
                                best_desc = (mode, closing, s0, x0, key, last_state)

    if not want_witness or best_desc is None or best == INF:
        return LocalSignatureResult(best, descriptor=best_desc)

    mode, closing, s0, x0, _, _ = best_desc
    allowed = allowed_states(mode)
    first_u00 = 1 if s0 == U00 else 0
    z0 = 1 if s0 >= U00 else 0
    initial_key = _cycle_key(x0, min(3, z0), first_u00)
    dp: dict[int, Number | float] = {
        initial_key: costs[order[0]][s0] + closing * edge_costs[-1] + x0 * edge_costs[0]
    }
    pred_keys: list[bytearray | None] = [None] * n
    pred_states: list[bytearray | None] = [None] * n
    for i in range(1, n - 1):
        next_dp: dict[int, Number | float] = {}
        pk = bytearray([255] * 16)
        ps = bytearray([255] * 16)
        for key, base in dp.items():
            previous_x, zcap, previous_u00 = _decode_cycle_key(key)
            for state in allowed:
                state_cost = costs[order[i]][state]
                if state_cost == INF:
                    continue
                current_u00 = 1 if state == U00 else 0
                if mode == 3 and previous_u00 and current_u00:
                    continue
                for current_x in (0, 1):
                    if previous_x + current_x != (1 if state == I else 0):
                        continue
                    new_z = min(3, zcap + (1 if state >= U00 else 0))
                    new_key = _cycle_key(current_x, new_z, current_u00)
                    value = base + state_cost + current_x * edge_costs[i]
                    if value < next_dp.get(new_key, INF):
                        next_dp[new_key] = value
                        pk[new_key] = key
                        ps[new_key] = state
        dp = next_dp
        pred_keys[i] = pk
        pred_states[i] = ps

    final_key: int | None = None
    final_state: int | None = None
    final_value: Number | float = INF
    for key, base in dp.items():
        previous_x, zcap, previous_u00 = _decode_cycle_key(key)
        for state in allowed:
            if previous_x + closing != (1 if state == I else 0):
                continue
            state_cost = costs[order[-1]][state]
            if state_cost == INF:
                continue
            last_u00 = 1 if state == U00 else 0
            if mode == 3 and (previous_u00 and last_u00 or last_u00 and first_u00):
                continue
            zfinal = min(3, zcap + (1 if state >= U00 else 0))
            if zfinal != mode:
                continue
            value = base + state_cost
            if value < final_value:
                final_value = value
                final_key = key
                final_state = state
    if final_key is None or final_state is None:
        raise RuntimeError("cycle reconstruction failed")

    states: dict[Node, int] = {order[0]: s0, order[-1]: final_state}
    matching: list[Edge] = []
    if closing:
        matching.append((order[-1], order[0]))
    if x0:
        matching.append((order[0], order[1]))

    current_key = final_key
    for i in range(n - 2, 0, -1):
        state_table = pred_states[i]
        key_table = pred_keys[i]
        if state_table is None or key_table is None:
            raise RuntimeError("missing cycle predecessor table")
        state = state_table[current_key]
        previous_key = key_table[current_key]
        if state == 255 or previous_key == 255:
            raise RuntimeError("invalid cycle predecessor")
        states[order[i]] = int(state)
        current_x, _, _ = _decode_cycle_key(current_key)
        if current_x:
            matching.append((order[i], order[i + 1]))
        current_key = int(previous_key)

    if set(states) != set(order):
        raise RuntimeError("incomplete cycle state reconstruction")
    return LocalSignatureResult(best, states, tuple(matching), best_desc)


def block_signature(
    block: Block,
    parent: Node,
    parent_state: int,
    child_messages: Mapping[Node, Sequence[Number | float]],
    edge_weights: Mapping[frozenset[Node], Number],
    want_witness: bool = False,
) -> LocalSignatureResult:
    if block.kind == "cycle":
        return cycle_signature(
            block, parent, parent_state, child_messages, edge_weights, want_witness
        )
    if block.kind == "complete_multipartite":
        return complete_multipartite_signature(
            block, parent, parent_state, child_messages, edge_weights, want_witness
        )
    raise ValueError(f"unknown block kind {block.kind!r}")
