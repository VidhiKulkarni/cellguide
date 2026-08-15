# Agent 5 — scientific skeptic / confidence assessment

Reviews [Agent 3](../agent3_metric_construction/)'s scoring metric and
[Agent 4](../agent4_benchmarking/)'s results as a skeptic: flags conflicting evidence
between cited papers, weak assumptions, context mismatches (delivery method, cell type),
and confounders the score doesn't account for — then gives an explainable confidence
rating per gene/guide.

Scoped tight on purpose: Read/Write/Glob/Grep only (no Bash, no MCP, no network) — read
access to `agent2_literature_summarization/output/`, `agent3_metric_construction/`,
`agent4_benchmarking/output/`, and `papers/`; write access only inside this folder's own
`output/`.

## Run

```bash
uv run agent5_confidence_assessment/run.py --results ../agent4_benchmarking/output/results.csv
```

Requires `ANTHROPIC_API_KEY` in `../.env`. No paperclip access needed.

## Output

- `output/confidence.json` — array of `{gene, cell_type, confidence, confidence_numeric,
  issues, rationale}`, consumed by [Agent 6](../agent6_next_experiment/) as its preferred
  uncertainty signal
- `output/CONFIDENCE_REPORT.md` — human-readable version
