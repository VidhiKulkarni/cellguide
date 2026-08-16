# Agent 4 — Azimuth (tier 2) in-context validation

REPORT.md's rho=0.441 validates DeepSpCas9/CHOPCHOP (tier 1), not Azimuth (tier 2) --
these are different models. This check reconstructs each Ito et al. guide's real
genomic 30-mer context (gene lookup -> real sequence -> real PAM scan -> spacer match,
no fabrication/padding) and runs Azimuth on it directly, to get an honest in-context
number for the path that actually gets used to score genes outside Ito's dataset.

- Guides in Ito et al.'s table: 199 (across 74 genes)
- Genes with a failed Ensembl lookup or sequence fetch: 41
- Guides with real context successfully reconstructed: 89/199
- Guides Azimuth itself failed to score (bad context, subprocess error): 0
- **Final n scored by Azimuth and compared to real indel%: 89**

| Score | n | Spearman ρ vs real indel% | p-value |
|---|---|---|---|
| **Azimuth (tier 2, this check)** | 89 | **0.346** | **0.000895** |
| DeepSpCas9/CHOPCHOP (tier 1), same 89-guide subset | 89 | 0.518 | 1.96e-07 |
| DeepSpCas9/CHOPCHOP (tier 1), full REPORT.md number for reference | 199 | 0.441 | 7.01e-11 |

### Genes excluded (41)

- **BACH2**: SEQUENCE_FETCH_FAILED (6:89926328-90297182)
- **BATF3**: SEQUENCE_FETCH_FAILED (1:212686217-212700088)
- **CD83**: SEQUENCE_FETCH_FAILED (6:14117056-14203665)
- **CDKN2B**: GENE_NOT_FOUND (Ensembl lookup failed)
- **CDKN2C**: GENE_NOT_FOUND (Ensembl lookup failed)
- **CTBP1**: GENE_NOT_FOUND (Ensembl lookup failed)
- **DEK**: GENE_NOT_FOUND (Ensembl lookup failed)
- **DGKQ**: GENE_NOT_FOUND (Ensembl lookup failed)
- **DPH1**: SEQUENCE_FETCH_FAILED (17:2029936-2044098)
- **DPH2**: SEQUENCE_FETCH_FAILED (1:43969775-43973573)
- **DPH5**: GENE_NOT_FOUND (Ensembl lookup failed)
- **DUSP22**: GENE_NOT_FOUND (Ensembl lookup failed)
- **EHMT1**: GENE_NOT_FOUND (Ensembl lookup failed)
- **EHMT2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **FHL2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **FOXO3**: GENE_NOT_FOUND (Ensembl lookup failed)
- **FURIN**: GENE_NOT_FOUND (Ensembl lookup failed)
- **GATA6**: GENE_NOT_FOUND (Ensembl lookup failed)
- **HDAC1**: GENE_NOT_FOUND (Ensembl lookup failed)
- **HDAC2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **HNRNPH1**: GENE_NOT_FOUND (Ensembl lookup failed)
- **ID2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **KDM1A**: GENE_NOT_FOUND (Ensembl lookup failed)
- **KLF2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **MAF**: GENE_NOT_FOUND (Ensembl lookup failed)
- **MSC**: GENE_NOT_FOUND (Ensembl lookup failed)
- **MTA2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **PCBP4**: GENE_NOT_FOUND (Ensembl lookup failed)
- **RAD54L**: GENE_NOT_FOUND (Ensembl lookup failed)
- **RAG1**: GENE_NOT_FOUND (Ensembl lookup failed)
- **RUNX2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **SOCS1**: GENE_NOT_FOUND (Ensembl lookup failed)
- **STAT4**: GENE_NOT_FOUND (Ensembl lookup failed)
- **SUV39H1**: GENE_NOT_FOUND (Ensembl lookup failed)
- **SUV39H2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **TBX21**: GENE_NOT_FOUND (Ensembl lookup failed)
- **TET2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **TNF**: GENE_NOT_FOUND (Ensembl lookup failed)
- **TOX2**: GENE_NOT_FOUND (Ensembl lookup failed)
- **TSC1**: GENE_NOT_FOUND (Ensembl lookup failed)
- **ZFP41**: GENE_NOT_FOUND (Ensembl lookup failed)

