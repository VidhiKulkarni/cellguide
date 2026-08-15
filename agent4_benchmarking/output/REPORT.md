# Agent 4 — benchmark report

- n = 199 guides
- weights: w_seq=0.4, w_atac=0.3, w_spec=0.3
- Spearman correlation (combined_score vs indel %): ρ = 0.315, p = 5.72e-06
- results table: `results.csv`
- scatter figure: `correlation.png`

No cell_type column — skipping T-cell-open vs K562-open panel check (see `CROSS_CONTEXT_REPORT.md` for the real Table S2 panel check instead — Table S1 and Table S2 are different guide sets in the paper, not the same guides in two contexts).

## Baseline comparison (sequence-only vs accessibility-only vs combined)

Computed directly from `results.csv`'s per-component columns against real Ito et al. 2024 measured indel% (n=199, guides with valid DeepSpCas9/CHOP2014/ATAC/indel values from Supplementary Table S1):

| Component | Spearman ρ vs indel% | p-value |
|---|---|---|
| `sequence_efficacy` only (DeepSpCas9 + CHOPCHOP 2014 blend) | **0.441** | 7.0e-11 |
| `accessibility` only (ATAC, GSM6896554) | 0.084 | 0.24 (not significant) |
| `combined_score` (w_seq=0.4, w_atac=0.3, w_spec=0.3) | 0.315 | 5.7e-06 |

**Finding: the default linear-weighted combination underperforms the sequence-only baseline on this dataset.** This is not a bug — it reproduces what Ito et al. themselves report (`papers/ito_2024/structured_extraction.md`): ATAC accessibility alone does not correlate with indel% across the full 205-gRNA set. Their actual method never linearly blends ATAC into a continuous score; they use it as an **AND-gate filter** on top of sequence scores (`DeepSpCas9 ≥ 60 AND CHOPCHOP ≥ 0.3 AND ATAC ≥ 0.1`), which this codebase reproduces separately as `passes_ito_thresholds()`:

- Evaluable on 179/205 guides (others missing a required raw score)
- vs actual >50% indel: **precision = 0.862**, recall = 0.287 (TP=25, FP=4, FN=62)

I.e. the rule is a high-precision, low-recall *filter* for confidently efficient guides, not a general-purpose ranker — consistent with how the plan describes it (§4.4: "for the live demo, emphasize ranking ... over exact probability calibration").

**Implication for Agent 3's weights** (flagged as a to-do in `agent3_metric_construction/SPEC.md`): the default `GuideScoreWeights(w_seq=0.4, w_atac=0.3, w_spec=0.3)` should not be treated as validated. On this ground truth, ATAC only adds value as a threshold/gate combined with a strong sequence score, not as an independently-weighted linear term at w_atac=0.3. A regression-fit weight (or switching the combined score to `sequence_efficacy` gated by `passes_ito_thresholds()`) would likely track the real data better than the current transparent-but-unfit linear blend.
