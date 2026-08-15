# Agent 5 — Confidence Assessment (skeptical review)

Reviewed: `agent3_metric_construction/{SPEC.md, guide_scoring.py}`, `agent4_benchmarking/output/` (`demo_results.csv`, `DEMO_REPORT.md`, `REPORT.md`, `CROSS_CONTEXT_REPORT.md`), `agent2_literature_summarization/output/SUMMARY.md`, `papers/`.

Results file under review: **`agent4_benchmarking/output/demo_results.csv`** — 4 rows, 2 genes × 2 cell types.

---

## Overall take

**The assigned results file is synthetic, and it showcases exactly the effect that Agent 4's real-data run failed to reproduce.**

`DEMO_REPORT.md` labels itself "DEMO — synthetic data, not real Ito et al. 2024 numbers", n=4, Spearman ρ=0.800, **p=0.2**. The indel% column in `demo_results.csv` is authored, not measured. Meanwhile `REPORT.md`, on 199 real guides, reports:

| Component | ρ vs real indel% | p |
|---|---|---|
| sequence_efficacy only | **0.441** | 7.0e-11 |
| accessibility only | **0.084** | **0.24 (n.s.)** |
| combined (0.4/0.3/0.3) | 0.315 | 5.7e-06 |

So on real data the accessibility term is **statistically indistinguishable from noise**, and adding it makes the score **worse than its own sequence component**. The demo file then presents a hand-built 88%→9% accessibility-driven swing as the headline result. Those two artifacts point in opposite directions, and only one of them contains real measurements.

To Agent 3's credit, `SPEC.md` is unusually honest — it flags the delivery-context problem, the untuned weights, and Ito's missing off-target data in prose. **The problem is that essentially none of those caveats are enforced in `guide_scoring.py`.** They are documented and then ignored by the combined score. Specifically:

1. **The delivery-context caveat is unenforceable.** SPEC.md says "Do not apply this accessibility term to stably-integrated/lentiviral delivery contexts without re-validating." `GuideScoreInputs` has **no delivery field**, and `score_guide()` has no guard. A user scoring a lentiviral library silently gets a 0.3-weighted term that Wang 2019 showed does not help in that context. A caveat that cannot fire is not a safeguard.

2. **30% of the weight budget is a dead constant.** `specificity()` falls back to `cfd_specificity([])`, which returns **1.0** when no off-target sites are supplied — and SPEC.md confirms no off-target enumeration is wired in. Every row in `demo_results.csv` has `specificity=1.0`. So the combined score is really `0.4·seq + 0.3·acc + 0.3`, contributing **zero discriminative information** while compressing the usable range to [0.3, 1.0]. Absence of off-target data is being scored as *perfect safety*.

3. **Missing-data conventions contradict each other in direction.** In the same module: missing ATAC → `0.0` (maximally pessimistic), missing off-target data → `1.0` (maximally optimistic), missing anything in `passes_ito_thresholds` → `False` (pessimistic). A guide with no off-target data is rewarded; a guide with no ATAC data is punished. Both are described as "not guessing." Both are guesses, in opposite directions.

4. **Additive linearity contradicts the source paper's own method.** Ito et al. never linearly blend ATAC; they use an **AND-gate** (`DeepSpCas9≥60 AND CHOPCHOP≥0.3 AND ATAC≥0.1`). Agent 4 measured that gate at precision 0.862 / recall 0.287 — a high-precision filter, not a ranker. Agent 3 implements the gate correctly but *separately*, then ships a linear blend as the primary score. Agent 4 explicitly recommends switching; that recommendation is unaddressed.

**Bottom line: no gene/guide in this results file rises above LOW confidence.** Not because the biology is implausible, but because the outcome column is fabricated, the specificity component is vacuous, the weights are unfit, and the combined score is empirically worse than a component it already contains.

---

## Conflicting evidence between cited papers

### A. Xu et al. 2018 vs the entire cell-context premise — **unaddressed in SPEC.md**
`papers/xu_2018/structured_extraction.md`: *"editing efficiency consistent across cell types (<30% variance) under efficient RNP delivery, **contradicting prior reports of 4–10× cross-cell-type differences**; the paper argues those earlier differences were largely a **delivery artifact, not biological**."* Same delivery method as Ito (RNP), overlapping cell types (primary T cells, MSC, iPSC).

This is a **core-corpus paper** that directly disputes the mechanism CellGuide is built on, and `SPEC.md` **never cites it**. The demo file asserts a ~10× same-guide cross-context swing — the precise magnitude Xu attributes to delivery artifact. This must be argued against explicitly, not omitted.

