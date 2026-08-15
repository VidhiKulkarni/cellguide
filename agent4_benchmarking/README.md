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

## Ground-truth data

`../papers/ito_2024/table_s1_for_agent4.csv` (205-gRNA Table S1, real row-level data —
fetched via Europe PMC's supplementary-files API and parsed with `openpyxl` since paperclip
only surfaced a schema summary; see `../papers/ito_2024/DATA_PROVENANCE.md`) is the real
`--data` input. `--data` expects a CSV with columns
`gene, spacer, atac_signal, chopchop_score, deepspcas9_score, indel_pct` (+ optional
`cell_type`).

**Real result so far**: on n=199 guides, `combined_score` (ρ=0.315) underperforms
`sequence_efficacy` alone (ρ=0.441) — see `output/REPORT.md`. Ito et al. never linearly
blend ATAC; they gate on it (`passes_ito_thresholds()`, precision=0.862/recall=0.287 on this
data). Agent 3's default linear weights are not validated by this benchmark — see
[Agent 5](../agent5_confidence_assessment/)'s review for the full critique.

`cross_context_panel.py` runs the separate Table S2 check (the 11-gene T-cell-open vs
K562-open panel) — no indel% ground truth exists for that panel (only Figure 2H-K in the
paper), so it only validates the accessibility term's *direction*, not a score-vs-outcome
correlation:

```bash
uv run agent4_benchmarking/cross_context_panel.py
```

## Output

`output/results.csv`, `output/correlation.png`, `output/REPORT.md` (real data) or
`output/demo_*` (synthetic, via `--demo`); `output/cross_context_panel_results.csv` +
`output/CROSS_CONTEXT_REPORT.md` (Table S2 check).
