# Agent 5 — Confidence assessment (skeptical review)

Scope: Agent 3's `guide_scoring.py` + `SPEC.md`, Agent 4's `output/results.csv` (n=199) and `REPORT.md`, against `papers/ito_2024/` (incl. the raw `table_s1_205_gRNAs.csv`), `papers/wang_2019_deephf/`, `papers/xu_2018/`.

## Overall take

**No gene in this benchmark earns "high" confidence, and that is not a hedge — it follows from four findings that the existing reports do not state.**

Agent 3 deserves credit for real fixes: `None`-propagation instead of guessing, the delivery gate on accessibility and poly-T, dropping the double-counted seed-GC term, and demoting `combined` after the benchmark contradicted it. Those are correct responses to a prior review. But the SPEC's remaining caveats are **noted and then ignored** — none of them is reflected in a number anyone reports. Specifically:

**1. The specificity component was never evaluated. At all.** The `specificity` column is empty in all 199 rows of `results.csv`. So `combined` is a two-component score (I verified: AIRE = (0.4×0.61391 + 0.3×1.0)/0.7 = 0.77938, matching to 15 digits). Both `SPEC.md` and `REPORT.md` print "weights: w_seq=0.4, w_atac=0.3, w_spec=0.3" as though three components were in play; the effective weights are 0.571/0.429. **30% of the advertised weight budget carries zero information, and one third of the metric has never been tested against anything.** Since specificity is what makes a guide *safe* rather than merely *effective*, no guide recommendation from this pipeline is currently validated for its most safety-relevant property.

**2. The benchmark is in-sample, and the report presents it as validation.** Ito et al. tuned `DeepSpCas9≥60 AND CHOPCHOP≥0.3 AND ATAC≥0.1` *on these exact 205 guides*, and selected DeepSpCas9 and CHOPCHOP as the best 2 of 13 tools *on this same dataset*. Agent 4 then evaluates those thresholds and those two tools on 199 of those guides and reports precision=0.862 and ρ=0.441. These are resubstitution numbers inflated by threshold tuning and winner's-curse tool selection. `REPORT.md` states them without qualification. There is no held-out set anywhere in the pipeline.

**3. Agent 4 silently chose one of two ATAC replicates, and the headline result depends on that choice.** `table_s1_205_gRNAs.csv` contains **two** ATAC columns — `atac_seq_GSM6896554` and `atac_seq_GSM7256892`. Agent 4 used only the first; nothing documents this. The two disagree badly. Of 13 gate-passing guides I checked, **11 would fail `ATAC≥0.1` under the other replicate**:

| Gene | GSM6896554 (used) | GSM7256892 | Gate under rep 2 |
|---|---|---|---|
| AIRE | 0.163 | 0.032 | FAIL |
| FURIN | 0.147 | 0.0426 | FAIL |
| GATA6 | 0.132 | 0.0213 | FAIL |
| HIVEP3 | 0.116 | 0.0853 | FAIL |
| PRDM1 | 0.108 | 0.0213 | FAIL |
| RARG | 0.124 | 0.032 | FAIL |
| SETDB1 | 0.101 / 0.124 | **0.0** | FAIL |
| ZBTB16 | 0.136 | 0.0426 | FAIL |
| ZNF683 | 0.101 | **0.0** | FAIL |
| ZNF831 | 0.112 | 0.032 | FAIL |
| TNF | 0.155 | 0.107 | pass |
| ZNF469 | 0.147 | 0.160 | pass |

SETDB1 and ZNF683 read **exactly zero** in replicate 2 while editing at 66.5% and 73%. The replicates are also on visibly different scales (rep 2 systematically lower, many zeros), which means **the 0.1 cutoff is in arbitrary units of one specific library**. That is fatal for the plan's intended cross-context use: `table_s2` gives K562 ATAC up to 15.03 versus T-cell values up to 1.13, a ~10× scale difference. Applying a shared 0.1 threshold across two differently-normalized datasets is not a biological rule, it is a units error waiting to happen.

**4. The cell-context claim — the entire point of CellGuide — is untested, and where it can be tested it mostly hurts.** `REPORT.md` ends with "No cell_type column — skipping T-cell-open vs K562-open panel check." The `cell_type` field is null in all 199 rows. Yet `papers/ito_2024/table_s2_tcell_vs_k562_panel.csv` **exists on disk**. It was not used. It also contains no indel data, only ATAC — so even if run, it could only show that the ATAC input differs between cell types, which is circular (that is the input, not the outcome). **The cross-context result cannot be validated with any data currently in this repo, and nobody has said so.**

