# Agent 5 — Confidence Assessment

Review of Agent 3's `guide_scoring.py` / `SPEC.md` and Agent 4's `results.csv` / `REPORT.md`
(n=199 guides, Ito et al. 2024).

---

## Overall skeptical take

**The benchmark does not test the thing this project exists to do, and the two conclusions
both agents drew from it are drawn from the wrong statistic.**

Agent 3's SPEC is unusually honest — it flags most of its own weaknesses in prose. But the
instruction was to check whether those flagged contradictions are *accounted for* or merely
*noted*. Mostly they are noted and then acted on incorrectly. Five findings, in order of
severity.

### A. The cell-context claim is entirely unvalidated. `cell_type` is null for all 199 rows.

CellGuide's premise is that guides should rank *differently in different cell types*. Agent 4's
`results.csv` has an empty `cell_type` column for every row, and REPORT.md closes with "No
cell_type column — skipping T-cell-open vs K562-open panel check." That skipped check **is the
project's thesis**. Everything benchmarked is a single context (primary human CD8+ T cells,
unlabeled).

Worse: the metric Agent 3 now recommends (`recommended_score = sequence_efficacy`) is a pure
function of the spacer sequence. It contains **zero cell-context information**. So the ρ=0.441
headline validates a sequence-only scorer — i.e. exactly the baseline the plan set out to beat.
As currently constituted the pipeline has validated the null hypothesis and adopted it.

The data to do better is partly present (`table_s2_tcell_vs_k562_panel.csv` has T-cell and K562
ATAC for 11 genes) but the per-cell-type indel ground truth exists only inside Figures 2I/2K of
the paper, not in any fetched table. That is a real blocker, and it should be stated as such
rather than silently skipped in a one-line footnote.

### B. Agent 4 measured the marginal correlation; Ito's claim was a conditional one. The "accessibility fails" conclusion does not follow.

Agent 4 reports `accessibility` ρ=0.084, p=0.239 and both agents treat this as evidence that
chromatin accessibility "has not demonstrated predictive value" (SPEC line 58), motivating the
switch to a sequence-only `recommended_score`.

But Ito et al. report the *same thing themselves*, in the paper, as a premise rather than a
refutation (fulltext L64):

> "the ATAC-seq score alone did not show a significant correlation with the efficiency of indel
> generation. **However**, high ATAC-seq scores were significantly associated with efficient
> indel formation **among gRNAs with above-median scores in CHOPCHOP or DeepSpCas9**."

Ito's claim is an **interaction effect**, conditional on sequence score. Agent 4 tested the
marginal effect, found it absent exactly as the paper predicts, and reported it as a negative
result. The interaction — the actual claim — was never tested.

Compounding this: Ito derived the ATAC≥0.1 cutoff *only within the DeepSpCas9≥60 subset*
(Figure 2D legend: "For (D), only gRNAs with the DeepSpCas9 score of ≥60 were used"). Agent 3's
`accessibility_score()` applies `min(1, atac/0.1)` to **every** guide unconditionally. A
conditionally-derived threshold is being extrapolated to the full population.

### C. Judging a precision filter by F1 is a mis-specified test.

REPORT.md's "Does the accessibility gate earn its keep?" concludes no, because F1 drops
0.593 → 0.431 when ATAC is added. But look at what actually moved:

| Rule | Precision | Recall |
|---|---|---|
| Sequence gates only | 0.741 | 0.494 |
| + ATAC≥0.1 | **0.862** | 0.287 |

Precision went **up**, which is what Ito designed the gate to do and what SPEC itself calls it
("a high-precision, low-recall filter, not a general ranker"). *Any* additional AND-condition
mechanically reduces recall, so F1 will almost always fall — F1 cannot distinguish a good filter
from a bad one here. The replicate check makes this sharper: on GSM7256892 precision hits 1.000.

