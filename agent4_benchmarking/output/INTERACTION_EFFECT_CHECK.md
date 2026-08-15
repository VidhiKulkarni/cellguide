# Agent 4 — testing Ito et al.'s actual (conditional) accessibility claim

n = 199; median CHOPCHOP (chop2014) = 0.280, median DeepSpCas9 = 56.51

| Test | n | Spearman ρ | p-value |
|---|---|---|---|
| Marginal (all guides) — what REPORT.md originally tested | 199 | 0.060 | 0.402 |
| **Conditional: above-median CHOPCHOP or DeepSpCas9 — Ito's actual claim** | 131 | **0.232** | **0.00773** |
| Below-median CHOPCHOP and DeepSpCas9 (should not show the effect, per Ito) | 68 | -0.315 | 0.00882 |

**This reproduces Ito et al.'s claim.** Tested correctly (conditional on sequence score, not marginal), accessibility DOES have a real, statistically significant positive association with editing efficiency (ρ=0.232, p=0.00773). The original REPORT.md's marginal test was the wrong statistic for this claim — the earlier 'accessibility has no value' conclusion does not hold; it was never properly tested. `recommended_score` (sequence-only) is still a reasonable default ranking value on its own, but the honest conclusion is 'accessibility adds conditional information not yet folded into a score,' not 'accessibility failed.'

**Caveat worth flagging, not overselling**: the below-median subset (n=68) shows its own significant correlation (ρ=-0.315, p=0.00882), which Ito's paper doesn't predict or address — worth treating as an open question rather than further evidence either way, since it wasn't a pre-registered hypothesis and the subset is smaller.