Worse, I isolated the ATAC gate's marginal contribution, which Agent 4 never computed. Reconstructing the 2×2 by hand (reproducing their TP=25/FP=4 exactly, which validates the enumeration):

| Rule | Precision | Recall | F1 |
|---|---|---|---|
| Base rate (any guide) | 0.437 | 1.00 | — |
| Sequence gates only (DeepSpCas9≥60 AND CHOPCHOP≥0.3) | **0.741** | **0.494** | **0.593** |
| Full Ito rule (+ ATAC≥0.1) | 0.862 | 0.287 | 0.431 |

Adding the accessibility gate **cuts F1 from 0.593 to 0.431** and nearly halves recall, buying 12 precision points by discarding 18 guides that edited >50%. Of the 29 guides ATAC vetoes, 18 (62%) actually worked. ATAC contributes only ~28% of the total lift over base rate; sequence contributes ~72%. Combined with finding 3 (that lift is replicate-dependent), **the cell-context premise is currently supported by a weak, unstable, in-sample effect** — while `accessibility` alone correlates at ρ=0.084, p=0.239, i.e. not at all.

**Bottom line: as validated, the deliverable is a sequence-only score.** `recommended_score` *is* `sequence_efficacy`; `combined` underperforms it; the accessibility gate reduces F1; specificity is empty. Agent 3's demotion of `combined` was the honest call, but its logical consequence — that CellGuide's differentiator has not yet demonstrated value on its own benchmark — is not stated anywhere in Agents 3 or 4's outputs. It should be, prominently.

---

## Conflicting evidence between cited papers

- **Xu et al. 2018 vs. the whole premise (flagged in SPEC line 57, still unaddressed).** Xu reports cross-cell-type editing efficiency is consistent (<30% variance) under efficient RNP delivery, and attributes prior 4–10× differences to *delivery artifact, not chromatin*. Ito's design is RNP. If Xu is right, the cross-context effect CellGuide models may be largely a delivery-quality confounder. The SPEC points at this document instead of resolving it; nothing in the code or benchmark addresses it, and neither electroporation efficiency nor viability is available as a covariate.
- **Wang 2019 vs. Ito 2024 on accessibility.** DNase-I fine-tuning did not help Wang's lentiviral model; ATAC gating helps (weakly) in Ito's RNP setting. Agent 3 handled this correctly with the `delivery` gate — genuinely good. But **that gate has zero test coverage**: every row in `results.csv` is RNP, so the lentiviral/vector/stable branch has never been executed against data.
- **Wang 2019's on-target/off-target trade-off vs. the additive `combined`.** A sum cannot represent "higher on-target activity → higher off-target risk." SPEC admits this. It is moot today only because specificity is empty — but it means `combined` will be structurally wrong the moment specificity is wired in.
- **Riesenberg 2025 vs. the ground truth itself.** indel% can *underestimate* true cutting. The benchmark's dependent variable is therefore biased, and the >50% label boundary inherits that bias.

## Weak assumptions

