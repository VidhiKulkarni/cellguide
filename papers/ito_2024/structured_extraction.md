# Agent 2 structured extraction — Ito et al. 2024

1. **Experimental design**: KO — Cas9 RNP electroporation, indel formation; dual-gRNA variant also tested.
2. **Target genes**: 110 genes, 205 gRNAs total. Named subsets: DNMT3A/PDCD1/PRDM1/TGFBR2/MYC (prospective validation set); GZMA/GZMB/CD3D/CD3G/CD28/EOMES (T-cell-open panel); GATA1/CD33/HBB/HBE1/TFR2 (K562-open panel). Full 110-gene list is in Supplementary Table S1 (not present in the fetched full text — needs the NAR supplementary ZIP).
3. **Outcomes**: On-target — indel % via Sanger sequencing + ICE, measured in duplicate. Off-target — **not measured in this paper**; it supplies no specificity data, a gap the CellGuide Agent-3 scoring formula must fill from elsewhere (e.g. crispAI/CrisprBERT, see `papers/related/ozden2024_crispai_uncertainty/` and `papers/related/sari2025_crisprbert/`).
4. **Data type**: Primary human CD8+ T cells (stimulated), K562 (CML cell line), hMSC-BM (bone-marrow mesenchymal stem cells).
