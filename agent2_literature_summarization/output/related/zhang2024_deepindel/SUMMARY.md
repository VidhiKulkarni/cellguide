# Agent 2 structured extraction — zhang2024_deepindel (DeepIndel)

1. **Experimental design**: KO/cleavage repair-outcome prediction model (interpretable deep learning).
2. **Target genes**: Not gene-specific (60bp windows around cut sites, pooled data).
3. **Outcomes**: On-target — predicts deletion/insertion/frameshift outcome frequencies; cross-cell-type transfer performs reasonably well. Off-target — not addressed.
4. **Data type**: K562, HEK293T, primary human T cells.

**Relevance flag**: along with seale2025_xcrisp, a substitute for the un-fetchable Leenay et al. 2019 (SPROUT) paper for repair-outcome/frameshift prediction needed in the plan's v2 roadmap stage.
