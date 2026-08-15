# Agent 2 — literature summarization

Reads [Agent 1](../agent1_literature_search/)'s saved papers and extracts, per paper:
experimental design (KO/KI/CRISPRi/CRISPRa), target genes, outcomes (on-/off-target), and
data type (cell line/tissue/animal model).

## Run

```bash
uv run agent2_literature_summarization/run.py
```

Requires `ANTHROPIC_API_KEY` in `../.env`. No paperclip/MCP access needed — it only reads
files Agent 1 already saved. Skips papers that already have a `SUMMARY.md`, so it's safe to
re-run after Agent 1 adds new papers.

## Output

`output/related/<slug>/SUMMARY.md` per paper, plus a combined `output/SUMMARY.md` table
synthesizing across all papers.

Input to [Agent 3](../agent3_metric_construction/).
