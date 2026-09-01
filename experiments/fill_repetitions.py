#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
from run_scaling import cases  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=3)
    args = parser.parse_args()

    raw_path = ROOT / "experiments" / "results" / "scaling_raw.jsonl"
    rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = Counter(int(row["case_index"]) for row in rows)
    script = ROOT / "experiments" / "benchmark_case.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

    for case_index, family, order, mode, seed in cases():
        while counts[case_index] < args.target:
            repetition = counts[case_index] + 1
            completed = subprocess.run(
                [sys.executable, str(script), family, str(order), mode, "--seed", str(seed)],
                cwd=ROOT,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            payload["case_index"] = case_index
            payload["repetition"] = repetition
            with raw_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            counts[case_index] += 1
            print(
                f"fill case={case_index:02d} {mode:10s} {family:26s} "
                f"n={order:7d} rep={repetition}/{args.target} solve={payload['solve_seconds']:.4f}s",
                flush=True,
            )


if __name__ == "__main__":
    main()
