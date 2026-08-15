# Agent 4 — benchmark report

- n = 199 guides
- weights: w_seq=0.4, w_atac=0.3, w_spec=0.3
- Spearman correlation (combined_score vs indel %): ρ = 0.315, p = 5.72e-06
- results table: `results.csv`
- scatter figure: `correlation.png`

### Baseline comparison (component-only vs combined)

| Component | Spearman ρ vs indel% | p-value |
|---|---|---|
| `sequence_efficacy` | 0.441 | 7.01e-11 |
| `accessibility` | 0.084 | 0.239 |
| `combined_score` | 0.315 | 5.72e-06 |
| `recommended_score` | 0.441 | 7.01e-11 |

`passes_ito_rule()` as a >50%-indel classifier: precision=0.862, recall=0.287 (TP=25, FP=4, FN=62, evaluable on 199/199 guides).

No cell_type column — skipping T-cell-open vs K562-open panel check.
