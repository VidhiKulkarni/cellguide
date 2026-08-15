# Agent 8 — Benchling sync

Closes the loop from the sponsor flow:

```
Guide ranking -> Next experiment -> Benchling -> Experimental result -> AIFG re-runs -> NEW ranking
```

Agent 6's top recommendation gets pushed to Benchling as "what to test next"; once the
wet-lab result is recorded there, this pulls it back into Agent 6's `record` so the ranking
updates. **Live and working** — connected to the Hackathon26 / AIFG workspace.

## What's set up in Benchling

Everything lives in the **Hackathon26** project, **AIFG** folder (`lib_uN7eHTTMEo`). Built
as two **Custom Entity schemas** (not Result schemas — that's what actually exists in this
workspace; `client.py` is written against the Custom Entity API accordingly):

**1. `CellGuide Next Experiment2`** (`ts_lWhrOraJND`) — fields:
- `Gene` (Text)
- `Cell Type` (Text)
- `Spacer` (Text)
- `Priority` (Number/Decimal)
- `Rationale` (Text, long)

**2. `CellGuide Guide Result`** (`ts_0gNo8twWAJ`) — fields:
- `Gene` (Text)
- `Cell Type` (Text)
- `Spacer` (Text)
- `Indel %` (Number/Decimal)
- `Source` (Text)

(Field *names* must match `client.py`'s `GENE_FIELD` etc. constants exactly — edit those
constants if you rename fields in Benchling.)

## `.env`

```bash
BENCHLING_API_KEY='sk_...'                     # Developer Console -> API keys (Basic-auth key)
BENCHLING_TENANT_URL='https://hackathon26.bnchdev.org'
BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID='ts_lWhrOraJND'
BENCHLING_RESULTS_SCHEMA_ID='ts_0gNo8twWAJ'
BENCHLING_FOLDER_ID='lib_uN7eHTTMEo'
```

Re-discover any of these IDs (e.g. if you rebuild the schemas) with:

```bash
uv run agent8_benchling_sync/list_resources.py --project Hackathon26
```

(`list_resources.py` currently only prints Assay Result schemas + folders/projects — it
doesn't yet list Custom Entity schemas by name; use the Benchling UI's schema settings page
to confirm a Custom Entity schema's ID if you create a new one.)

## Run

```bash
uv run agent8_benchling_sync/run.py --candidates ../agent4_benchmarking/output/results.csv
```

## Auth note

Benchling's API uses HTTP Basic Auth: the API key as the username, blank password —
`benchling-sdk`'s `ApiKeyAuth` handles this. Custom Entities *can* be updated in place, but
`push_next_experiment` always creates a fresh one instead — that gives a full history of
recommendations over time rather than overwriting the last one.