- **Untuned weights presented as a result.** 0.4/0.3/0.3 is explicitly "not fit to data," yet `REPORT.md` reports ρ for `combined` as if it characterized the approach rather than one arbitrary point in weight space.
- **Better scores were available and unused.** `table_s1_205_gRNAs.csv` — the file Agent 4 parsed — contains `deephf_u6`, `deephf_t7`, `azimuth2`, `crispick`, `vbc`, `sprout`, `idt_score`, `chop2016`, `chop_xu`, `chop_mm`, `crisprEdict_u6/t7`. SPEC says DeepHF is "not implemented, left pluggable"; the DeepHF scores were sitting in the input file. Agent 3 uses **2 of 13** available predictors.
- **Ground truth is one replicate, not the paper's own average.** Agent 4's `indel_pct` equals `indel_1st`, not the table's `indel_avg` column. For AIRE that is 91.0 vs 78.2 — a 13-point difference. Replicate columns (`indel_1st`…`indel_7th`) exist and were discarded, so no measurement noise is propagated and no guide is down-weighted for being noisy. Note also `indel_avg` has inconsistent denominators (13, 13, 9, 7 across the first four rows), so the ground-truth definition is genuinely ambiguous and undocumented.
- **The `1/(1+Σ)` CFD fallback is misdescribed.** `_CFD_POSITION_WEIGHTS` is position-only; the real Doench 2016 CFD table is per-position **and per-mismatch-identity** (rX:dY). The values 0.91→0.11 look like a stylized monotone ramp, not the published table. Calling it "the standard Doench et al. 2016 position-weight table" overstates it. Untested either way.
- **A provenance error in the specificity rationale.** SPEC and the docstring claim crispAI/CrisprBERT are trained on "the same CHANGE-seq 110-sgRNA/13-locus primary human T-cell dataset **that overlaps Ito et al.'s cell system**" / "that Ito's cohort comes from." That is false. CHANGE-seq's 110 sgRNAs and Ito's 110 genes are a coincidence of numbers; they are unrelated datasets that merely both use primary T cells. This conflation is currently the *entire* stated justification for the recommended specificity scorers.
- **Hard thresholds on noisy inputs.** KEAP1's best guide (93.5% indel) is vetoed at ATAC 0.0968 vs a 0.1 cutoff — 0.3% below, on a quantized (~0.00775 steps), replicate-unstable measurement. TIA1 loses a 65.5% guide at CHOPCHOP 0.28. ARID1A (93%), MSC (66%), TSC1, SUV39H1 lose guides to DeepSpCas9 near-misses of 0.7–1.6 points. No margin, no soft boundary, no uncertainty.
- **Internal inconsistency in the unused GC heuristic.** `gc_content()`'s docstring says optimal 40–60%, but `gc_content_score()` peaks sharply at exactly 50%, scoring 40% GC at 0.667 — penalizing a value inside its own stated optimum. Never exercised here (all 199 rows have external scores), so it is entirely untested.
- **Averaging DeepSpCas9/100 with raw CHOPCHOP** assumes two differently-distributed scores are calibrated to each other. They are not.

## Context mismatches

- **Delivery**: thresholds and the ATAC effect are RNP-specific. Correctly gated in code, never tested outside RNP.
- **Cell type**: 199/199 rows are primary human CD8+ T cells; `cell_type` is null throughout. Ito also ran K562 and hMSC-BM; neither is in the benchmark. Any use outside stimulated primary CD8+ T cells is pure extrapolation.
- **Model training contexts**: DeepSpCas9 and CHOPCHOP/Doench-2014 derive from immortalized-line and integrated-library screens; DeepHF from HEK293T synthetic integrated targets; the CFD weights from a HEK293T mismatch screen; crispAI/CrisprBERT from CHANGE-seq *in vitro* cleavage. Every component is transferred from a different context to endogenous primary-T-cell loci.
- **ATAC units**: as above, the 0.1 cutoff is not portable across libraries or cell types.

## Confounders not modeled at all

- **Locus-level effects independent of accessibility.** CD83's two guides share ATAC 0.062 and near-identical sequence_efficacy (0.281 vs 0.268) yet edit at 88.75% and 0.0%. Nothing in the score can express this. Conversely KLF2 (ATAC 0.79–3.4, wide open) gives 0–0.5% indel on four of six guides, and PRDM2's ATAC 6.32 — the dataset maximum — gives 1.0%.
- **Pseudo-replication.** 199 guides across ~110 genes; ATAC is a locus-level covariate shared by all guides at a gene (TSC1's 10 guides span 0.0155–0.124; MTA2's four span 0.062–0.0852). Spearman treats these as independent, so the reported p-values are anticonservative; effective n for the ATAC term is nearer 110 than 199.
- **Zero-inflation.** ~30 guides read exactly 0.0. ICE/Sanger failures, primer dropout and true non-editing are indistinguishable, and are pooled into both the correlation and the >50% classifier.
- **Donor and amplicon effects.** Primary T cells from multiple donors; per-amplicon PCR/Sanger quality varies. Neither is available or modeled.
- **Ursch 2024**: T-cell *activation state* drives large deletions, translocations and aneuploidy independent of sequence — a genomic-safety axis orthogonal to CFD-style off-target scoring. Flagged in SPEC as a known gap; still entirely outside the score.
- **Undocumented attrition**: 205 → 199 guides. Six dropped with no record of which or why (one is PRDM1 `CCACACAAGAAGTTCCTGGT`). If dropped for missing indel, that is potentially informative missingness.
- **Data hygiene**: `CDKN2C ` (trailing space) is treated as a separate gene from `CDKN2C`, creating a phantom locus. No gene-name normalization exists anywhere in the pipeline.

