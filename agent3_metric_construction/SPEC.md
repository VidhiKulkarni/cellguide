# Agent 3 — CellGuide efficiency + specificity scoring spec

Implementation: `agent3_metric_construction/guide_scoring.py`. Built from the structured literature extraction in `agent2_literature_summarization/output/SUMMARY.md` (Agent 2 output) and the plan's own §4.4 formula.

## Formula

```
combined(g, c) = renormalized_sum(w_seq * sequence_efficacy(g), w_atac * accessibility(g, c), w_spec * specificity(g))
recommended_score(g, c) = sequence_efficacy(g)   # what to actually rank by — see below
```

Linear and transparent by design (plan §4.4: "Start with transparent weights ... compare against sequence-only"; plan §2: "Keep the biological scoring functions inspectable"). Each term is independently inspectable and swappable for a trained model later.

**Update after Agent 4/5**: real-data benchmarking (`agent4_benchmarking/output/REPORT.md`, n=199 Ito et al. guides) found `combined` underperforms `sequence_efficacy` alone (ρ=0.315 vs 0.441) — Ito et al. never linearly blend ATAC into a score; they gate on it (`passes_ito_thresholds()`). `recommended_score` is `sequence_efficacy`; check `passes_ito_rule` alongside it as the accessibility gate. `combined` remains for transparency/comparison, not as the value to rank by. `renormalized_sum` means weights are rescaled over whichever of the three components actually have data for a given guide — a component with no data is *excluded*, not guessed (see Components 2 and 3 below).

## Component 1 — `sequence_efficacy(g)` (on-target efficiency)

- **Preferred inputs**: `deepspcas9_score` (0-100, native DeepSpCas9 scale) and/or `chopchop_score` (0-1, native CHOPCHOP/Doench scale) — the two tools Ito et al. 2024 found most predictive on their own 205-gRNA T-cell dataset (`papers/ito_2024/structured_extraction.md`). When both are given, they're averaged after normalizing to `[0,1]`.
- **Fallback (no external scorer available)**: a transparent sequence heuristic — GC content (optimal ~50%, per `wang_2019_deephf`) and a poly-T penalty (U6 promoter terminates transcription on `TTTT+`, only applied when `delivery` indicates vector expression — see Component 2). This is the "GC content, motif" heuristic requested in `CLAUDE.md`. No separate seed-region GC term: it doubled-counted the (highly correlated, since the seed is a subset of the spacer) whole-spacer GC term and reused an unvalidated curve for a different window — dropped rather than kept as uncalibrated confidence.
- **Not implemented, left pluggable**: DeepHF (`papers/wang_2019_deephf/`) — best Spearman 0.867 in its own lentiviral HEK293T assay, but trained on synthetic integrated targets, not endogenous primary-cell loci; treat as one more optional external score to wire in, not a ready-made drop-in.
- **Caveat baked into the design**: `riesenberg2025_synthetic_grna` shows indel% can *underestimate* true cutting activity — this score is a ranking signal, not a calibrated probability of editing.

## Component 2 — `accessibility(g, c)` (cell context)

- **Input**: `atac_signal` — median ATAC-seq read count/signal over the guide's target window in the target cell type (plan §3.1/§4.1: GSE221788 for T cells, GSE137647 for K562).
- **Normalization**: `min(1, atac_signal / 0.1)`, reusing Ito et al.'s own empirical ATAC ≥ 0.1 cutoff as the point where the term saturates at 1.0.
- **Returns `None` (excluded from `combined`, not guessed) when no ATAC data is supplied**, so a missing accessibility measurement doesn't silently masquerade as "inaccessible" (it used to return `0`, which — combined with `specificity`'s old default of `1.0` for the opposite case — meant two missing-data situations were guessed in opposite directions; both now propagate as "unknown" instead).
- **`delivery` gate**: `GuideScoreInputs.delivery` (`"rnp"` / `"lentiviral"` / `"vector"` / `"stable"` / `None`) — when it indicates lentiviral/vector/stable expression, `accessibility` returns `None` unconditionally, *even if `atac_signal` is given*. This encodes the caveat below as an actual guard instead of prose that nothing enforces.
- **Important caveat, from `wang_2019_deephf`**: fine-tuning with DNase-I accessibility did *not* improve their model — accessibility only mattered in Ito et al.'s **transient RNP** delivery, not Wang's lentiviral-integration assay. `schep2024_chromatin_drugs` independently corroborates the RNP-context effect (chromatin state also shifts NHEJ:MMEJ repair balance).

