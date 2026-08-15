# Literature Index — `papers/related/`

**Agent 1 (literature search) output.**
Search topic for this pass: **CRISPRi / CRISPRa guide RNA design and chromatin accessibility.**

Source: Paperclip (`-s papers` = PMC + bioRxiv + medRxiv + arXiv). 34 slugs total —
**19 newly fetched** in this pass, **15 pre-existing** from the earlier Cas9-nuclease pass.

Each folder contains `meta.json` plus one of `fulltext.txt` (complete body),
`excerpt.md` / `fulltext_excerpt.txt` (partial), or `abstract.md` (abstract only).

---

## New this pass — CRISPRi / CRISPRa + chromatin accessibility

### Tier 1 — directly on-topic (chromatin context changes guide efficacy/specificity)

| Slug | Text | Why it's relevant |
|---|---|---|
| `cohen2026_context_determinants` | fulltext | **Most load-bearing for CellGuide.** 1005 endogenous sites across 8 cell systems *including primary human T cells and K562*; sequence-only predictors collapse out-of-context (DeepCRISPR 0.96→0.08, SPROUT 0.41→0.11) and top features flip sign between cell types. Ships a 557-feature catalogue with an explicit accessibility family (DNase-seq, CTCF, H3K4me3, methylation motifs, Hi-C density). |
| `feng2026_egold_chromatin_offtarget` | excerpt | Holds sequence constant across sequence-identical off-target sites: off-target editing is significantly **more** frequent in open chromatin, suppressed by DNA methylation and H3K9me3, and grows more chromatin-dependent as mismatch count rises. Adding 13 ENCODE chromatin features improved off-target model accuracy — direct justification for a chromatin-aware *specificity* term. |
| `amirabad2025_cas12_chromatin_foundation` | fulltext | ATAC-seq accessibility as a second modality on a foundation-model guide encoder lifts Cas12a on-target Spearman 0.76→0.78 (vs 0.71 DeepCpf1). Provides a reusable ATAC → binary accessibility labeling pipeline for guide loci. |
| `cucuy2026_tomato_chromatin_efficiency` | fulltext | 420 sgRNAs with matched ATAC-seq in one uniform system: open chromatin significantly raises efficiency while transcription does not; human-trained Azimuth fails to rank guides (r=0.05). Explicitly cites Ito et al. 2024 as precedent for epigenome-augmented prediction. |
| `moore2025_truncated_crispri` | excerpt | 10-nt truncated guides retain CRISPRi efficacy across hundreds of match sites, with per-site success governed by local chromatin (H3K9me3 deposition, CTCF occupancy) — spacer length + chromatin state, not 20-mer match, determine effect. |
| `chardon2024_crispra_celltype_elements` | excerpt | 493-gRNA multiplex single-cell CRISPRa screen in **both K562 and iPSC-derived neurons**; enhancer responsiveness to CRISPRa is cell-type-restricted, implying dependence on the *cis* chromatin landscape — the same cross-context logic as the Ito T-cell vs K562 panel. |
| `joyce2026_pocketseq_dcas9krab` | fulltext | Maps dCas9-KRAB binding genome-wide; sequence-mismatch predictors (CRISPOR) share nearly zero overlap with measured off-targets (1/334 sites for SOCS3_g1; missed the causal PEX19 off-target), attributed to local chromatin context. ⚠️ short preprint, 4 guides — motivates but does not size the effect. |

### Tier 2 — CRISPRi/CRISPRa guide-design rules and scoring formulations

