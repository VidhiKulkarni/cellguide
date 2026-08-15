# Agent 2 structured extraction — seale2025_xcrisp (X-CRISP)

1. **Experimental design**: KO/cleavage repair-outcome prediction model with domain-adaptation/transfer learning.
2. **Target genes**: Not gene-specific.
3. **Outcomes**: On-target — predicts repair-outcome frequency; microhomology *location* matters more than microhomology *sequence* for outcome prediction. Off-target — not addressed.
4. **Data type**: Pretrained on mESC, transferred to K562, HAP1, U2OS, and repair-pathway-altered mESC lines (from as few as 50 target-site samples in the new cell type).

**Relevance flag**: a direct template for the hackathon plan's v3 "unseen-cell transfer" roadmap stage (§6.1) — demonstrates that a model pretrained in one cell type can transfer to K562 and others with minimal new data.
