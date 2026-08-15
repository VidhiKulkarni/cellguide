# CellGuide AI — Agent Design Notes

Working notes on how the CellGuide agent differentiates from existing tools, and what
the hackathon plan is currently missing. Companion to `CellGuide_AI_Hackathon_Plan.pdf`.

Status: analysis / not yet validated against data. Items marked **[VERIFY]** are
assumptions that need checking against the primary sources before they go on a slide.

---

## 1. What we are actually competing with

"An agent" is not a moat. Three different competitors need three different answers.

### Claude Code / Codex (general coding agents)

Given the hackathon plan, a general coding agent can write the enumerator, pull the
bigWigs, and fit the ranker — probably in a day. So *"can it code the pipeline"* is not
the differentiator, and any agent whose value is prompt + tool wiring gets replicated in
a weekend.

What a general agent structurally cannot do is **know whether its answer is right**. It
produces a well-formatted ranked table with fabricated confidence and no way to signal
that it is wrong. No ground truth, no calibration, no held-out set, no memory of what
failed last time.

### Benchling

Wins on **distribution, not prediction**. It is where the scientist already works —
registry, inventory, workflows, the order form. We will not out-ELN Benchling and should
not try.

But its guide design is sequence-based on-target scoring (Doench/Azimuth lineage) plus
CFD/MIT-style off-target — **cell-context-blind by construction**. It cannot return a
different ranking for K562 vs primary T cells for the same gene. That is not a feature
gap we are exploiting cleverly; it is a structural property of the score.

**[VERIFY]** Benchling's current scoring algorithms and AI feature set. This assessment
is from knowledge with a May 2026 cutoff and their product moves.

### CRISPick / CHOPCHOP / DeepSpCas9 / DeepHF (scientific incumbents)

Strong on sequence, and that is the axis *not* to fight on. Consume them as a feature.

### Resulting position

Not a competitor to any of them — **a reranking layer that takes their candidates and
conditions on cell state.** The plan already gestures at this (Benchling for generation,
CellGuide for cell-aware reranking). Lean into it.

---

## 2. Moat ladder

| Layer | Time to replicate | Real moat? |
|---|---|---|
| Prompt / persona / "domain expert agent" | 1 day | No |
| MCP wiring to Benchling, GEO, literature | ~2 weeks | Barely |
| Harmonized coordinate-consistent data substrate | 2–3 months | Yes |
| Calibrated scoring + falsification harness | Months; needs the above | Yes |
| Wet-lab feedback loop that updates calibration | Years | The only durable one |

Everything above the line is what a judge sees. Everything below is what makes it a
product. For the weekend: build the top, and *demonstrate* the bottom is possible.

---

## 3. Gaps in the current plan

### 3.1 The cross-context panel is confounded with gene identity — highest priority

T-cell-open panel: GZMA, GZMB, CD3D, CD3G, CD28. K562-open panel: GATA1, CD33, HBB,
HBE1, TFR2. Those are immune genes vs erythroid genes.

A model that learns nothing about chromatin — that only memorizes "immune gene → higher
in T cells" — scores **100% on cross-context direction accuracy**. The headline metric is
passable by a lookup table.

Two fixes, both cheap:

- **ATAC label-swap ablation.** Score every guide with the *wrong* cell type's ATAC
  track. If performance does not collapse, the signal is not chromatin. Roughly twenty
  lines of code, and the most convincing slide available.
- **Within-guide paired analysis.** Restrict to guides measured in *both* contexts and
  ask whether the ATAC *delta* predicts the editing *delta*. Gene identity cancels out.

**Gating question (do this first):** how many guides in Ito et al. have measurements in
both T cells and K562? If under ~20, H3 may not be testable this weekend, and we need to
know that Friday night rather than Sunday morning.

### 3.2 Precision@3 is likely undefined for most genes

205 guides / 110 genes ≈ 1.9 guides per gene. Cannot take the top 3 of 2.