## Component 3 — `specificity(g)` (off-target / inverse risk)

- **Gap this fills**: Ito et al. 2024 — the plan's primary ground-truth paper — reports **no off-target data at all** (`papers/ito_2024/structured_extraction.md`). The specificity term must come entirely from other sources.
- **Preferred inputs (recommended, not yet wired to real data)**: `external_specificity_score` from crispAI (`agent1_literature_search/output/related/ozden2024_crispai_uncertainty/`) or CrisprBERT (`agent1_literature_search/output/related/sari2025_crisprbert/`) — both trained on the same CHANGE-seq 110-sgRNA/13-locus **primary human T-cell** off-target dataset that overlaps Ito et al.'s cell system, making them the closest-context specificity predictors available.
- **Fallback**: a CFD (Cutting Frequency Determination)-style aggregate over an *enumerated* off-target site list (`OffTargetSite(mismatches, mismatch_positions, cfd_pam_score)`), using the standard Doench et al. 2016 position-weight table (PAM-proximal mismatches penalized far more than PAM-distal). An empty enumerated list (a search was run and found nothing) legitimately scores `1.0`. Off-target sites themselves are not enumerated by this module — plug in an external candidate generator (e.g. Cas-OFFinder, or `agent1_literature_search/output/related/schmidt2025_guidescan2/` GuideScan2, which also builds low-off-target guide libraries directly).
- **Returns `None` (excluded from `combined`) when *neither* an external score *nor* an off-target list was supplied** — i.e. specificity was never actually assessed. This used to default to `1.0` ("perfectly safe"), which rewarded guides nobody had checked; every row in the old demo output had `specificity=1.0` purely from this default, silently padding 30% of the weight budget with zero real information.
- **Not modeled**: `ursch2024_tcell_genomic_safety`'s finding that T-cell **activation state** (not sequence) drives large deletions/translocations/aneuploidy — a genomic-safety signal orthogonal to sequence-based off-target prediction. Flagged as a known gap, not folded into `specificity()`.

## Default weights

```python
GuideScoreWeights(w_seq=0.4, w_atac=0.3, w_spec=0.3)
```

Equal-ish split favoring on-target slightly, as an arbitrary transparent starting point — **not fit to data**, and used only for `combined` (see "Formula" above for why `recommended_score`, not `combined`, is what to actually rank by).

## `passes_ito_thresholds(...)`

A separate, non-weighted rule-based classifier that directly reproduces Ito et al.'s validated empirical rule on the tools' **native scales** (not the normalized `[0,1]` scores used elsewhere): `DeepSpCas9 >= 60 AND CHOPCHOP >= 0.3 AND ATAC >= 0.1`. Returns `False` (not a guess) whenever any of the three raw inputs is missing. This is the accessibility *gate* to check alongside `recommended_score` — real-data precision/recall against >50% indel: precision=0.862, recall=0.287 (n=199, see `agent4_benchmarking/output/REPORT.md`) — a high-precision, low-recall filter, not a general ranker on its own.

## Known limitations / not yet implemented

