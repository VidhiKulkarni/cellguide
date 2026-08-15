# Paper pull + summary — CellGuide AI hackathon plan

Source: `docs/CellGuide_AI_Hackathon_Plan.pdf`, §8 "Key sources and links." Fetched via Paperclip; see `MANIFEST.md` for fetch status per paper.

## Combined synthesis for the hackathon workstreams

- **Workstream A (data ingestion):** Ito et al. Supplementary Tables S1/S2 are the actual source of `guide_benchmark.csv` — the fetched full text (body only) doesn't contain the tables; someone needs to pull the NAR supplementary ZIP directly (`gkad1076_Supplemental_Files`).
- **Baseline model choice (§4.2 Baseline A):** DeepHF (Wang et al.) is a viable, well-documented sequence-only score source with a public site/API, and its RNN+biofeature architecture is a good reference if the team wants to go beyond linear/GBM baselines later.
- **Cell-context hypothesis (H2, plan §1.2):** Ito et al. is direct positive evidence that chromatin accessibility improves prediction in *transient RNP* delivery; Wang et al.'s DNase-I fine-tuning failure is a useful negative control showing the effect is delivery-method-dependent, not universal — this nuance strengthens rather than weakens the hackathon's pitch if stated explicitly in the demo/README.
- **Cross-context confound risk (plan §7 risk table):** Xu et al. is the citation to use when arguing that T-cell vs. K562 editing differences could stem from delivery, not just chromatin — supports the plan's existing caveat language.

## Papers fetched

| Slug | Paper | Role in plan |
|---|---|---|
| `ito_2024/` | Ito Y. et al. 2024, *Nucleic Acids Research* | Primary ground-truth dataset (205 gRNAs/110 genes, T-cell/K562 panel) |
| `wang_2019_deephf/` | Wang D. et al. 2019, *Nat Commun* (DeepHF) | Sequence-only baseline score source |
| `xu_2018/` | Xu X. et al. 2018, *Sci Rep* | Cross-cell-type delivery-confound caveat |

## Missing

**Leenay et al. 2019** (*Nat Biotechnol*, SPROUT — repair-outcome prediction, Tier 2 in the roadmap) and **Jensen et al. 2017** (*FEBS Letters*, chromatin/secondary-structure effects) were **not found in the Paperclip corpus** (not indexed in PMC/bioRxiv/medRxiv/arXiv). Both are cited by name inside Ito et al.'s own reference list, so the team should source them via institutional journal access (Nature Biotechnology, FEBS Letters) if SPROUT-style repair prediction or the Jensen chromatin-comparison claims are needed for v2 of the model.

## Broader topical pull — `papers/related/` (15 more papers, 18 total)

Beyond the plan's literal §8 citations, a topical search across chromatin/Cas9 activity, on-/off-target ML scoring, T-cell/K562 editing, repair-outcome prediction, and guide-ranking-under-uncertainty surfaced 15 more relevant papers (full list + relevance notes in `MANIFEST.md`). Highlights that extend the synthesis above:

- **Repair-outcome / v2-v4 roadmap:** `zhang2024_deepindel`, `seale2025_xcrisp`, and `pallaseni2024_repair_context` are strong substitutes for the un-fetchable Leenay/SPROUT paper — DeepIndel and X-CRISP both predict frameshift/indel-type outcomes from sequence, and X-CRISP specifically demonstrates cross-cell-type transfer learning (mESC → K562/HAP1/U2OS from as few as 50 samples), a direct template for the plan's v3 "unseen-cell transfer" stage.
- **Chromatin mechanism, independent of Ito et al.:** `schep2024_chromatin_drugs` (160 epigenetic drugs × 19 chromatin contexts in K562/RPE-1 reporters) is independent, more mechanistic evidence that chromatin state governs both editing efficiency AND repair-pathway choice — strengthens the plan's ATAC hypothesis (H2) beyond a single dataset.
- **Off-target/specificity term:** `ozden2024_crispai_uncertainty` and `sari2025_crisprbert` are both trained on the same CHANGE-seq 110-sgRNA/13-locus primary-T-cell dataset — either is a plausible drop-in for the plan's specificity term, and both come with genome-wide aggregate scores. crispAI's uncertainty output maps directly onto the plan's "uncertainty" secondary endpoint (§1.1, §4.3).
- **Guide ranking under uncertainty:** `schmitz2025_uncertainty_guide_selection` is the closest match anywhere in this search to the plan's actual deliverable — an uncertainty-aware guide *selection strategy*, not just a score.
- **Endpoint caveat, reinforced:** `riesenberg2025_synthetic_grna` (2025, Nat Commun) adds a fresh caveat that indel% can also *underestimate* true cleavage activity, complementing the plan's existing "indel% ≠ knockout" framing.
- **Tooling:** `schmidt2025_guidescan2` is a concrete open-source fallback for Workstream B1 if Benchling access is limited, exactly as the plan's risk table anticipates.
- **Lower-priority background:** `ursch2024_tcell_genomic_safety`, `tommasi2025_cas9clipt_cart`, `nilsri2025_jak2_k562`, `lukasiak2025_benchmark_grna_libraries`, `saraswat2025_crispr_tools_review`, and `kumbara2025_crispr_hawk` are useful context/methodology references but not central to the core ranking hypothesis.