**[VERIFY]** the per-gene guide-count distribution before committing to this metric. May
need top-1-of-2 or a paired-comparison accuracy instead.

### 3.3 Bulk ATAC at the cut site is the naive feature

Cas9 is obstructed by **nucleosomes specifically** — Horlbeck 2016 and Isaac 2016 both
show cutting drops sharply at nucleosome dyads and recovers in linker DNA, at ~10 bp
resolution. Bulk accessibility is a coarse proxy.

If paired-end ATAC fragments are available, **fragment-length deconvolution
(NucleoATAC-style) for sub-nucleosomal signal at the protospacer** is a materially better
feature — and is exactly the kind of thing that distinguishes a domain agent from a
general one.

Also: raw bigWig signal is not comparable across GEO samples with different sequencing
depth and normalization. Rank-within-sample or quantile-normalize, or batch effect will
masquerade as biology.

### 3.4 Missing cell-specific features that are known to matter

- **Repair pathway state.** K562 is a fast-cycling cancer line; primary T cells require
  activation and have a different NHEJ/MMEJ balance and cell-cycle distribution. Indel %
  is a readout of *repair*, not only of cutting — this confounder sits directly on the
  primary endpoint.
- **Delivery and dose.** **[VERIFY]** what Ito et al. used. At saturating Cas9 dose,
  chromatin effects compress toward zero and the effect size shrinks. Worth knowing
  before betting the demo on it.
- Expression / Pol II occupancy; replication timing.

### 3.5 No uncertainty quantification specified

"Uncertainty" is listed as a deliverable but no method is named. Conformal prediction over
the gene-held-out folds is cheap and supports a defensible claim of the form "top-3
contains an efficient guide with 85% coverage."

### 3.6 The output is the wrong shape

Scientists do not order a ranking. They order ~3 guides and want ≥1 to work. That is
**portfolio selection under correlated failure**, not ranking. Three top-ranked guides in
the same 200 bp of closed chromatin all fail together.

Selecting a *diverse* set — spread across exons, decorrelated accessibility, hedged
against the least-certain factor — is a different objective, is what Proto's constrained
optimization is actually good for, and no existing tool does it. Most under-exploited
idea in the plan.

### 3.7 No abstention behavior

Highest-value behavior for a domain agent: *"I have no ATAC for your cell type. Closest
proxy is X, confidence drops by Y, here is what to measure to fix it."* General agents
never say this, and it is what makes the output trustworthy enough to act on.

### 3.8 No memory / no learning loop

The demo as specified is stateless. The compounding asset is that each experimental result
recalibrates the weights. Even a stub — a results table the agent appends to and refits
from — changes the story from "wrapper" to "system that improves."

---

## 4. The demo that is structurally unreplicable

Sequence-only score and cell-aware score side by side for the same guide. Show the rank
reversal between T cells and K562, with experimental indel % underneath. Then run the
label-swap ablation live and show it collapse.

Benchling cannot produce that output — not because they have not built it, but because
their score takes no cell-type argument. A general coding agent cannot produce it in the
room, because it lacks the harmonized data and the validation harness. That contrast is
the pitch.

---

## 5. Recommended next actions

Ordered by what gates what.

1. **Count paired guides** (T cell ∩ K562) in the Ito supplementary tables. Gates H3 and
   the entire cross-context demo.
2. Check per-gene guide-count distribution; pick metrics that the data can actually
   support (§3.2).
3. Build the **label-swap ablation before the UI**. It is the falsification test and the
   best slide.
4. Confirm ATAC data format — if paired-end fragments exist, use nucleosome-resolution
   signal rather than bulk (§3.3).
5. Make the output a **diverse 3-guide portfolio with conformal coverage**, not a ranked
   list (§3.6, §3.5).

---

## 6. One-liner

> Existing tools score guides. CellGuide selects a hedged guide *set* for a specific
> cellular context, tells you how confident it is, and can prove the cell-context term is
> doing real work.
