# Agent 3 — CellGuide efficiency + specificity scoring spec

Implementation: `scoring/guide_scoring.py`. Built from the structured literature extraction in `papers/related/SUMMARY.md` (Agent 2 output) and the plan's own §4.4 formula.

## Formula

```
score(g, c) = w_seq * sequence_efficacy(g) + w_atac * accessibility(g, c) + w_spec * specificity(g)
```

Linear and transparent by design (plan §4.4: "Start with transparent weights ... compare against sequence-only"; plan §2: "Keep the biological scoring functions inspectable"). Each term is independently inspectable and swappable for a trained model later.

## Component 1 — `sequence_efficacy(g)` (on-target efficiency)

- **Preferred inputs**: `deepspcas9_score` (0-100, native DeepSpCas9 scale) and/or `chopchop_score` (0-1, native CHOPCHOP/Doench scale) — the two tools Ito et al. 2024 found most predictive on their own 205-gRNA T-cell dataset (`papers/ito_2024/structured_extraction.md`). When both are given, they're averaged after normalizing to `[0,1]`.
- **Fallback (no external scorer available)**: a transparent sequence heuristic — GC content (optimal ~50%, per `wang_2019_deephf`), PAM-proximal seed-region GC content (Doench-style seed weighting), and a poly-T penalty (U6 promoter terminates transcription on `TTTT+`). This is the "GC content, motif" heuristic requested in `CLAUDE.md`.
- **Not implemented, left pluggable**: DeepHF (`papers/wang_2019_deephf/`) — best Spearman 0.867 in its own lentiviral HEK293T assay, but trained on synthetic integrated targets, not endogenous primary-cell loci; treat as one more optional external score to wire in, not a ready-made drop-in.
- **Caveat baked into the design**: `riesenberg2025_synthetic_grna` shows indel% can *underestimate* true cutting activity — this score is a ranking signal, not a calibrated probability of editing.

## Component 2 — `accessibility(g, c)` (cell context)

- **Input**: `atac_signal` — median ATAC-seq read count/signal over the guide's target window in the target cell type (plan §3.1/§4.1: GSE221788 for T cells, GSE137647 for K562).
- **Normalization**: `min(1, atac_signal / 0.1)`, reusing Ito et al.'s own empirical ATAC ≥ 0.1 cutoff as the point where the term saturates at 1.0.
- **Returns 0 (not a guess) when no ATAC data is supplied** for that cell context, so a missing accessibility measurement doesn't silently masquerade as "inaccessible."
- **Important caveat, from `wang_2019_deephf`**: fine-tuning with DNase-I accessibility did *not* improve their model — accessibility only mattered in Ito et al.'s **transient RNP** delivery, not Wang's lentiviral-integration assay. `schep2024_chromatin_drugs` independently corroborates the RNP-context effect (chromatin state also shifts NHEJ:MMEJ repair balance). Do not apply this accessibility term to stably-integrated/lentiviral delivery contexts without re-validating.

## Component 3 — `specificity(g)` (off-target / inverse risk)

- **Gap this fills**: Ito et al. 2024 — the plan's primary ground-truth paper — reports **no off-target data at all** (`papers/ito_2024/structured_extraction.md`). The specificity term must come entirely from other sources.
- **Preferred inputs (recommended, not yet wired to real data)**: `external_specificity_score` from crispAI (`papers/related/ozden2024_crispai_uncertainty/`) or CrisprBERT (`papers/related/sari2025_crisprbert/`) — both trained on the same CHANGE-seq 110-sgRNA/13-locus **primary human T-cell** off-target dataset that overlaps Ito et al.'s cell system, making them the closest-context specificity predictors available.
- **Fallback**: a CFD (Cutting Frequency Determination)-style aggregate over an enumerated off-target site list (`OffTargetSite(mismatches, mismatch_positions, cfd_pam_score)`), using the standard Doench et al. 2016 position-weight table (PAM-proximal mismatches penalized far more than PAM-distal). Off-target sites themselves are not enumerated by this module — plug in an external candidate generator (e.g. Cas-OFFinder, or `papers/related/schmidt2025_guidescan2/` GuideScan2, which also builds low-off-target guide libraries directly).
- **Not modeled**: `ursch2024_tcell_genomic_safety`'s finding that T-cell **activation state** (not sequence) drives large deletions/translocations/aneuploidy — a genomic-safety signal orthogonal to sequence-based off-target prediction. Flagged as a known gap, not folded into `specificity()`.

## Default weights

```python
GuideScoreWeights(w_seq=0.4, w_atac=0.3, w_spec=0.3)
```

Equal-ish split favoring on-target slightly, as an arbitrary transparent starting point — **not fit to data**. Agent 4 should re-derive these (e.g. via regularized regression against `papers/ito_2024/` measured indel%, per the plan's own recommendation) rather than treating the defaults as final.

## `passes_ito_thresholds(...)`

A separate, non-weighted rule-based classifier that directly reproduces Ito et al.'s validated empirical rule on the tools' **native scales** (not the normalized `[0,1]` scores used elsewhere): `DeepSpCas9 >= 60 AND CHOPCHOP >= 0.3 AND ATAC >= 0.1`. Returns `False` (not a guess) whenever any of the three raw inputs is missing. Useful as a binary sanity check alongside the continuous `combined` score, and as the exact metric Agent 4 should try to reproduce on the T-cell/K562 cross-context panel.

## Known limitations / not yet implemented

- No real genome, ATAC bigWig, or off-target enumeration data is wired into this module yet — it is a scoring *library* with well-defined inputs, not an end-to-end pipeline. Workstream A (`docs/CellGuide_AI_Hackathon_Plan.pdf` §5) still needs to build the feature extractor that turns raw ATAC/genome files into the `atac_signal` / `OffTargetSite` inputs this module expects.
- No CRISPRi/CRISPRa scoring — `papers/related/SUMMARY.md` notes that none of the 18 papers pulled so far cover CRISPRi/CRISPRa, consistent with the plan's SpCas9-knockout-oriented MVP scope.
- Repair-outcome/frameshift prediction (v2 roadmap stage) is out of scope for this module; see `papers/related/zhang2024_deepindel/` and `papers/related/seale2025_xcrisp/` as starting points when that stage begins.
