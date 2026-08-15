# Agent 2 structured extraction — ozden2024_crispai_uncertainty (crispAI)

1. **Experimental design**: Computational — off-target activity model trained on CHANGE-seq experimental off-target data, with calibrated uncertainty output.
2. **Target genes**: 110 sgRNAs / 13 loci (same CHANGE-seq set used by sari2025_crisprbert).
3. **Outcomes**: Off-target only — calibrated uncertainty estimates, beats prior state-of-the-art off-target predictors. No on-target/knockout outcome reported.
4. **Data type**: Trained on primary human T cells (CHANGE-seq); tested on HEK293T/K562.

**Relevance flag**: strong candidate for the CellGuide Agent-3 specificity term, since Ito et al. (the primary ground-truth paper) has no off-target data of its own, and this model is trained on data from the same primary-T-cell system.
