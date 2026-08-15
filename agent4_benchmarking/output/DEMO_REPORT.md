# Agent 4 — benchmark report (DEMO — synthetic data, not real Ito et al. 2024 numbers)

- n = 4 guides
- weights: w_seq=0.4, w_atac=0.3, w_spec=0.3
- Spearman correlation (combined_score vs indel %): ρ = 0.800, p = 0.2
- results table: `demo_results.csv`
- scatter figure: `demo_correlation.png`

### Baseline comparison (component-only vs combined)

| Component | Spearman ρ vs indel% | p-value |
|---|---|---|
| `sequence_efficacy` | 0.447 | 0.553 |
| `accessibility` | 0.738 | 0.262 |
| `combined_score` | 0.800 | 0.2 |

`passes_ito_rule()` as a >50%-indel classifier: precision=1.000, recall=1.000 (TP=2, FP=0, FN=0, evaluable on 4/4 guides).

### T-cell-open vs K562-open panel check

- **GATA1**: K562=0.844, T=0.634
- **GZMA**: T=0.864, K562=0.624
