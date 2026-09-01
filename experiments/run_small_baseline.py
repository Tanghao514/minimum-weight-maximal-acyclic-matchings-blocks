#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

from generator import generate_block_tree  # noqa: E402
from mmacm import solve_min_weight_maximal_acyclic_matching  # noqa: E402
from mmacm.bruteforce import brute_force_min_weight_maximal_acyclic_matching  # noqa: E402

FAMILIES = ("cactus", "block_graph", "multipartite", "mixed")
ORDERS = (4, 6, 8, 10, 12, 14)
REPETITIONS = 5


def main() -> None:
    output_dir = ROOT / "experiments" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []

    for family in FAMILIES:
        for order in ORDERS:
            for rep in range(REPETITIONS):
                seed = 8_290_000 + 100_000 * FAMILIES.index(family) + 1_000 * order + rep
                item = generate_block_tree(order, seed=seed, family=family)

                start = time.perf_counter()
                result = solve_min_weight_maximal_acyclic_matching(item.graph)
                solver_seconds = time.perf_counter() - start

                start = time.perf_counter()
                brute_cost, brute_matching = brute_force_min_weight_maximal_acyclic_matching(item.graph)
                brute_seconds = time.perf_counter() - start

                if result.cost != brute_cost:
                    raise AssertionError(
                        f"baseline discrepancy family={family}, n={order}, rep={rep}: "
                        f"solver={result.cost}, brute={brute_cost}, "
                        f"solver matching={result.matching}, brute matching={brute_matching}"
                    )
                rows.append(
                    {
                        "family": family,
                        "vertices": item.graph.number_of_nodes(),
                        "edges": item.graph.number_of_edges(),
                        "seed": seed,
                        "repetition": rep + 1,
                        "optimum": result.cost,
                        "solver_seconds": solver_seconds,
                        "bruteforce_seconds": brute_seconds,
                        "speedup": brute_seconds / solver_seconds if solver_seconds else float("inf"),
                    }
                )
                print(
                    f"{family:14s} n={order:2d} rep={rep+1}/{REPETITIONS} "
                    f"solver={solver_seconds:.6f}s brute={brute_seconds:.6f}s",
                    flush=True,
                )

    with (output_dir / "small_baseline_raw.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["family"], row["vertices"])].append(row)
    summary: list[dict] = []
    for (family, order), group in sorted(groups.items()):
        summary.append(
            {
                "family": family,
                "vertices": order,
                "instances": len(group),
                "median_edges": statistics.median(row["edges"] for row in group),
                "solver_median_seconds": statistics.median(row["solver_seconds"] for row in group),
                "bruteforce_median_seconds": statistics.median(row["bruteforce_seconds"] for row in group),
                "speedup_median": statistics.median(row["speedup"] for row in group),
                "all_equal": True,
            }
        )
    with (output_dir / "small_baseline_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    (output_dir / "small_baseline_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    lines = [
        "# Small-instance baseline comparison",
        "",
        "The production dynamic program and the definition-level exhaustive solver were run on the same deterministic generated graphs. All optimum values agreed.",
        "",
        "| Family | n | Instances | Median m | DP median/s | Brute median/s | Median speedup |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['family']} | {row['vertices']} | {row['instances']} | {row['median_edges']:.0f} | "
            f"{row['solver_median_seconds']:.6f} | {row['bruteforce_median_seconds']:.6f} | "
            f"{row['speedup_median']:.2f}x |"
        )
    (output_dir / "SMALL_BASELINE_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "instances": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