So the honest statement is not "accessibility failed." It is **"accessibility was never
correctly evaluated in either direction."** Both agents converged on a confident conclusion
(drop the project's differentiator) from a test that cannot support it. That is the single
most consequential error in the pipeline.

### D. The benchmark is in-sample. The reported gate performance is optimistically biased.

Ito derived the thresholds 60 / 0.3 / 0.1 **from these exact 205 guides** (Figures 2C–2E). Agent
4 then evaluates the same rule on the same 199 guides and reports precision=0.862 as validation.
This is training-set evaluation, not validation, and no caveat appears in REPORT.md.

The genuinely held-out set is Ito's 10 prospectively designed guides (DNMT3A, PDCD1, PRDM1,
TGFBR2, MYC), which they report all worked. Confirmation that these are absent: the DNMT3A rows
in `results.csv` are 19%, 0%, 0%, and the PRDM1 rows include a full-gate-passing guide at 5%
indel. Those are the discovery-set guides, not the validated ones. The one true out-of-sample
test available was not run.

### E. Better on-target scores were sitting unused in the ground-truth file.

`papers/ito_2024/table_s1_205_gRNAs.csv` ships per-guide `deephf_u6`, `deephf_t7`, `azimuth2`,
`crispick`, `vbc`, `sprout`, `idt_score`, `chop2016`, `chop_xu`, `chop_mm`, `crisprEdict_u6/t7`.
SPEC describes DeepHF as "not implemented, left pluggable" — but DeepHF scores are already in the
file Agent 4 reads. The metric uses 2 of ~13 available predictors and never benchmarks the rest,
so the ρ=0.441 ceiling is self-imposed and untested against readily available alternatives.

(One assumption I checked that **holds**: `chopchop_score` is correctly mapped to the `chop2014`
column — the paper specifies "CHOPCHOP (Doench 2014)". Good.)

---

## Additional weak assumptions, context mismatches, and confounders

**ATAC is quantized read counts; the 0.1 threshold is applied below the measurement's resolution.**
ATAC values fall on a lattice of ~0.00775 (0.00775, 0.0155, 0.0232, 0.031, 0.0387, …), i.e. Ito's
"median read count" in units of one read. Guides near the cutoff are separated by 1–2 reads —
Poisson noise. Concretely: the best KEAP1 guide (**93.5% indel**) fails the gate at ATAC=0.0968
vs a 0.1 cutoff, while ZNF683 passes at 0.101. That is a one-read difference deciding a
recommendation.

**The 0.1 cutoff does not transfer between ATAC datasets — which breaks cross-cell-type use.**
Per-guide values differ 2–5x between the two CAR-T replicates (AIRE 0.163 vs 0.032; ARID1A 0.438
vs 0.181; BACH2 0.132 vs 0.299 — inverted). Rank correlation may survive but absolute scale does
not, and the gate is absolute. Applying `atac_signal >= 0.1` to a *new cell type's* ATAC data —
the entire point of CellGuide — requires a renormalization nobody has defined. Agent 4's replicate
report shows the cost: TP falls 25 → 12 on the second replicate.

**Accessibility saturates exactly where it fails most.** `min(1, atac/0.1)` maps everything above
0.1 to 1.0. The largest counterexamples all live there: PRDM2 ATAC **6.32** → 1% indel; ID2 ATAC
2.39 → 0%; KLF2 ATAC 3.4 → 0% (all six KLF2 guides are wide open, half produced ~0% editing);
SOCS1 ATAC 2.04 → 0%; RUNX3 ATAC 1.41 → 0%. The normalization discards the only information that
would flag these.

**Delivery gating is correct but inert here.** Agent 3's `delivery` guard (accessibility and
poly-T disabled for lentiviral/vector/stable) is a genuine, well-implemented fix for the Wang
2019 vs Ito 2024 contradiction. But `results.csv` has no `delivery` column, so every guide falls
through as `None` → RNP-like. Correct for Ito, but the guard is untested and any downstream
consumer feeding vector-delivered guides will silently get the default.

**Xu et al. 2018 contradicts the premise and is still unaddressed.** Xu reports cross-cell-type
editing efficiency is consistent (<30% variance) under efficient RNP delivery, attributing
reported 4–10x differences to delivery artifact. SPEC line 57 acknowledges this and defers to
*this document*. It remains unresolved — and given finding A (no cross-context test was run),
the pipeline currently has no evidence against Xu's position.

