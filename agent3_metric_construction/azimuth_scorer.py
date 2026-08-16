#!/usr/bin/env python3
"""
Runs INSIDE the `azimuth` conda environment (~/miniforge3/envs/azimuth) — this file is not
importable from the main `uv`-managed environment, because Azimuth's real trained model
(Doench et al. 2016, PMID 26780180 — https://pubmed.ncbi.nlm.nih.gov/26780180/) only loads
under an old scikit-learn/biopython stack that can't coexist with our modern one. See
guide_scoring.py's azimuth_score() for how the main pipeline calls this as a subprocess.

Reads a JSON array of 30-mer sequences from stdin ([4nt upstream][20nt spacer][NGG PAM]
[3nt downstream] — a bare 20nt spacer is NOT enough, Azimuth's model uses the flanking
context as real features), writes a JSON array of scores (or null per-sequence on error) to
stdout.

Usage (called by guide_scoring.py, not normally run directly):
    echo '["ACAGCTGATCTCCAGATATGACCATGGGTT"]' | \
        ~/miniforge3/bin/mamba run -n azimuth python azimuth_scorer.py
"""

import json
import sys


def main() -> None:
    sequences_in = json.loads(sys.stdin.read())
    if not isinstance(sequences_in, list):
        sys.exit("Input must be a JSON array of 30-mer sequence strings.")

    import numpy as np
    import azimuth.model_comparison

    scores = []
    for seq in sequences_in:
        if len(seq) != 30:
            scores.append(None)  # not a valid 30-mer, refuse to score rather than guess
            continue
        try:
            pred = azimuth.model_comparison.predict(np.array([seq]))
            scores.append(float(pred[0]))
        except Exception:
            scores.append(None)

    print(json.dumps(scores))


if __name__ == "__main__":
    main()
