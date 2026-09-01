#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python -m pip install -e ".[dev]" --no-build-isolation
python -m pytest -q
python experiments/run_correctness_audit.py
python experiments/run_small_baseline.py
python experiments/run_scaling.py --start 1 --end 56 --reset
python experiments/run_scaling.py --summarize
python scripts/build_manifest.py
python scripts/validate_release.py