### B. Wang 2019 vs Ito 2024 on accessibility — flagged, not handled
DNase-I accessibility fine-tuning did *not* help Wang's lentiviral assay; it helped Ito's transient RNP. SPEC.md states this correctly. The code has no delivery input (see point 1 above). Agent 4's real-data ρ=0.084 (n.s.) means the effect is weak even *within* Ito's own RNP dataset.

### C. Wang 2019's on-target/off-target trade-off vs additive independence — **not flagged anywhere**
Agent 2's extraction: *"higher on-target activity raises off-target risk for WT-SpCas9."* A weighted **sum** structurally cannot represent a trade-off, and maximizing it preferentially selects high-efficacy guides that carry *higher* off-target risk. The formula's additivity is not just untuned, it is the wrong functional form given a cited finding.

### D. Sari 2025 vs a context-free specificity term — **internal inconsistency**
CrisprBERT *"argues cell-type-matched epigenomics improves [off-target] prediction."* Yet `specificity()` takes **no cell_type argument**. The metric is cell-context-aware for efficiency and context-blind for specificity, contradicting the paper it names as its preferred specificity source.

### E. Riesenberg 2025 vs the benchmark's ground truth
Indel% *underestimates* true cutting activity. Agent 4 regresses against indel%; every ρ in `REPORT.md` is against a known-biased proxy. Noted in SPEC.md, not propagated into any uncertainty estimate.

---

## Weak assumptions

- **Untuned weights (0.4/0.3/0.3)** — SPEC.md calls them "arbitrary"; Agent 4 showed they underperform sequence-only. Still shipped as default.
- **Fallback used where a better score existed.** `CROSS_CONTEXT_REPORT.md` seq_efficacy values (0.467, 0.733, 0.8, 0.867, 0.933) are all multiples of ~1/15 — the signature of the GC/motif *fallback*, not DeepSpCas9/CHOPCHOP. The real benchmark run had those tool scores for 199 guides, and sequence is the **only** component that actually correlates (ρ=0.441). The panel check ran the weakest available scorer. (Caveat: Table S1 and S2 are different guide sets, so tool scores may genuinely be unavailable for the panel — but this should be stated, not left implicit.)
- **Poly-T penalty is copied from the wrong delivery context.** `poly_t_penalty` docstring: "U6-promoter transcription terminates on TTTT+". Ito et al. use **synthetic gRNA in RNP** — there is no U6 promoter. A vector-expression rule is being applied to a chemically synthesized guide.
- **ATAC threshold 0.1 is Ito's pipeline-specific number**, applied to any ATAC input and transferred across GEO series (GSE221788 T cells vs GSE137647 K562) with no cross-dataset normalization. An apparent "context difference" can be a sequencing-depth/batch artifact.
- **Saturating ATAC transform destroys dynamic range.** `min(1, atac/0.1)` makes all open chromatin identical (1.0); the only resolution is *below* threshold, which is exactly where the signal is noisiest.
- **GC is double-counted.** `sequence_motif_score` = 0.4·spacer-GC + 0.4·seed-GC + 0.2·polyT, but the seed is a **subset** of the spacer — two correlated features at equal weight. Sub-weights also untuned.
- **`seed_gc_score` misapplies the 50%-optimum curve.** The "optimal ~50% GC" result is a whole-spacer finding; reusing that inverted-V for the seed region is an unjustified transfer.
- **CFD table is position-only.** Real CFD (Doench 2016) is **mismatch-identity-specific** (nucleotide-pair dependent), not just positional. The simplification is not listed among SPEC.md's limitations.
- **Cross-context 11/11 is near-circular.** Those genes were designated "T-cell-open"/"K562-open" *by the paper on the basis of chromatin accessibility*. Confirming ATAC is higher where the paper says chromatin is open tests the ATAC data, not the metric's predictive value — and the report itself concedes there is **no indel% ground truth** for the panel. 11/11 is not evidence of predictive skill.

---

## Context mismatches

| Dimension | Mismatch |
|---|---|
| **Delivery** | Accessibility validated for transient RNP only (Ito); contradicted under lentiviral integration (Wang 2019); Xu 2018 says delivery efficiency dominates. No delivery field in the model. |
| **Species/system** | DeepHF: HEK293T, **synthetic integrated targets**, not endogenous loci. Schep 2024: integrated reporters. Pallaseni/Seale: mESC. Zhang 2024: pooled. These are folded in as generic support for endogenous primary-cell scoring. |
| **Cell type granularity** | `cell_type="T"` is underspecified — naive vs stimulated CD8 have different ATAC landscapes. Ito used *stimulated* CD8+ T cells. |
| **Cell line genetics** | K562 is a near-triploid, rearranged CML line. Guides are designed against reference genome; Kumbara 2025 reports population variants alter on-target activity for **82.5%** of guides. |
| **Off-target source data** | crispAI/CrisprBERT trained on CHANGE-seq — a biochemical/cell-based off-target assay in a different experimental frame than Ito's endogenous indel readout. |
| **Demo vs real internal inconsistency** | For the *same* gene+context, `demo_results.csv` and `CROSS_CONTEXT_REPORT.md` disagree: GZMA seq_efficacy 0.661 vs 0.467; GZMA/K562 accessibility 0.20 vs 0.0; GATA1 seq_efficacy 0.61 vs 0.80; GATA1/T accessibility 0.30 vs 0.465. |

