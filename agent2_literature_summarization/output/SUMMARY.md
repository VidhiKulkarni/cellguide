# Agent 2 output — structured literature extraction (all 18 papers)

Per `CLAUDE.md` Agent 2 spec: for each paper, (1) experimental design — KO/KI/CRISPRi/CRISPRa; (2) target genes; (3) outcomes — expected on-target + reported off-target; (4) data type — cell line/animal/tissue/cell type.

| Slug | Experimental design | Target genes | Outcomes (on-target / off-target) | Data type |
|---|---|---|---|---|
| ito_2024 | KO (RNP) | 110 genes (205 gRNAs); full list in Supplementary Table S1 (not fetched) | Indel% (Sanger+ICE, duplicate); **no off-target data** | Primary human CD8+ T cells, K562, hMSC-BM |
| wang_2019_deephf | KO (lentiviral integrated) | ~20,000 genes, genome-scale | Indel rate (Spearman 0.867 best model); on-/off-target trade-off (WT vs high-fidelity variants) | HEK293T, synthetic integrated targets |
| xu_2018 | KO (RNP) + KI (HDR/ssODN) | B2M, APP, AAVS1, OCT4, PDCD1 | Consistent efficiency across cell types (<30% var.); HDR ≤42%; off-target not reported | HEK293FT, primary MSC, iPSC, primary T cells |
| kumbara2025_crispr_hawk | Computational (variant-aware design) | BCL11A + 7 therapeutic loci; 79,648 genomes | On-target activity altered by population variants (82.5% of guides); PAM creation/loss | Population variant data, no cell system |
| lukasiak2025_benchmark_grna_libraries | KO (pooled screen library benchmark) | Genome-wide | Library specificity/sensitivity; 50% smaller libraries, same performance | Computational benchmark over public KO screen data |
| nilsri2025_jak2_k562 | KI (point mutation, RNP) | JAK2 (V617F) | Confirmed KI; ↑expression, ↑proliferation, ↑drug sensitivity; no off-target reported | K562 |
| ozden2024_crispai_uncertainty | Computational off-target model (trained on CHANGE-seq) | 110 sgRNAs / 13 loci | Off-target only: calibrated uncertainty, beats prior SOTA | Primary human T cells (train), HEK293T/K562 (test) |
| pallaseni2024_repair_context | KO/cleavage, repair-mechanism dissection | Synthetic reporter targets (not endogenous genes) | 236,000+ mutational outcomes; Prkdc/Polm/Nbn/Polq pathway roles; no off-target | 18 repair-deficient mESC lines |
| riesenberg2025_synthetic_grna | KO (synthetic RNP) | Not gene-specific, genome-wide model | Indel-only scoring **underestimates** true activity; HDR-efficiency + large-deletion tools; Cas9 vs Cas12a safety comparison | Multiple published cell-line datasets |
| saraswat2025_crispr_tools_review | N/A (review) | N/A | Survey of design/off-target/screening tools | N/A |
| sari2025_crisprbert | Computational off-target model | 110 sgRNAs/13 loci + 30 sgRNAs (DeepCRISPR) | Off-target only: beats SOTA; argues cell-type-matched epigenomics improves prediction | Primary CD4+/CD8+ T cells, HEK293/K562 |
| schep2024_chromatin_drugs | KO/cleavage (dCas9 + RNP, reporter) | 19 integrated reporter sites (not endogenous genes) | Efficiency + NHEJ:MMEJ repair-pathway balance vs. chromatin state/drug (58/160 drugs modulate); no off-target | K562#17 (reporter clone), RPE-1 |
| schmidt2025_guidescan2 | Computational tool + KO screen application | Genome-wide + essentiality screen + mouse allele-specific | Off-target-focused: flags low-specificity guides, builds low-off-target library | Computational + mouse (hybrid genome) |
| schmitz2025_uncertainty_guide_selection | Computational (deep ensemble, uncertainty) | Not gene-specific; >93% mouse genome coverage | On-target efficiency ranking under uncertainty; >90% precision | Computational; training data type underdetermined (see notes) |
| seale2025_xcrisp | KO/cleavage repair-outcome model + transfer learning | Not gene-specific | Repair-outcome frequency prediction; microhomology location > sequence; no off-target | mESC (pretrain) → K562, HAP1, U2OS, repair-altered mESC |
| tommasi2025_cas9clipt_cart | KI (HDR, RNP + novel donor) | TRAC (CAR knock-in) | KI efficiency ≤60%; functional CAR-T potency; no off-target | Primary human T cells (CAR-T) |
| ursch2024_tcell_genomic_safety | KO (RNP), cell activation state as variable | Not gene-specific | Activation state → large deletions/translocations/aneuploidy; pifithrin-α mitigates; not classical off-target | Primary human T cells (varying activation states), CAR T cells |
| zhang2024_deepindel | KO/cleavage repair-outcome model | Not gene-specific (60bp windows, pooled data) | Deletion/insertion/frameshift frequency prediction; cross-cell-type transfer works reasonably well; no off-target | K562, HEK293T, primary human T cells |

## Notes / confidence flags

- **schmitz2025_uncertainty_guide_selection**: data type for field (4) is underdetermined from the abstract alone (only "mouse genome coverage" stated) — flagged as unclear rather than guessed.
- **ito_2024 has no off-target/specificity data at all** — the plan's specificity term must come from elsewhere. `ozden2024_crispai_uncertainty` and `sari2025_crisprbert` are the two strongest candidates in this set, both trained on the same CHANGE-seq primary-T-cell data.
- Several "computational tool" papers (kumbara, ozden, sari, schmidt, schmitz, saraswat) run no wet-lab KO/KI/CRISPRi/CRISPRa of their own — marked "computational" rather than forced into the KO/KI/CRISPRi/CRISPRa taxonomy, since they are prediction/ranking tools evaluated on others' experimental data.
- **No CRISPRi or CRISPRa study appeared in either the core 3 or the related 15** — everything found is knockout/cleavage or knockin (HDR), consistent with the plan's SpCas9-knockout-oriented MVP scope. If CRISPRi/CRISPRa coverage is needed, that's a gap requiring a further targeted Agent-1 search.
