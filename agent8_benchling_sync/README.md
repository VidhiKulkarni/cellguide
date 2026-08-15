# Agent 8 — Benchling sync (stub)

**Not runnable yet** — no Benchling account/API key was available when this was scaffolded.
`client.py`'s two methods (`fetch_new_results`, `push_ranking_update`) raise
`NotImplementedError` with exactly what each needs.

## To complete this

1. Get a Benchling API key (Settings → Developer Console → API keys) and your tenant
   subdomain.
2. Decide which Benchling schema (custom entity or result type) holds guide experiment
   results in your workspace — gene, cell type, spacer, indel % — and pass its schema ID.
3. Fill in the two `NotImplementedError` bodies in `client.py` using Benchling's REST API
   (https://benchling.com/api/reference), following the request shapes already sketched in
   the docstrings.
4. Add `BENCHLING_API_KEY` to `../.env`.

## Intended flow (once implemented)

`run.py` pulls new results from Benchling → feeds each into
[Agent 6](../agent6_next_experiment/)'s `record` subcommand (updates the ranking) → pushes
the new top ranking and [Agent 5](../agent5_confidence_assessment/)'s confidence back to
Benchling.

```bash
uv run agent8_benchling_sync/run.py --tenant your-org --schema-id <id>
```