**Confounders not modeled at all:**
- **Locus-level effects dominate at several genes.** DUSP22: all 5 guides fail (1.0–17.5%)
  including one at DeepSpCas9 80.7 / CHOPCHOP 0.97. TSC1: 10 guides, DeepSpCas9 clustered 59–72,
  outcomes 0–74.5%. TOX2: 4 of 6 near zero. Copy number, essentiality/dropout, amplicon and ICE
  performance are all unrepresented in the score.
- **Zero-indel ambiguity.** Many rows are exactly 0.0. Assay/amplicon failure is
  indistinguishable from true biological inefficiency, and Riesenberg 2025 (cited in SPEC) warns
  indel% *underestimates* cutting. Zeros are treated as ground truth anyway.
- **Ground-truth column choice is an unexamined analytic degree of freedom.** The source table
  carries both `indel_avg` and `indel_1st…7th`. Agent 4 uses `indel_1st` (which is in fact the
  replicate mean). `indel_avg` is a substantially different quantity (AIRE 78.2 vs 91.0; CD83
  60.5 vs 88.75). The choice is undocumented and unjustified in REPORT.md.
- **Single donor cohort, one species, one Cas9 variant (WT SpCas9), CD8+ T cells only.** No
  variance component for donor, and Ursch 2024's finding that T-cell *activation state* drives
  large deletions/translocations is acknowledged in SPEC but modeled nowhere.
- **205 → 199 guides.** Six guides are dropped with no explanation in REPORT.md.

**Specificity is 100% absent, not merely weak.** `specificity` is null for all 199 rows. The
advertised 0.4/0.3/0.3 split is really 0.571/0.429 over two components (REPORT.md does disclose
this — credit where due). But the consequence is that **no guide in this pipeline has any
off-target assessment whatsoever**, and Ito et al. supply none. Any recommendation here is an
efficiency recommendation only and must not be presented as a safety-aware one.

**Data hygiene:** `CDKN2C ` (trailing whitespace) is a phantom 75th gene. Any per-gene grouping
downstream — Agent 6's ranking, Agent 7's provenance — is silently wrong.

---

## What would actually raise confidence

1. Test the **interaction**, not the marginal: Spearman(accessibility, indel) *within* the
   DeepSpCas9≥60 stratum, and the 4-group comparison of Ito's Figure 2B. This is the paper's real
   claim and is computable from data already on disk.
2. Judge the gate on **precision / enrichment**, not F1, and report the base rate.
3. Extract per-cell-type indel for the 11 Table S2 genes and run the T-cell vs K562 check, or
   state plainly that the core claim is untestable with current data.
4. Convert ATAC to a **within-dataset percentile** before thresholding, so the cutoff transfers
   across ATAC runs and cell types.
5. Benchmark the ~11 unused predictors already in Table S1 before accepting ρ=0.441 as a ceiling.
6. Strip whitespace on gene keys; document the 205→199 drop; justify the indel column choice.

---

## Confidence summary

Distribution over 75 gene entries: **high 6 · medium 21 · low 48.**

No gene exceeds 0.70. The ceiling is imposed by four issues that apply to every row: no
off-target data anywhere, in-sample threshold evaluation, no cell-context validation, and a
single unreplicated cell type/donor. Most genes are `low` because of specific local failures —
rank inversions, gate false positives at 0% indel (ZBTB16, PRDM1), or accessibility running
opposite to outcome (KLF2, PRDM2, ID2, FOXO1, SELL, RUNX3).

The handful of `high` entries (ZNF469, ARID1A, MAF, HIVEP3, ZNF683, TNF) are genes where sequence
scores and measured indel agree strongly. Note that all but ARID1A and TNF are single guides, and
their agreement is with the **sequence-only** component — they are evidence that DeepSpCas9 works
in T cells, not evidence that CellGuide's cell-context contribution works.

Per-gene detail: `confidence.json`.