## What would actually raise confidence

1. Populate specificity (GuideScan2/Cas-OFFinder enumeration + crispAI) so the third of the metric that has never been tested can be tested — and re-derive weights afterwards, since the additive form cannot express Wang's trade-off.
2. Report the sequence-only-gate baseline (P=0.741 / R=0.494 / F1=0.593) beside the full rule in `REPORT.md`. Right now the ATAC gate's negative contribution to F1 is invisible.
3. Use **both** ATAC replicates: report gate stability, or average/quantile-normalize them, and stop treating `ATAC≥0.1` as portable across libraries or cell types until it is renormalized.
4. Hold out a test set, or at minimum label every current figure as in-sample resubstitution.
5. Run the T-cell vs K562 panel using `table_s2` and be explicit that only the *input* differs by context — the indel outcomes needed to validate the cross-context claim are not in this repo and must be sourced.
6. Use `indel_avg` (or the replicate mean) with replicate spread as a weight, and document the choice.
7. Replace hard AND-gates with soft/margin-aware scoring; report ties and near-misses rather than silently vetoing.

---

## Per-gene assessments

Machine-readable equivalent: `confidence.json` (75 entries, one per gene in `results.csv`, covering all 199 guides). `cell_type` is `null` for every entry because Agent 4 emitted no cell-type column.

Confidence bands: **low** < 0.35 ≤ **medium** ≤ 0.60 < **high**. **No gene scores "high"** — the ceiling is set by three conditions that apply to every row: specificity never assessed, in-sample threshold tuning, and T-cell-only RNP data with no cross-context test.

Distribution: 47 low, 28 medium, 0 high.

### Highest confidence (0.50–0.52)
- **ZNF469** (0.52) — top sequence scores, 83% indel, and the only gate-passing guide checked whose ATAC agrees across both replicates (0.147 / 0.160).
- **SOCS1** (0.50) — clean discrimination (71% vs 0%) with accessibility high for both guides, so sequence did the separating; robust to replicate choice.
- **MAF** (0.50) — ATAC 0.364 (3.6× cutoff), 89% indel.

### Most damaging cases (≤ 0.20)
- **ZBTB16** (0.12) — passes all three gate components and gives **0.0% indel**. Single worst case against the claimed 0.862 precision; its ATAC pass also vanishes under replicate 2.
- **FOXO3** (0.12) — **95.5% indel**, among the highest in the dataset, rejected by all three components simultaneously.
- **PTEN** (0.18) — best-sampled locus after TSC1; edits >60% at eight of ten guides across ATAC 0.0155–0.116, producing **four** accessibility-driven false negatives (87.5%, 86%, 82.5%, 70%).
- **KLF2** (0.18) — six guides in wide-open chromatin (ATAC up to 3.4), four edit at 0–0.5%. The strongest single counterexample to the accessibility premise.
- **CD83** (0.15) — identical ATAC and near-identical sequence score; 88.75% vs 0.0% indel.
- **PRDM1** (0.15) — the rule's gate pass edits at 5% while a guide it rejects edits at 52.5%: prediction exactly inverted, at a gene Ito used for *prospective validation*.
- **GATA6** (0.15), **DPH1** (0.15), **DPH5** (0.15), **CDKN2C** (0.15), **DEK** (0.15), **DNAJC24** (0.15), **HDAC2** (0.15) — gate false positives, or loci where every working guide is filtered out, or where ATAC runs backwards against outcome.
- **CDKN2C ** (0.15) — not a real gene; a whitespace artifact.

### Notable genuine successes for the accessibility term
Worth recording, because they are the honest case *for* the component: **DUSP22** (DeepSpCas9 80.7 / CHOPCHOP 0.97 → 1.0% indel, correctly blocked), **SUV39H1** (75.6 / 0.76 → 1.0%), **RBM47** (69.9 / 0.76 → 0.0%), **ZFP41** (70.9 / 0.60 → 12%), **TOX2** (64.9 / 0.73 → 0.0%). These are real saves. There are 11 such saves against 18 ATAC-caused false negatives — which is precisely why the net F1 effect is negative.
