# Benchling schema setup (Hackathon26 / AIFG)

Create these two **Result Schemas** in Benchling: Settings → Feature Library / Schemas →
Result Schemas → New Result Schema.

## Schema 1: `CellGuide Next Experiment`

| Field Name | Type |
|---|---|
| `Gene` | Text |
| `Cell Type` | Text |
| `Spacer` | Text |
| `Priority` | Number (Decimal) |
| `Rationale` | Text (Long Text) |

## Schema 2: `CellGuide Guide Result`

| Field Name | Type |
|---|---|
| `Gene` | Text |
| `Cell Type` | Text |
| `Spacer` | Text |
| `Indel %` | Number (Decimal) |
| `Source` | Text |

Field names must match exactly (case and spacing) — `agent8_benchling_sync/client.py` reads
and writes by these exact names.

After creating both, run:

```bash
uv run agent8_benchling_sync/list_resources.py --project Hackathon26
```

and put the two schema IDs it prints into `.env`:

```bash
BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID='assaysch_...'
BENCHLING_RESULTS_SCHEMA_ID='assaysch_...'
```
