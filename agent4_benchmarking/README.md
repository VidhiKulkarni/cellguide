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
`cell_type`). `indel_pct` is mapped from the source table's `indel_avg` column (the mean
across replicates), matching the paper's own stated methodology ("obtained at least in
duplicate, and the mean values were used"); `atac_signal` is the `GSM6896554` replicate (see
`replicate_sensitivity_check.py` for why the other replicate gives different results);
`chopchop_score` is `chop2014` (CHOPCHOP/Doench 2014, the specific tool the paper names).
205 raw rows drop to 199 because 6 have a placeholder `"-"` instead of a numeric score in
`chop2014` or `deepspcas9` (missing scores for those tools, not missing measurements).

**Real results, revised once already after Agent 5 caught a methodology error** — on n=199
guides, `combined_score` (ρ=0.315) underperforms `sequence_efficacy` alone (ρ=0.441) — see
`output/REPORT.md` — so `recommended_score` is sequence-only. `specificity` (off-target risk)
was never wired to real data and has since been removed from the scoring library entirely,
not just left unevaluated — see `agent3_metric_construction/SPEC.md` "Known limitations."
`combined_score` is now a plain 2-component blend (`w_seq=0.4/w_atac=0.3`), nothing hidden.

For accessibility specifically: the first pass tested the *marginal* ATAC-indel correlation
(ρ=0.084, n.s.) and concluded accessibility "has not demonstrated value." **That was the
wrong statistical test.** Ito et al.'s actual claim is conditional: accessibility predicts
efficiency *among guides with above-median sequence scores*, not marginally across everyone.
Tested that way (`interaction_effect_check.py`), the effect reproduces — ρ=0.232, p=0.008 on
the n=131 above-median subset. The gate's F1 drop is similarly a mis-specified read: SPEC.md
already documents it as a deliberate high-precision/low-recall filter, and *any* added
AND-condition mechanically reduces recall, so F1 was never a fair way to judge it — precision
is what it's designed for, and precision does rise (0.741 -> 0.862). **Honest current
conclusion: accessibility has real conditional predictive value that isn't there
marginally — this project's core differentiator is more defensible than the first pass
suggested, but it's not yet folded into a single score correctly.** See
[Agent 5](../agent5_confidence_assessment/)'s review for the full critique (including
findings that still stand: in-sample tuning, the untested cross-cell-type claim, and more).

`motif_and_accessibility_checks.py` tried to rescue the *sequence-motif* story two ways — forcing our own
from-scratch sequence heuristic instead of the external DeepSpCas9/CHOPCHOP tools, and
averaging both ATAC replicates instead of using one — and neither helped (motif heuristic
ρ=0.043 n.s.; averaged ATAC ρ=0.062, p=0.386, still n.s.):

```bash
uv run agent4_benchmarking/motif_and_accessibility_checks.py
```

`interaction_effect_check.py` runs the statistically correct test of Ito et al.'s actual
(conditional) accessibility claim — this is the one that reverses the "accessibility failed"
conclusion:

```bash
uv run agent4_benchmarking/interaction_effect_check.py
```

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
`output/demo_*` (synthetic, via `--demo`); `output/INTERACTION_EFFECT_CHECK.md` (the
corrected accessibility test); `output/REPLICATE_SENSITIVITY_REPORT.md` (ATAC replicate
check); `output/MOTIF_AND_ACCESSIBILITY_CHECKS.md` (the two sequence-motif rescue attempts);
`output/cross_context_panel_results.csv` + `output/CROSS_CONTEXT_REPORT.md` (Table S2 check).
