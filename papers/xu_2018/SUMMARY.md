# Xu et al. 2018 — Scientific Reports (PMC6076306, DOI 10.1038/s41598-018-30227-w)

**Relevant to the plan's cross-cell-type confound discussion, not to gRNA scoring itself.**

- Introduces a "tube electroporation" delivery device and tests Cas9/gRNA RNP delivery across HEK293FT, primary human MSC, human iPSC, and primary human T cells, targeting B2M, APP, AAVS1, OCT4, PDCD1 (L25).
- **Key finding directly relevant to the plan's "what is cell-context-specific" framing (plan §1.1):** with efficient RNP delivery, the *same gRNA* achieved consistent editing efficiency across very different cell types (variance <30%), contradicting earlier reports of 4–10× lower efficiency in primary cells vs. HEK293T (L26). The authors argue prior cross-cell-type differences were largely a **delivery artifact**, not a biological (chromatin/epigenetic) one.
- This is a useful counterweight/caveat to cite alongside Ito et al.: it suggests that when comparing T-cell vs. K562 efficiency, the team should be careful to attribute differences to chromatin accessibility specifically, not to confounded delivery efficiency between the two cell types — the plan's risk table (§7) already flags "delivery, repair state, transcription" as confounds, and this paper is a solid citation for that caveat.
- Also demonstrates unexpectedly high HDR rates (up to 42%) via PAM-disrupting ssODN co-delivery — not directly relevant to the plan's cutting/indel-only MVP scope, but relevant background if the team later extends to precise-edit design.
