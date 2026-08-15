# Predicting CRISPR-Cas9 off-target effects in human primary cells using bidirectional LSTM with BERT embedding

Sari O., Liu Z., Pan Y., Shao X., *Bioinformatics Advances* (2025). PMC11696696, DOI 10.1093/bioadv/vbae184

We present CrisprBERT, a deep learning model incorporating a BERT architecture to provide high-dimensional embedding for paired sgRNA and DNA sequences, and Bidirectional LSTM networks for learning, to predict off-target effects using only the sgRNAs and paired DNA sequences. We proposed doublet stack encoding to capture the local energy configuration of Cas9 binding. The new model achieved better performance than state-of-the-art deep learning models on single split and leave-one-sgRNA-out cross-validation as well as independent testing. GitHub: https://github.com/OSsari/CrisprBERT

**Key discussion point (relevant to CellGuide's ATAC hypothesis):** the authors note DeepCRISPR (which integrates epigenomic features) underperformed on independent testing partly because the epigenomic profile used (HepG2) wasn't a perfect match for the actual assayed cell type (primary CD4+/CD8+ T cells) — they explicitly state "cell-type-specific chromatin contexts, including epigenomic and gene expression data, do provide additional information for distinguishing different off-target activities and would be beneficial for building predictive models," provided the epigenomic profile matches the actual target cell type.

**Training data:** CHANGE-seq — 110 sgRNA targets / 13 loci in human primary T cells, 202,043 pairs (125,419 unique after dedup); plus DeepCRISPR HEK293/K562 cell-line data (18 + 12 sgRNAs).
