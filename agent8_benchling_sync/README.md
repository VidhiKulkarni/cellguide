# Agent 8 — Benchling sync

Closes the loop from the sponsor flow:

```
Guide ranking -> Next experiment -> Benchling -> Experimental result -> AIFG re-runs -> NEW ranking
```

Agent 6's top recommendation gets pushed to Benchling as "what to test next"; once the
wet-lab result is recorded there, this pulls it back into Agent 6's `record` so the ranking
updates. Code is real (uses the official `benchling-sdk`), but **not runnable yet** — no
tenant/schema was set up as of writing this.

## What to set up in Benchling first

Everything lives in the **Hackathon26** project, **AIFG** folder.

Create two **Result schemas** (Feature Library / Schema settings — result schemas are
immutable per-record types, which fits both use cases: a timestamped "here's what to test
next" log, and a timestamped "here's what we measured" log):

**1. "CellGuide Next Experiment"** — fields:
- `Gene` (Text)
- `Cell Type` (Text)
- `Spacer` (Text)
- `Priority` (Number/Decimal)
- `Rationale` (Text, long)

**2. "CellGuide Guide Result"** — fields:
- `Gene` (Text)
- `Cell Type` (Text)
- `Spacer` (Text)
- `Indel %` (Number/Decimal)
- `Source` (Text)

(Field *names* must match `client.py`'s `GENE_FIELD` etc. constants exactly — edit those
constants instead if you name things differently.)

## Then, in `.env`

```bash
BENCHLING_API_KEY='...'                        # Developer Console -> API keys (Basic-auth key)
BENCHLING_TENANT_URL='https://your-org.benchling.com'
BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID='...'
BENCHLING_RESULTS_SCHEMA_ID='...'
BENCHLING_PROJECT_ID='...'                     # optional, scopes writes to Hackathon26
```

Find the schema/project IDs with:

```bash
uv run agent8_benchling_sync/list_resources.py --project Hackathon26
```

## Run

```bash
uv run agent8_benchling_sync/run.py --candidates ../agent4_benchmarking/output/results.csv
```

## Auth note

Benchling's API uses HTTP Basic Auth: the API key as the username, blank password —
`benchling-sdk`'s `ApiKeyAuth` handles this. Results can't be updated once created (only
archived + recreated), so `push_next_experiment` always creates a fresh record — that
gives you a full history of recommendations over time instead of overwriting the last one.