| Slug | Text | Why it's relevant |
|---|---|---|
| `srikanth2026_crispri_library_design` | fulltext | Doench-lab CRISPRi-specific on-target scoring (Rule Set 3 Interference) from tiling screens; quantifies seed-driven off-target promiscuity and cites higher-resolution **chromatin accessibility datasets** + updated TSS annotation as the motivation for redesigning the library (Katsano). |
| `drepanos2025_ontarget_offtarget_library` | fulltext | Reference formulation for combining on-target prediction (Rule Set 3) with an off-target exclusion rule into a single guide-selection strategy (Jacquere library) — the sequence-only baseline Agent 3's metric should extend. |
| `kristof2025_crispri_repressors` | excerpt | Quantifies both axes a context-aware metric needs: guide-sequence variance (9-guide TSS-tiling panel, strong vs weak CD81/CD151 guides) **and** cell-context dependence (MAX-containing effectors potent in HEK293T but failing in A549/HCT116/HeLa via cofactor levels); neighbor-gene spreading as a specificity readout. |
| `arvidsson2025_crispra_sgrna_screen` | fulltext | Empirical CRISPRa sgRNA-efficiency screen (Tfeb/Adam17/Sirt1) that tested and **failed** to find correlation between activation and TSS distance or nearby TF binding sites — a useful negative result bounding sequence-only efficiency features. |
| `kiattisewee2025_bacterial_crispra_rules` | fulltext | Maps CRISPRa target-site position rules relative to TSS; optima vary by up to 200 bp and shift with promoter context — a positional-efficiency term whose optimum is context-dependent, not fixed. (Bacterial; no chromatin component.) |
| `xiang2025_glide_crispri_design` | fulltext | CRISPRi sgRNA library design tool built around an off-target/specificity QC framework using mismatch-tolerance rules from dCas9–sgRNA binding data. Specificity-scoring template. (Prokaryotic; no chromatin component.) |

### Tier 3 — cell-context / T-cell & K562 evidence for cross-context validation

| Slug | Text | Why it's relevant |
|---|---|---|
| `wang2026_tcell_enhancer_crispri` | fulltext | CRISPRi tiling of cis-regulatory elements (PDCD1, HAVCR2, TBX21) in **primary human T cells** — guide placement at accessible enhancer chromatin vs functional repression, in exactly CellGuide's target cell type. |
| `zhang2025_crispri_k562_screens` | fulltext | CRISPRi/CROP-seq in **K562** (the Ito et al. cross-context comparator line); only ~40–50% of targeted genes achieve effective knockdown, quantifying the guide-level efficiency variability a metric must predict. |
| `huang2024_dcas9_tcell_epigenetic` | fulltext | CRISPRa/epigenome editing in **primary human T cells**: tiles sgRNAs at −157/−333/−499 bp from the TERT TSS and shows guide-directed chromatin rewiring (dCas9-p300, dCas9-TET1) vs transient activators determines durability — guide position + local chromatin state, not sequence alone, drive CRISPRa efficacy. Documents its guide-design rules and ChIP-qPCR occupancy as an on-target specificity readout. |
| `ni2026_crispri_casrx_context` | fulltext | CRISPRi off-target risk as a promoter/TSS-architecture property: overlapping TSSs (ATF5-NUP62) and shared retrotransposon TSSs (HERV-H LTR7) cause co-repression no spacer-sequence score would catch; also quantifies CRISPRi reactivation via chromatin re-opening. |
| `feng2024_crispri_hpsc_map` | fulltext | Genome-scale CRISPRi (>20,000 gRNAs, 7,226 genes, 34 iPSC lines, ~2M cells) quantifying how the same perturbation varies across cellular/genetic backgrounds — the cross-context generalization problem at scale. |
| `taifour2026_dcas9_locus_silencing` | fulltext | dCas9-KRAB locus-selective repression of the EWSR1-FLI1 fusion — clean case of guide-level *specificity* (discriminating a fusion allele from wild-type EWSR1/FLI1) combined with promoter/chromatin-targeted silencing. |

---

## Pre-existing — earlier Cas9-nuclease / off-target-prediction pass

These were already present before this pass and were **not re-fetched**. Most hold `abstract.md` only.

