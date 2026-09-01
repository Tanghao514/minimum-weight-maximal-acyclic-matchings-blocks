# Experiment result files

Files distributed in release `v1.0.0`:

- `correctness_audit.json`: exhaustive atlas and deterministic random audit;
- `small_baseline_raw.csv`, `small_baseline_summary.csv`,
  `small_baseline_summary.json`, and `SMALL_BASELINE_REPORT.md`: production
  dynamic program versus exhaustive optimization;
- `scaling_raw.jsonl` and `scaling_raw.csv`: 168 fresh-process scale runs;
- `scaling_summary.csv` and `scaling_summary.json`: 56 cases, each summarized
  from three repetitions;
- `linearity_regression.csv` and `linearity_regression.json`: descriptive fits
  against explicit input size;
- `environment.json` and `dependency_check.json`: software and hardware
  metadata;
- `final_release_validation.json`: cross-file checks recorded before release;
- `runtime_*.png` and `peak_memory_*.png`: generated plots.

The raw JSONL/CSV files and the final summaries are the source of record.
