# Agent 4 — benchmark report (DEMO — synthetic data, not real Ito et al. 2024 numbers)

- n = 4 guides
- weights: w_seq=0.4, w_atac=0.3, w_spec=0.3
- Spearman correlation (combined_score vs indel %): ρ = 0.800, p = 0.2
- results table: `demo_results.csv`
- scatter figure: `demo_correlation.png`

### T-cell-open vs K562-open panel check

- **GATA1**: K562=0.844, T=0.634
- **GZMA**: T=0.864, K562=0.624
