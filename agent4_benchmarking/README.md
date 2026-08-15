# Agent 4 — benchmarking / validation

Deterministic script (no LLM) — scores guides with [Agent 3](../agent3_metric_construction/)'s
metric and compares against Ito et al. 2024's measured indel%, including the T-cell-open vs
K562-open cross-context panel check.

## Run

```bash
# sanity-check the script itself against synthetic data (no real ground truth needed):
uv run agent4_benchmarking/run.py --demo

# real benchmark, once ground-truth data is available:
uv run agent4_benchmarking/run.py --data path/to/table_s1.csv
```

## Ground-truth data gap

`../papers/ito_2024/` currently only has a **schema summary** of Supplementary Table S1
(205 gRNAs) and Table S2 (the 7-gene T-cell/K562 panel) — not row-level values (see
`../papers/ito_2024/structured_extraction.md`). `--data` expects a CSV with columns
`gene, spacer, atac_signal, chopchop_score, deepspcas9_score, indel_pct` (+ optional
`cell_type`). Fetching that row-level data (re-running [Agent 1](../agent1_literature_search/)
against the NAR supplementary Excel file and exporting it to CSV) is a prerequisite for a
real run.

## Output

`output/results.csv`, `output/correlation.png`, `output/REPORT.md` (or `demo_*` variants
under `--demo`).
