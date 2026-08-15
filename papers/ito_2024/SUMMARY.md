# Ito et al. 2024 — Nucleic Acids Research (PMC10783505, DOI 10.1093/nar/gkad1076)

**This is the plan's primary ground-truth paper — its method is what the hackathon re-implements.**

- 205 gRNAs / 110 genes, electroporated individually (Cas9 RNP) into stimulated primary human CD8+ T cells; indel % measured via Sanger + ICE, in duplicate (L59, L44).
- Tested 13 sequence-only tools against the 205-guide set; CHOPCHOP (Doench 2014) and DeepSpCas9 correlated best but none was reliable alone (L60–61).
- ATAC score = median read count over the gRNA target region, from the authors' own CAR-T ATAC-seq (GSE221788) (L50, L64). ATAC alone doesn't correlate with indel%, but **combined with DeepSpCas9 ≥60 + CHOPCHOP ≥0.3 + ATAC ≥0.1, guides reliably edit efficiently** (L64–67) — this is exactly the plan's §4.4 scoring formula.
- Prospective validation set: 10 gRNAs across DNMT3A/PDCD1/PRDM1/TGFBR2/MYC selected via this rule, all worked (L67).
- Cross-context T-cell vs K562 panel (L68): GZMA/GZMB/CD3D/CD3G/CD28/EOMES edit well in T cells but poorly in K562; GATA1/CD33/HBB/HBE1/TFR2 show the reverse — this is the exact gene panel and "same guide, different context" result behind the plan's winning demo.
- Also: dual-gRNA targeting rescues closed regions (L69–73); IL-7 pretreatment improves editing in naive T cells (L77–81); replicates in hMSC-BM (L85–86).

## Where the actual data lives

The 205-gRNA table is **Supplementary Table S1**, the T/K562 gene panel is **Supplementary Table S2** — neither is in the fetched full text (body only). The team needs the NAR supplementary file itself (`gkad1076_Supplemental_Files`) to build `guide_benchmark.csv`. Source code: Figshare DOI 10.6084/m9.figshare.24428509.

## Caveats

Indel% ≠ knockout (the paper is explicit about this, matching the plan's endpoint framing). The thresholds (DeepSpCas9≥60, CHOPCHOP≥0.3, ATAC≥0.1) were tuned on this exact dataset — a starting point, not a universal rule. The chromatin-accessibility effect is specific to **transient RNP delivery** — stably expressed Cas9/gRNA can still cleave closed regions (L75–76, L92), so ATAC shouldn't be treated as a delivery-agnostic biological constant.