---

## Confounders not modeled at all

1. **Indel% ≠ functional knockout.** No frameshift/repair-outcome term. In-frame indels leave protein function intact (Pallaseni 2024, Zhang 2024, Seale 2025 all in corpus, all unused by the score).
2. **Essential-gene dropout / selection.** GATA1 is a lineage-survival dependency in K562; edited cells are selected against between editing and readout. No timepoint or essentiality term.
3. **Copy number / ploidy.** K562 near-triploid; GATA1 is X-linked. Indel% is per-allele-pool and unadjusted.
4. **T-cell activation state** (Ursch 2024) → large deletions, translocations, aneuploidy. SPEC.md explicitly flags this as "not modeled." It affects both the ATAC landscape *and* genomic safety, and it is the dominant safety signal in the corpus for the target cell type.
5. **Chromatin-dependent repair-pathway shift** (Schep 2024): chromatin state alters NHEJ:MMEJ balance, so chromatin changes *outcome spectrum*, not just cut rate — the score treats accessibility as a pure efficiency multiplier.
6. **ATAC batch/normalization effects** across GEO series.
7. **Assay noise floor & replication.** Ito measured in duplicate via Sanger+ICE. Demo values of 9% and 7% sit at/near the ICE detection floor. No replicate variance is propagated; no uncertainty is attached to any score, despite two corpus papers (Ozden 2024, Schmitz 2025) being *specifically about* calibrated uncertainty in guide selection.
8. **Reference-vs-actual genome mismatch** in the target cells.
9. **Multi-allele / multi-copy target site editing kinetics.**

---

## Per-guide confidence

Machine-readable: `confidence.json`.

| Gene | Cell type | Confidence | Numeric | Rationale |
|---|---|---|---|---|
| GZMA | T | low | **0.30** | The most favorable row — high ATAC, passes the Ito AND-gate, direction corroborated by the real-ATAC panel — but the 88% indel value is fabricated. Capped low because the only component that tracks real indel% (sequence) is diluted by an untuned accessibility weight and a constant specificity placeholder. |
| GZMA | K562 | low | **0.18** | Synthetic 9% indel at the ICE noise floor, and its accessibility (0.20) disagrees with the real-ATAC run's 0.0 for the same gene/context. It illustrates the mechanism the real benchmark most clearly failed to confirm (ATAC-only ρ=0.084, p=0.24). |
| GATA1 | K562 | low | **0.22** | Carries a specific unmodeled confounder: GATA1 is essential in K562, so indel% reflects survival selection as much as cutting. No essentiality, timepoint, or ploidy term; demo and real-ATAC components disagree for this exact gene. |
| GATA1 | T | low | **0.15** | Weakest row: fabricated low indel at the noise floor, accessibility off by >50% from the real-ATAC run (0.30 vs 0.465), and no corroborating real-data evidence of any kind. |

---

## What would actually raise confidence

1. **Re-run against `results.csv` (real, n=199), not `demo_results.csv`.** Retire the synthetic file from any results-facing role, or watermark it in-file — a CSV with no provenance column will be read as real.
2. **Fix the specificity term or drop its weight to zero.** Returning 1.0 for "no data" makes unmeasured guides look safest. Until off-target enumeration is wired in, `w_spec` should be 0 and the score renormalized, or specificity should return `None` and propagate.
3. **Make missing-data direction consistent and explicit** across accessibility / specificity / Ito-rule.
4. **Add a `delivery` field** and hard-gate the accessibility term to RNP contexts, per SPEC.md's own warning.
5. **Adopt Agent 4's recommendation**: sequence_efficacy *gated* by `passes_ito_thresholds()`, matching Ito's actual AND-gate method, instead of a linear blend that underperforms its own sequence component.
6. **Address Xu et al. 2018 head-on in SPEC.md** — either rebut the delivery-artifact explanation or scope CellGuide's claims to loci/contexts where Ito's effect survives it.
7. **Attach uncertainty per guide** (Ozden 2024 / Schmitz 2025 are already in the corpus for exactly this).
8. **Report a null/negative-control panel** — genes where accessibility predicts *no* difference — instead of only the two textbook cross-context examples.
