# Agent 2 structured extraction — sari2025_crisprbert

1. **Experimental design**: Computational — off-target activity prediction model (BiLSTM + BERT).
2. **Target genes**: 110 sgRNAs/13 loci (CHANGE-seq) + 30 sgRNAs (DeepCRISPR set).
3. **Outcomes**: Off-target only — beats prior state-of-the-art; argues cell-type-matched epigenomic features improve off-target prediction accuracy. No on-target/knockout outcome reported.
4. **Data type**: Primary CD4+/CD8+ T cells, HEK293/K562.

**Relevance flag**: alternative candidate (alongside ozden2024_crispai_uncertainty) for the CellGuide Agent-3 specificity term; both trained on the same CHANGE-seq primary-T-cell off-target dataset.
