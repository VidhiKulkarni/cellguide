# Wang et al. 2019 (DeepHF) — Nature Communications (PMC6753114, DOI 10.1038/s41467-019-12281-8)

**This is the source of the sequence-only baseline the plan's Baseline A / Model comparison table (§4.2) is built against.**

- Genome-scale lentiviral guide–target pair screen: indel rates for **55,604 gRNAs (WT-SpCas9)**, plus ~58k/57k for eSpCas9(1.1) and SpCas9-HF1, covering ~20,000 genes in HEK293T (L26).
- Best model: **RNN + hand-crafted biological features** (secondary structure accessibility, Tm, GC content) — Spearman correlation 0.867 (WT-SpCas9), beating plain RNN (0.856), CNN (0.846), XGBoost (0.845), MLP (0.842) (L38–44).
- Public online tool at DeepHF.com — a plausible drop-in sequence-efficacy score source for the plan's feature table (§4.1, "Sequence efficacy" block), as an alternative to CHOPCHOP/DeepSpCas9 which Ito et al. actually used.
- **Directly relevant negative result:** the authors tried fine-tuning DeepWt_U6 with DNase-I chromatin-accessibility data (KBM-7, HEK293T) and found it **did not improve prediction** (L49) — a notable counterpoint to Ito et al.'s positive ATAC result, worth flagging to the team as a discussion point. Their guide library was delivered via lentiviral integration into open chromatin, which structurally minimizes accessibility variance — unlike Ito's transient RNP electroporation into intact chromatin, which is why accessibility mattered there.
- Indel rate ≠ phenotype was also tested here: correlation with protein expression r=0.82, with luciferase functional assay r=0.70 (L56) — supports the plan's cautious "indel% ≠ knockout" framing.
- Also useful: on-target/off-target trade-off data (L57) — higher on-target activity generally raises off-target risk for WT-SpCas9, but not for the high-fidelity variants — relevant if the specificity term in the plan's scoring formula is elaborated later.

## Caveats

All guides were assayed as synthetic integrated lentiviral targets in HEK293T, not endogenous primary-cell loci — a very different assay context from Ito's endogenous T-cell RNP data. Direct score comparability across the two datasets should be validated, not assumed.
