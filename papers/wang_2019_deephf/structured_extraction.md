# Agent 2 structured extraction — Wang et al. 2019 (DeepHF)

1. **Experimental design**: KO — lentiviral integrated guide-target pair library, tested across 3 Cas9 variants (WT-SpCas9, eSpCas9(1.1), SpCas9-HF1).
2. **Target genes**: Genome-scale, ~20,000 genes; 55,604 (WT-SpCas9) / ~58,000 (eSpCas9) / ~57,000 (SpCas9-HF1) gRNAs.
3. **Outcomes**: On-target — indel rate; best model (RNN + hand-crafted biological features) reaches Spearman correlation 0.867. Indel% correlates with protein expression (r=0.82) and a luciferase functional assay (r=0.70). Off-target — on-target/off-target trade-off observed: higher on-target activity raises off-target risk for WT-SpCas9, but not for the high-fidelity variants.
4. **Data type**: HEK293T, synthetic integrated lentiviral targets (not endogenous primary-cell loci).