| Slug | Text | Why it's relevant |
|---|---|---|
| `schep2024_chromatin_drugs` | abstract | Chromatin-context-dependent effects of 160 epigenetic drugs on Cas9 editing — most alter editing in a chromatin-dependent manner. Closest pre-existing analogue to this pass's topic. |
| `pallaseni2024_repair_context` | abstract | DNA repair context interacts with target sequence to predictably bias Cas9 mutation outcomes — cell-context term for outcome prediction. |
| `ursch2024_tcell_genomic_safety` | abstract | Genomic safety profile of CRISPR-engineered **primary human T cells** (TCR stimulation, pifithrin-α) — T-cell-context off-target/safety evidence. |
| `tommasi2025_cas9clipt_cart` | abstract | Nonviral integration of large transgenes into **human T cells** (Cas9-CLIPT) — T-cell knock-in efficiency context. |
| `nilsri2025_jak2_k562` | excerpt | Cas9 modeling of JAK2 V617F in **K562** — K562-context editing evidence for the cross-context panel. |
| `ozden2024_crispai_uncertainty` | abstract | Uncertainty quantification for off-target activity + a genome-wide sgRNA efficiency score — specificity-scoring baseline. |
| `schmitz2025_uncertainty_guide_selection` | abstract | Deep-ensemble uncertainty quantification to optimize guide selection (>90% precision) — guide-ranking methodology. |
| `schmidt2025_guidescan2` | abstract | GuideScan2 genome-wide guide design + specificity analysis — standard specificity-scoring tool to benchmark against. |
| `sari2025_crisprbert` | abstract | BiLSTM+BERT off-target prediction in **human primary cells** — sequence-only off-target baseline in a primary-cell setting. |
| `zhang2024_deepindel` | excerpt | Interpretable deep learning for Cas9 editing outcomes — on-target outcome-prediction baseline. |
| `seale2025_xcrisp` | abstract | X-CRISP domain-adaptable, interpretable repair-outcome prediction — explicit domain adaptation across contexts. |
| `riesenberg2025_synthetic_grna` | abstract | Linear model predicting synthetic gRNA activity by disentangling cleavage outcomes; flags cryptic large-scale repair. |
| `lukasiak2025_benchmark_grna_libraries` | abstract | Benchmark comparison of CRISPRn guide-design algorithms — baseline comparison set for Agent 4. |
| `kumbara2025_crispr_hawk` | abstract | Haplotype- and variant-aware guide design — genotype (not chromatin) context axis for guide selection. |
| `saraswat2025_crispr_tools_review` | abstract | Review of CRISPR tools/databases — orientation reference for available feature sources. |

---

## Notes and caveats for Agent 2

1. **Preprint weighting.** Several Tier 1/2 entries are 2025–2026 bioRxiv preprints (`srikanth2026`, `ni2026`, `wang2026`, `zhang2025`, `joyce2026`, `cucuy2026`, `cohen2026`, `drepanos2025`, `taifour2026`, `kiattisewee2025`). Not peer-reviewed — weight accordingly when deriving metric weights.
2. **`joyce2026_pocketseq_dcas9krab`** is a short-format preprint; its CRISPOR-vs-measured comparison rests on 4 guides. It motivates chromatin-aware specificity scoring but does not by itself quantify an effect size.
3. **Partial texts.** `feng2026_egold_chromatin_offtarget` is an excerpt — Paperclip's `content.lines` slab was unavailable, so it was rebuilt from `sections/`; one results subsection ("An open chromatin state promotes the off-target activity...") is unretrievable because a `/` in its filename breaks Paperclip's path parser. Its findings are covered by the included Discussion and the parallel base-editor section. `kristof2025_crispri_repressors` and `huang2024_dcas9_tcell_epigenetic` were likewise rebuilt from `sections/` (slab outage); all scientifically load-bearing sections are present, some routine Methods subsections are omitted.
4. **Pre-existing slugs are abstract-only.** The 15 papers from the earlier pass mostly hold `abstract.md`, not full text. If Agent 2 needs experimental design / target genes / cell types at the depth the pipeline spec asks for, several will need a full-text fetch pass first — notably `schep2024_chromatin_drugs` and `pallaseni2024_repair_context`, which are chromatin-context papers relevant to this topic.
5. **No duplicates.** `schep2024_chromatin_drugs` (PMC11347147 / doi 10.1093/nar/gkae570) resurfaced in this pass's searches and was correctly skipped as already-saved.
