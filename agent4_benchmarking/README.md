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

**Real result so far, and it's a humbling one**: on n=199 guides, `combined_score` (ρ=0.315)
underperforms `sequence_efficacy` alone (ρ=0.441) — see `output/REPORT.md`. Worse, the
accessibility gate (`passes_ito_thresholds()`) actually **reduces F1** relative to sequence
gates alone (0.593 -> 0.431: precision goes up, 0.741->0.862, but recall collapses,
0.494->0.287) — also in `output/REPORT.md`'s "Does the accessibility gate earn its keep?"
section. And `specificity` was unevaluated for all 199 guides (no off-target data source
wired in for this benchmark), so `combined_score`'s advertised
w_seq=0.4/w_atac=0.3/w_spec=0.3 is really an undisclosed w_seq=0.571/w_atac=0.429 — also
now called out explicitly in the report. **As currently validated, CellGuide's differentiator
(cell-context/chromatin accessibility) has not demonstrated value on its own benchmark** —
see [Agent 5](../agent5_confidence_assessment/)'s review for the full critique, including
why (in-sample tuning, an untested cell-context claim, and more).

`replicate_sensitivity_check.py` shows *why* the accessibility numbers above should be
read with real caution: the source data has two ATAC-seq replicates for the same 205
guides, and they disagree badly — the gate's precision/recall swing from 0.862/0.287 to
1.000/0.138 depending on which one you use:

```bash
uv run agent4_benchmarking/replicate_sensitivity_check.py
```

`cross_context_panel.py` runs the separate Table S2 check (the 11-gene T-cell-open vs
K562-open panel) — no indel% ground truth exists for that panel (only Figure 2H-K in the
paper), and the genes in Table S2 don't overlap with Table S1's indel measurements, so this
can only validate the accessibility term's *direction* against the paper's own chromatin
calls, not a real score-vs-outcome correlation — it is not evidence that the cell-context
premise improves editing-outcome prediction:

```bash
uv run agent4_benchmarking/cross_context_panel.py
```

## Output

`output/results.csv`, `output/correlation.png`, `output/REPORT.md` (real data) or
`output/demo_*` (synthetic, via `--demo`); `output/REPLICATE_SENSITIVITY_REPORT.md` (ATAC
replicate check); `output/cross_context_panel_results.csv` + `output/CROSS_CONTEXT_REPORT.md`
(Table S2 check).
