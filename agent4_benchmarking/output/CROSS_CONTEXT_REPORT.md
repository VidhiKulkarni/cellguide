# Agent 4 — cross-context panel check (Ito et al. 2024 Table S2)

n = 11 genes (6 T-cell-open, 5 K562-open — matches the plan's §3.3 10-gene panel + EOMES)

No per-guide indel% ground truth is available for this panel (the paper reports it only as Figure 2H-K, not as numbers) — this check validates only what real data supports: whether the accessibility term alone, computed from real ATAC-seq scores, correctly flips direction between T cells and K562 for each gene's designated 'open' context, while sequence_efficacy stays fixed for the same guide across contexts (by construction, since sequence doesn't change).

**Result: accessibility correctly predicts the paper's reported open-chromatin context for 11/11 genes.**

| Gene | Category | seq_efficacy (fixed) | accessibility (T cell) | accessibility (K562) | matches paper? |
|---|---|---|---|---|---|
| GZMA | T cell-associated genes | 0.767 | 1.0 | 0.0 | True |
| GZMB | T cell-associated genes | 0.883 | 1.0 | 0.0 | True |
| CD3D | T cell-associated genes | 0.883 | 1.0 | 0.0 | True |
| CD28 | T cell-associated genes | 1.0 | 1.0 | 0.0 | True |
| EOMES | T cell-associated genes | 1.0 | 1.0 | 0.0 | True |
| CD3G | T cell-associated genes | 0.883 | 1.0 | 0.0 | True |
| CD33 | Myeloerythroid-associated genes | 0.883 | 0.232 | 1.0 | True |
| GATA1 | Myeloerythroid-associated genes | 0.883 | 0.465 | 1.0 | True |
| HBB | Myeloerythroid-associated genes | 0.883 | 0.465 | 1.0 | True |
| HBE1 | Myeloerythroid-associated genes | 1.0 | 0.232 | 1.0 | True |
| TFR2 | Myeloerythroid-associated genes | 0.767 | 0.31 | 1.0 | True |

Results CSV: `cross_context_panel_results.csv`
