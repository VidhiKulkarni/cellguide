# Agent 8 — Benchling sync

Closes the pipeline loop. Pulls guide experiment results out of the Benchling tenant,
feeds each into [Agent 6](../agent6_next_experiment/)'s `record` (which logs it and
re-ranks), then pushes the fresh ranking and confidence back so the lab notebook reflects
current state.

```
Benchling AIFG -> Agent 6 record -> re-ranked recommendations -> Benchling AIFG
```

## Tenant specifics (re:AGENT hackathon)

This deployment is not a standard Benchling install. Three things differ from the docs:

| | Standard Benchling | This tenant |
|---|---|---|
| Host | `<org>.benchling.com` | `hackathon26.bnchdev.org` |
| Auth | Bearer API key | OAuth2 app: `client_id` + `client_secret` |
| Location | wherever | project `Hackathon26`, folder `AIFG` |

## Setup

1. In the tenant: **Developer Console → Apps → Create**. Copy the `client_id` and
   `client_secret` (the secret is shown once).
2. Add the app to the `Hackathon26` project — a new app has no permissions and will see
   an empty result set until you do.
3. Fill in `../.env` (gitignored) from `../.env.example`:
   ```
   BENCHLING_TENANT_URL=https://hackathon26.bnchdev.org
   BENCHLING_CLIENT_ID=...
   BENCHLING_CLIENT_SECRET=...
   BENCHLING_AIFG_FOLDER_ID=lib_...
   BENCHLING_RESULTS_SCHEMA_ID=...   # optional; narrows the query to one entity schema
   ```

## Run

```bash
uv run agent8_benchling_sync/run.py --dry-run   # show what would sync, write nothing
uv run agent8_benchling_sync/run.py --no-push   # pull + re-rank only
uv run agent8_benchling_sync/run.py             # full loop
```

Start with `--dry-run`. It exercises auth, folder access, and field mapping without
writing to either the experiment log or Benchling.

## Field mapping

`fetch_new_results()` expects custom entities with fields `gene`, `cell_type`, `spacer`,
`indel_pct`. Entities whose `indel_pct` isn't numeric are skipped rather than guessed at.
If your AIFG schema names these differently, adjust the `field(...)` calls in
`client.py` — that is the one place the mapping lives.

`push_ranking_update()` writes `combined_score` and `confidence` onto the matching entity,
so those fields need to exist on the schema for the write-back to succeed.
