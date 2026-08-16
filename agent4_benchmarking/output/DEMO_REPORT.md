# Agent 4 — benchmark report (DEMO — synthetic data, not real Ito et al. 2024 numbers)

- n = 4 guides
- weights: w_seq=0.4, w_atac=0.3
- Spearman correlation (combined_score vs indel %): ρ = 0.800, p = 0.2
- results table: `demo_results.csv`
- scatter figure: `demo_correlation.png`

### Baseline comparison (component-only vs combined)

`combined_score = 0.4*sequence_efficacy + 0.3*accessibility` (renormalized when accessibility is unavailable for a guide).

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

F1 improves when the ATAC≥0.1 gate is added (0.667 -> 1.000), but **F1 is the wrong metric to judge this rule by** — SPEC.md itself documents this as intended to be "a high-precision, low-recall filter, not a general ranker," and *any* added AND-condition mechanically reduces recall regardless of whether the added condition is useful, so F1 will almost always fall here. What the gate is actually designed to do is raise precision, and it does: 0.500 -> 1.000. See `interaction_effect_check.py` for the statistically correct test of Ito et al.'s actual accessibility claim (a conditional effect, not reflected in this precision/recall table) — evaluable on 4/4 guides here.

### T-cell-open vs K562-open panel check

- **GATA1**: K562=0.777, T=0.477
- **GZMA**: T=0.806, K562=0.463
