# CellGuide AI — Source papers pulled via Paperclip

Papers cited in Section 8 of `docs/CellGuide_AI_Hackathon_Plan.pdf`. Fetched full text via Paperclip (PMC).

| Slug | Status | PMC ID | DOI | Title match |
|---|---|---|---|---|
| `ito_2024` | ✅ full text | PMC10783505 | 10.1093/nar/gkad1076 | Confirmed (author Ito, NAR, 2024; title says "gene knockout" vs plan's "gene editing" — same paper) |
| `wang_2019_deephf` | ✅ full text | PMC6753114 | 10.1038/s41467-019-12281-8 | Exact match |
| `xu_2018` | ✅ full text | PMC6076306 | 10.1038/s41598-018-30227-w | Exact match |
| `leenay_2019` | ❌ not found | — | — | Not in Paperclip corpus (Nature Biotechnology, 2019) — only found as a citation inside other papers' reference lists, not indexed as a full document |
| `jensen_2017` | ❌ not found | — | — | Not in Paperclip corpus (FEBS Letters, 2017) — no match by title, author, or topic search |

Each found paper's folder contains `meta.json` (Paperclip metadata) and `fulltext.txt` (full line-numbered body text from Paperclip's `content.lines`).

Leenay et al. 2019 and Jensen et al. 2017 were not retrievable through Paperclip's search/lookup (likely not open-access-indexed in PMC/bioRxiv/medRxiv/arXiv). To get these two, fetch manually via DOI/publisher site or `paperclip fetch <doi>` if institutional access is configured.

## Broader topical search — `papers/related/`

Beyond the plan's literal §8 reference list, a topical search across 10 core themes (chromatin accessibility & Cas9 activity, on-target ML scoring, off-target prediction, primary T-cell/CAR-T editing, K562 screens, repair-outcome prediction, uncertainty-aware guide ranking, functional/frameshift validation, benchmark comparisons of design tools) surfaced 15 additional papers, saved to `papers/related/<slug>/` (each with `meta.json` + `abstract.md`, and `fulltext_excerpt.txt` for the 2 most central ones). Combined with the 3 core papers above, that's **18 papers total** pulled for this project.

| Slug | Title | Journal/Year | PMC ID |
|---|---|---|---|
| `schep2024_chromatin_drugs` | Chromatin context-dependent effects of epigenetic drugs on CRISPR-Cas9 editing | Nucleic Acids Research 2024 | PMC11347147 |
| `ozden2024_crispai_uncertainty` | Learning to quantify uncertainty in off-target activity for CRISPR guide RNAs | Nucleic Acids Research 2024 | PMC11472043 |
| `sari2025_crisprbert` | Predicting CRISPR-Cas9 off-target effects in human primary cells using BiLSTM+BERT | Bioinformatics Advances 2025 | PMC11696696 |
| `ursch2024_tcell_genomic_safety` | Modulation of TCR stimulation and pifithrin-α improves genomic safety of CRISPR-engineered T cells | Cell Reports Medicine 2024 | PMC11722128 |
| `tommasi2025_cas9clipt_cart` | Efficient nonviral integration of large transgenes into human T cells using Cas9-CLIPT | Mol Ther Methods Clin Dev 2025 | PMC11930092 |
| `nilsri2025_jak2_k562` | CRISPR/Cas9-Based Modeling of JAK2 V617F Mutation in K562 Cells | Int J Mol Sci 2025 | PMC12111430 |
| `zhang2024_deepindel` | DeepIndel: Interpretable Deep Learning for CRISPR/Cas9 Editing Outcomes | Int J Mol Sci 2024 | PMC11507043 |
| `riesenberg2025_synthetic_grna` | Robust prediction of synthetic gRNA activity and cryptic DNA repair | Nature Communications 2025 | PMC12095496 |
| `seale2025_xcrisp` | X-CRISP: Domain-Adaptable and Interpretable CRISPR Repair Outcome Prediction | bioRxiv 2025 | PMC11839120 |
| `pallaseni2024_repair_context` | The interplay of DNA repair context with target sequence predictably biases Cas9-generated mutations | Nature Communications 2024 | PMC11599590 |
| `schmitz2025_uncertainty_guide_selection` | Leveraging uncertainty quantification to optimize CRISPR guide RNA selection | Biology Methods & Protocols 2025 | PMC12657131 |
| `schmidt2025_guidescan2` | Genome-wide CRISPR guide RNA design and specificity analysis with GuideScan2 | Genome Biology 2025 | PMC11863968 |
| `lukasiak2025_benchmark_grna_libraries` | A benchmark comparison of CRISPR guide-RNA design algorithms | BMC Genomics 2025 | PMC11863645 |
| `saraswat2025_crispr_tools_review` | Unlocking the potential of CRISPR tools and databases for precision genome editing (review) | Frontiers in Plant Science 2025 | PMC12319022 |
| `kumbara2025_crispr_hawk` | CRISPR-HAWK: Haplotype- and Variant-aware guide design toolkit | bioRxiv 2025 | PMC12767513 |

See each `meta.json`'s `relevance_to_cellguide` field for how it maps onto the plan's workstreams/roadmap.
