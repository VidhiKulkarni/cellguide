# Agent 7 — provenance tracking

Deterministic (no LLM) — links every guide score component back to its supporting paper,
by **parsing** [Agent 3](../agent3_metric_construction/)'s `SPEC.md` rather than
hand-duplicating its citations, so provenance can't silently drift out of sync with the
scoring spec. Also links in [Agent 4](../agent4_benchmarking/)'s validation report and
[Agent 5](../agent5_confidence_assessment/)'s confidence report when present.

## Run

```bash
uv run agent7_provenance/build.py --results agent4_benchmarking/output/results.csv
```

No API keys needed. Read-only outside this folder.

## Output

- `output/provenance.json` — per-component and per-guide source links + evidence snippets
- `output/PROVENANCE_REPORT.md` — human-readable version
