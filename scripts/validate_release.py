#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "pyproject.toml",
    "src/mmacm/solver.py",
    "src/mmacm/signatures.py",
    "tests/test_basic.py",
    "experiments/run_correctness_audit.py",
    "experiments/run_small_baseline.py",
    "experiments/run_scaling.py",
    "experiments/results/correctness_audit.json",
    "experiments/results/small_baseline_raw.csv",
    "experiments/results/small_baseline_summary.csv",
    "experiments/results/scaling_raw.jsonl",
    "experiments/results/scaling_summary.csv",
    "experiments/results/environment.json",
    "experiments/results/final_release_validation.json",
    "docs/experimental_methods.md",
    "docs/experimental_results.md",
    "MANIFEST_SHA256.txt",
]

missing = [relative for relative in REQUIRED if not (ROOT / relative).is_file()]
if missing:
    raise SystemExit(f"missing release files: {missing}")

audit = json.loads(
    (ROOT / "experiments/results/correctness_audit.json").read_text(encoding="utf-8")
)
if audit.get("status") != "PASS":
    raise SystemExit("correctness audit did not pass")

with (ROOT / "experiments/results/scaling_summary.csv").open(encoding="utf-8") as handle:
    scaling = list(csv.DictReader(handle))
if len(scaling) != 56:
    raise SystemExit(f"expected 56 scale cases, found {len(scaling)}")
if not all(row["valid_all"] == "True" for row in scaling):
    raise SystemExit("scale summary contains an invalid witness")
if not all(int(row["repetitions"]) == 3 for row in scaling):
    raise SystemExit("not every scale case has three repetitions")

raw_lines = [
    line
    for line in (ROOT / "experiments/results/scaling_raw.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line.strip()
]
if len(raw_lines) != 168:
    raise SystemExit(f"expected 168 raw scale runs, found {len(raw_lines)}")

with (ROOT / "experiments/results/small_baseline_raw.csv").open(
    encoding="utf-8"
) as handle:
    baseline_raw = list(csv.DictReader(handle))
if len(baseline_raw) != 120:
    raise SystemExit(f"expected 120 baseline instances, found {len(baseline_raw)}")

with (ROOT / "experiments/results/small_baseline_summary.csv").open(
    encoding="utf-8"
) as handle:
    baseline = list(csv.DictReader(handle))
if not baseline or not all(row["all_equal"] == "True" for row in baseline):
    raise SystemExit("small baseline is incomplete or has a discrepancy")

final_validation = json.loads(
    (ROOT / "experiments/results/final_release_validation.json").read_text(
        encoding="utf-8"
    )
)
if final_validation.get("status") != "PASS":
    raise SystemExit("final release validation did not pass")

manifest_rows = 0
for line in (ROOT / "MANIFEST_SHA256.txt").read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    try:
        expected, relative = line.split("  ", 1)
    except ValueError as exc:
        raise SystemExit(f"malformed manifest line: {line!r}") from exc
    path = ROOT / relative
    if not path.is_file():
        raise SystemExit(f"manifest path is missing: {relative}")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"manifest mismatch: {relative}")
    manifest_rows += 1

print(
    json.dumps(
        {
            "status": "PASS",
            "required_files": len(REQUIRED),
            "manifest_files": manifest_rows,
            "scale_cases": len(scaling),
            "scale_runs": len(raw_lines),
            "baseline_instances": len(baseline_raw),
            "correctness_instances": audit["atlas_solver_vs_bruteforce_instances"]
            + audit["random_small_instances"],
        },
        indent=2,
    )
)
