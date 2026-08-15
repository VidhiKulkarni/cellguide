# Agent 4 — motif-heuristic and ATAC-averaging follow-up checks

n = 199 real Ito et al. 2024 guides

## Does our own motif heuristic (GC + poly-T) predict real indel%?

Forced sequence_motif_score() (ignoring DeepSpCas9/CHOPCHOP) on all 199 real guides: Spearman ρ=0.043, p=0.544 vs. sequence_efficacy's ρ=0.441 when using DeepSpCas9/CHOPCHOP as designed.
No meaningful signal on its own. The two external tools (DeepSpCas9, CHOPCHOP) are carrying essentially all of sequence_efficacy's real predictive power; our own GC/poly-T heuristic is a reasonable-looking fallback for when no external score is available, not a validated predictor in its own right.

## Does averaging both ATAC replicates give a more stable accessibility signal?

| Signal | accessibility ρ | p | gate precision | gate recall |
|---|---|---|---|---|
| GSM6896554 alone | 0.084 | 0.239 | 0.862 | 0.287 |
| GSM7256892 alone | 0.019 | 0.792 | 1.000 | 0.138 |
| **Average of both** | **0.062** | **0.386** | **0.941** | **0.184** |

Still not a statistically significant signal even averaged — the two replicates' disagreement is not just independent noise that cancels out; accessibility's predictive value for this benchmark remains unsupported.
