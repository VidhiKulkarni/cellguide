# Agent 4 — benchmark report

- n = 199 guides
- weights: w_seq=0.4, w_atac=0.3, w_spec=0.3
- Spearman correlation (combined_score vs indel %): ρ = 0.315, p = 5.72e-06
- results table: `results.csv`
- scatter figure: `correlation.png`

### Baseline comparison (component-only vs combined)

**Effective weights**: specificity was unevaluated for all 199 guides (no off-target data wired in for this benchmark) — `combined_score` is actually `0.571 * sequence_efficacy + 0.429 * accessibility`, not the advertised w_seq=0.4/w_atac=0.3/w_spec=0.3.

| Component | Spearman ρ vs indel% | p-value |
|---|---|---|
| `sequence_efficacy` | 0.441 | 7.01e-11 |
| `accessibility` | 0.084 | 0.239 |
| `combined_score` | 0.315 | 5.72e-06 |
| `recommended_score` | 0.441 | 7.01e-11 |

### Does the accessibility gate earn its keep? (>50%-indel classifier)

| Rule | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Sequence gates only (no ATAC) | 0.741 | 0.494 | 0.593 | 43 | 15 | 44 |
| Full Ito rule (+ ATAC≥0.1) | 0.862 | 0.287 | 0.431 | 25 | 4 | 62 |

F1 drops when the ATAC≥0.1 gate is added (0.593 -> 0.431), but **F1 is the wrong metric to judge this rule by** — SPEC.md itself documents this as intended to be "a high-precision, low-recall filter, not a general ranker," and *any* added AND-condition mechanically reduces recall regardless of whether the added condition is useful, so F1 will almost always fall here. What the gate is actually designed to do is raise precision, and it does: 0.741 -> 0.862. See `interaction_effect_check.py` for the statistically correct test of Ito et al.'s actual accessibility claim (a conditional effect, not reflected in this precision/recall table) — evaluable on 199/199 guides here.

No cell_type column — skipping T-cell-open vs K562-open panel check.
