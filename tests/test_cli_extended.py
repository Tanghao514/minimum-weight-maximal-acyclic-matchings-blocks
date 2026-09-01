from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import networkx as nx


def _run(*args: str, cwd: Path) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "mmacm", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_json_cli_and_numeric_vertex_cost_mapping(tmp_path: Path) -> None:
    payload = {
        "nodes": [0, 1, 2, 3],
        "edges": [
            {"u": 0, "v": 1, "weight": -3},
            {"u": 1, "v": 2, "weight": 2},
            {"u": 2, "v": 3, "weight": 4},
            {"u": 3, "v": 0, "weight": 1},
        ],
        "vertex_costs": {"0": 1, "1": -2, "2": 0, "3": 0},
    }
    source = tmp_path / "graph.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    out = _run("--json", str(source), "--verify", cwd=tmp_path)
    assert out["cardinality"] >= 1
    assert isinstance(out["matching"], list)


def test_graph6_cost_keys_are_resolved(tmp_path: Path) -> None:
    g6 = nx.to_graph6_bytes(nx.path_graph(4), header=False).decode().strip()
    costs = tmp_path / "costs.json"
    costs.write_text(json.dumps({"0": -5, "1": 2}), encoding="utf-8")
    out = _run("--graph6", g6, "--vertex-costs", str(costs), "--verify", cwd=tmp_path)
    assert "cost" in out
