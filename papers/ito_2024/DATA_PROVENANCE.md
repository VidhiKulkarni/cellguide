# How `table_s1_205_gRNAs.csv` / `table_s2_tcell_vs_k562_panel.csv` were obtained

Paperclip's own ingestion of PMC10783505 only converted the supplementary Excel file
(`gkad1076_supplemental_files.zip`) into a **schema summary** (`supplements/gkad1076_supplemental_files.zip.md.lines`
— column names, dtypes, and 3 sample values per column), not the full row-level data, and
its sandboxed vsh cannot unzip or parse binary spreadsheets (`cat` on the raw zip errors:
"Cannot read binary file ... Download via GCS or use Python to process").

NCBI's own OA package mirrors were unreachable from this environment:
- The `ftp://` OA package link from `oa.fcgi?id=PMC10783505` returns curl exit code 9 (FTP access denied) — outbound FTP appears blocked.
- The `https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/...` HTTPS mirror 404s.
- The `pmc.ncbi.nlm.nih.gov/articles/instance/.../bin/...zip` direct-download link is behind a Google reCAPTCHA challenge page when fetched without a browser session.

**What worked:** Europe PMC's supplementary-files REST endpoint, which is not bot-gated:

```
https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10783505/supplementaryFiles
```

This returns a zip containing the article's figures plus the original nested
`gkad1076_supplemental_files.zip`, which itself contains
`2nd revise Supplementary Table 231015.xlsx` (Table S1, Table S2 sheets) — parsed locally
with `openpyxl` into the two CSVs in this folder. Row counts and sample values were
cross-checked against Paperclip's schema summary and matched exactly.

Reuse this Europe PMC pattern (`https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/supplementaryFiles`)
for other PMC papers' supplementary data if Paperclip only surfaces a schema summary.
