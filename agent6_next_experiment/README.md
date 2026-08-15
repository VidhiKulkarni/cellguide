# Agent 6 — next-experiment recommendation

Deterministic (no LLM). Ranks untested candidate guides by
`priority = combined_score * uncertainty` and recommends the top picks — prefers Agent 5's
calibrated confidence for uncertainty when available, otherwise falls back to a transparent
proxy (disagreement between the three score components).

## Run

```bash
# rank current candidates
uv run agent6_next_experiment/recommend.py recommend \
    --candidates ../agent4_benchmarking/output/results.csv --top 5

# log a real result, then automatically re-rank
uv run agent6_next_experiment/recommend.py record \
    --gene GZMA --cell-type T --spacer GACCTGAAGCTGAGCGAGTG --indel-pct 88.0 \
    --candidates ../agent4_benchmarking/output/results.csv --top 5
```

No API keys needed.

## State

`state/experiment_log.csv` — every recorded real result (gene, cell_type, spacer,
indel_pct, source, recorded_at). Already-logged (gene, cell_type, spacer) triples are
excluded from future `recommend` runs.

## Output

`output/recommendations.csv` — current top-N ranked candidates with `uncertainty` and
`priority` columns.
