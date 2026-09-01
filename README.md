# Minimum-Weight Maximal Acyclic Matchings on Structured-Block Graphs

This repository contains the reference implementation, tests, experiment
scripts, and raw validation data accompanying the manuscript
*Minimum-Weight Maximal Acyclic Matchings on Graphs with Cycle or
Complete-Multipartite Blocks*.

For a finite simple graph whose nontrivial blocks are cycles or complete
multipartite graphs, the implementation computes and reconstructs a
minimum-cost inclusion-wise maximal acyclic matching.  The algorithm uses
`O(|V|+|E|)` arithmetic and comparison operations and linear space.  With
constant-word weights and intermediate values, this is linear word-RAM time.

## Repository contents

- `src/mmacm/`: block decomposition, recognition, local signatures, global
  dynamic programming, witness reconstruction, and independent checkers.
- `tests/`: unit, edge-case, CLI, and deterministic random cross-check tests.
- `experiments/`: deterministic generators and correctness/scaling scripts.
- `experiments/results/`: raw and summarized data reported in the manuscript.
- `docs/`: concise descriptions of the experimental protocol and results.
- `scripts/`: release-manifest and artifact-validation utilities.

## Installation

Python 3.10 or newer is required.

```bash
python -m pip install -e ".[dev]" --no-build-isolation
python -m pytest -q
```

The recorded experiment environment used Python 3.13.5, NetworkX 3.6.1,
and Matplotlib 3.10.8.  Exact versions are listed in
`requirements-lock.txt` and `experiments/results/environment.json`.

## Python API

```python
import networkx as nx
from mmacm import solve_min_weight_maximal_acyclic_matching

G = nx.cycle_graph(8)
result = solve_min_weight_maximal_acyclic_matching(G, verify=True)
print(result.cost)
print(result.matching)
```

With omitted weights, every edge has weight 1 and every saturated vertex has
cost 0.  Signed edge weights and signed vertex-saturation costs are supported.

## Command line

```bash
python -m mmacm --json examples/mixed_example.json --verify
python -m mmacm --edge-list examples/mixed_example.edgelist \
  --vertex-costs examples/vertex_costs.json --verify
python -m mmacm --graph6 'Ch' --verify
```

## Reproducing the validation

Run the test suite and correctness audits:

```bash
python -m pytest -q
python experiments/run_correctness_audit.py
python experiments/run_small_baseline.py
```

Re-running the full scale benchmark can take substantial time and overwrites
the benchmark result files:

```bash
python experiments/run_scaling.py --start 1 --end 56 --reset
python experiments/run_scaling.py --summarize
```

The archived release records 1,341 production-solver versus exhaustive-
optimizer instances, 360 additional deterministic random weighted instances,
120 small-baseline instances, and 168 scale runs.  All recorded witnesses
passed independent validation and no optimum discrepancy was found.

Validate the archived files without rerunning the experiments:

```bash
python scripts/validate_release.py
```

`scripts/build_manifest.py` is a maintainer utility for regenerating the
SHA-256 manifest after intentionally replacing release files.

## Citation

Please cite release `v1.0.0` of this repository and the accompanying
manuscript.  Machine-readable metadata are provided in `CITATION.cff`.

## License

The software and accompanying data are released under the MIT License.
