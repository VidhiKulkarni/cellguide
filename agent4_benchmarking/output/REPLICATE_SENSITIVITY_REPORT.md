# Agent 4 — ATAC replicate sensitivity check

| Replicate | n | accessibility ρ | p | gate precision | gate recall | TP | FP | FN |
|---|---|---|---|---|---|---|---|---|
| GSM6896554 (used by run.py) | 199 | 0.084 | 0.239 | 0.862 | 0.287 | 25 | 4 | 62 |
| GSM7256892 | 199 | 0.019 | 0.792 | 1.000 | 0.138 | 12 | 0 | 75 |

If these numbers move a lot between replicates, the ATAC>=0.1 threshold is picking up sequencing-run-specific scale/noise, not a stable biological cutoff — treat any single-replicate accessibility result with that in mind.
