# Result-file schema

## `correctness_audit.json`

Contains the total number of atlas graphs inspected, accepted target-class graphs, exact solver-versus-brute-force scenarios, weighted scenarios, reconstructed witnesses, fast-checker equivalence comparisons, random instances, and unsupported-block rejection status.

## `scaling_raw.jsonl` / `scaling_raw.csv`

One row per fresh-process repetition.

- `case_index`: deterministic benchmark-case identifier;
- `family`: graph generator family;
- `mode`: `weighted` or `unweighted`;
- `requested_vertices`, `vertices`, `edges`, `n_plus_m`;
- `blocks`, `components`;
- `matching_size`, `cost`;
- `seed`, `repetition`;
- `generation_seconds`, `solve_seconds`, `verify_seconds`;
- `peak_rss_mib`;
- `valid_witness`;
- `matching_sha256`.

## `scaling_summary.csv` / `scaling_summary.json`

One row per benchmark case. Repeated timings are summarized by their median; the minimum and maximum solve times and maximum peak RSS are retained.

## `linearity_regression.csv`

Descriptive least-squares regression of solve time against explicit input size \(n+m\), separately for every family and weight mode. These fits are not used to prove complexity.

## `small_baseline_raw.csv` and `small_baseline_summary.csv`

Production-DP versus exhaustive-optimizer timing and exact optimum agreement on deterministic small generated instances.
