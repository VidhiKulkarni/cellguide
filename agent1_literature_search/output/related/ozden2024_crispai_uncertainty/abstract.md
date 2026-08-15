# Learning to quantify uncertainty in off-target activity for CRISPR guide RNAs

Özden F., Minary P., *Nucleic Acids Research* (2024). PMC11472043, DOI 10.1093/nar/gkae759

CRISPR-based genome editing technologies have revolutionised the field of molecular biology, offering unprecedented opportunities for precise genetic manipulation. However, off-target effects remain a significant challenge. Current literature predominantly focuses on point predictions for off-target activity, which may not fully capture the range of possible outcomes and associated risks. We present crispAI, a neural network architecture-based approach for predicting uncertainty estimates for off-target cleavage activity, using a Zero-Inflated Negative Binomial (ZINB) count model. We also present crispAI-aggregate, a genome-wide sgRNA efficiency/specificity score enabling prioritization among sgRNAs with similar point aggregate predictions. Uncertainty estimates are calibrated and predictive performance is superior to state-of-the-art off-target prediction methods. Tool: https://github.com/furkanozdenn/crispr-offtarget-uncertainty

**Training data:** CHANGE-seq dataset — 110 sgRNAs across 13 therapeutically relevant loci in human primary T cells, 2,019,434 candidate off-target sites. Tested against GUIDE-seq, SITE-seq, and HEK293T/K562 cell-line datasets.
