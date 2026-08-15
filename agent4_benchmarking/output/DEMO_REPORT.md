# Agent 4 — benchmark report (DEMO — synthetic data, not real Ito et al. 2024 numbers)

- n = 4 guides
- weights: w_seq=0.4, w_atac=0.3, w_spec=0.3
- Spearman correlation (combined_score vs indel %): ρ = 0.800, p = 0.2
- results table: `demo_results.csv`
- scatter figure: `demo_correlation.png`

### Baseline comparison (component-only vs combined)

**Effective weights**: specificity was unevaluated for all 4 guides (no off-target data wired in for this benchmark) — `combined_score` is actually `0.571 * sequence_efficacy + 0.429 * accessibility`, not the advertised w_seq=0.4/w_atac=0.3/w_spec=0.3.

| Component | Spearman ρ vs indel% | p-value |
|---|---|---|
| `sequence_efficacy` | 0.447 | 0.553 |
| `accessibility` | 0.738 | 0.262 |
| `combined_score` | 0.800 | 0.2 |
| `recommended_score` | 0.447 | 0.553 |

### Does the accessibility gate earn its keep? (>50%-indel classifier)

| Rule | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Sequence gates only (no ATAC) | 0.500 | 1.000 | 0.667 | 2 | 2 | 0 |
| Full Ito rule (+ ATAC≥0.1) | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 |

Adding the ATAC≥0.1 gate improves F1 relative to sequence gates alone (0.667 -> 1.000) on this dataset — evaluable on 4/4 guides.

### T-cell-open vs K562-open panel check

- **GATA1**: K562=0.777, T=0.477
- **GZMA**: T=0.806, K562=0.463