- No real genome, ATAC bigWig, or off-target enumeration data is wired into this module yet — it is a scoring *library* with well-defined inputs, not an end-to-end pipeline. Workstream A (`docs/CellGuide_AI_Hackathon_Plan.pdf` §5) still needs to build the feature extractor that turns raw ATAC/genome files into the `atac_signal` / `OffTargetSite` inputs this module expects.
- No CRISPRi/CRISPRa scoring — `agent2_literature_summarization/output/SUMMARY.md` notes that of the papers pulled so far, only the more recent CRISPRi/CRISPRa-focused search pass (see `agent1_literature_search/output/related/INDEX.md`) covers this; not yet folded into the scoring formula, consistent with the plan's SpCas9-knockout-oriented MVP scope.
- Repair-outcome/frameshift prediction (v2 roadmap stage) is out of scope for this module; see `agent1_literature_search/output/related/zhang2024_deepindel/` and `agent1_literature_search/output/related/seale2025_xcrisp/` as starting points when that stage begins.
- `combined`'s additive structure still can't represent the on-target/off-target trade-off `wang_2019_deephf` reports (higher on-target activity correlating with higher off-target risk) — a sum structurally can't express that, regardless of weights. Not an issue for `recommended_score` (sequence-only), but worth flagging if `combined` is used for anything.
- Xu et al. 2018 (core corpus) reports cross-cell-type editing efficiency is consistent (<30% variance) under efficient RNP delivery, and attributes earlier reports of larger (4-10x) cross-cell-type differences to delivery artifact rather than a biological chromatin effect — this is in tension with the cell-context premise this whole module is built on and is not yet addressed here (see `agent5_confidence_assessment/output/CONFIDENCE_REPORT.md` finding A).
- **Correction (Agent 5 caught this)**: an earlier version of this file said the real n=199 benchmark showed accessibility "has not demonstrated predictive value," based on a *marginal* ATAC-vs-indel correlation (ρ=0.084, n.s.) and an F1 comparison. Both were the wrong test. Ito et al.'s actual claim is conditional — accessibility predicts efficiency *among guides with above-median sequence scores*, not marginally — and F1 mechanically penalizes any added AND-gate regardless of whether it's useful, when the gate is a deliberate high-precision/low-recall filter (which SPEC already said, two lines up). Tested correctly (`agent4_benchmarking/interaction_effect_check.py`), the conditional effect reproduces: ρ=0.232, p=0.008 on the above-median subset (n=131), and the gate's precision does rise (0.741→0.862) as designed. **Honest current state: accessibility has real conditional predictive value that the marginal test missed — but that conditional signal isn't yet folded into `recommended_score` or `combined` correctly**, which is why `recommended_score` staying sequence-only is a reasonable default but not the final word. The underlying ATAC measurement is also unstable across replicates (`agent4_benchmarking/output/REPLICATE_SENSITIVITY_REPORT.md`), which is a real reason for caution independent of this correction.
- `specificity` has been unevaluated (returns `None`, excluded from `combined`) for every guide in the real benchmark so far — no off-target data source has been wired in for any of the 199 Ito et al. guides, so `combined_score`'s advertised 3-way weight split is currently a 2-way split in practice (see the "Effective weights" note in `agent4_benchmarking/output/REPORT.md`).
- Two follow-up attempts to strengthen the motif/accessibility story both came back negative (`agent4_benchmarking/output/MOTIF_AND_ACCESSIBILITY_CHECKS.md`): (1) `sequence_motif_score()` (our own GC+poly-T heuristic, forced instead of DeepSpCas9/CHOPCHOP) has no real signal on its own (ρ=0.043, p=0.544) — essentially all of `sequence_efficacy`'s predictive power on real data comes from the two external tools, not this module's own sequence logic; (2) averaging both ATAC replicates (instead of using one) still doesn't produce a statistically significant accessibility signal (ρ=0.062, p=0.386) — the replicate disagreement isn't simple noise that cancels out. Neither the sequence-motif fallback nor the accessibility term has demonstrated real predictive value on this benchmark independent of the two external on-target tools.
