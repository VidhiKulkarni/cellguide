"""
Agent 8 — Benchling sync (CellGuide AI pipeline, see ../CLAUDE.md).

Uses the official `benchling-sdk` package to close the loop from the sponsor flow:

    Guide ranking -> Next experiment -> Benchling -> Experimental result -> AIFG re-runs

i.e. Agent 6's top recommendation gets written to Benchling (so the wet-lab team sees what
to run next), and once they've recorded a real result there, this pulls it back so Agent 6
can `record` it and re-rank.

Requires, in `../.env`:
  BENCHLING_API_KEY                    - Basic-auth API key (Benchling -> Developer Console -> API keys)
  BENCHLING_TENANT_URL                 - e.g. https://your-org.benchling.com
  BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID  - schema ID for "what to test next" records
  BENCHLING_RESULTS_SCHEMA_ID          - schema ID for recorded experimental results

None of these exist yet (no tenant/schema chosen as of writing this) — see `README.md` for
exactly what to create in the Benchling UI (both live in the Hackathon26 / AIFG folder) and
how to find the resulting IDs (`list_resources.py` in this folder helps once you have a
tenant URL and API key).

Field names below (GENE_FIELD etc.) must match your schemas' field *names* exactly
(Benchling UI: schema field "name", not necessarily what's displayed) — edit them if you
name the fields differently when creating the schemas.
"""

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling
from benchling_sdk.helpers.serialization_helpers import fields
from benchling_sdk.models import AssayResultCreate

# "Next experiment" schema fields (what Agent 6 recommends testing)
GENE_FIELD = "Gene"
CELL_TYPE_FIELD = "Cell Type"
SPACER_FIELD = "Spacer"
PRIORITY_FIELD = "Priority"
RATIONALE_FIELD = "Rationale"

# "Experimental result" schema fields (what the wet-lab team records back)
INDEL_PCT_FIELD = "Indel %"
SOURCE_FIELD = "Source"


@dataclass
class ExperimentResult:
    gene: str
    cell_type: str
    spacer: str
    indel_pct: float
    recorded_at: datetime
    benchling_entity_id: str


class BenchlingClient:
    def __init__(
        self,
        api_key: str,
        tenant_url: str,
        next_experiment_schema_id: str,
        results_schema_id: str,
        project_id: str | None = None,
    ):
        self.next_experiment_schema_id = next_experiment_schema_id
        self.results_schema_id = results_schema_id
        self.project_id = project_id
        self.benchling = Benchling(url=tenant_url, auth_method=ApiKeyAuth(api_key))

    @classmethod
    def from_env(cls) -> "BenchlingClient":
        env = {
            "BENCHLING_API_KEY": os.environ.get("BENCHLING_API_KEY"),
            "BENCHLING_TENANT_URL": os.environ.get("BENCHLING_TENANT_URL"),
            "BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID": os.environ.get("BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID"),
            "BENCHLING_RESULTS_SCHEMA_ID": os.environ.get("BENCHLING_RESULTS_SCHEMA_ID"),
        }
        missing = [k for k, v in env.items() if not v]
        if missing:
            raise RuntimeError(
                f"Missing from .env: {', '.join(missing)}. See agent8_benchling_sync/README.md "
                "for what to create in Benchling and how to find these values."
            )
        return cls(
            env["BENCHLING_API_KEY"],
            env["BENCHLING_TENANT_URL"],
            env["BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID"],
            env["BENCHLING_RESULTS_SCHEMA_ID"],
            os.environ.get("BENCHLING_PROJECT_ID"),
        )

    def push_next_experiment(self, gene: str, cell_type: str, spacer: str, priority: float, rationale: str) -> None:
        """Write Agent 6's top recommendation to Benchling so the wet-lab team can see what
        to run next. Called once per recommend() run — see run.py."""
        result = AssayResultCreate(
            schema_id=self.next_experiment_schema_id,
            project_id=self.project_id,
            fields=fields(
                {
                    GENE_FIELD: {"value": gene},
                    CELL_TYPE_FIELD: {"value": cell_type},
                    SPACER_FIELD: {"value": spacer},
                    PRIORITY_FIELD: {"value": priority},
                    RATIONALE_FIELD: {"value": rationale},
                }
            ),
        )
        self.benchling.assay_results.create([result])

    def fetch_new_results(self, since: datetime | None = None) -> list[ExperimentResult]:
        """Pull guide experiment results recorded in Benchling since `since` (or all, if
        None). Feeds agent6_next_experiment/recommend.py's `record` subcommand — one
        `record` call per ExperimentResult returned here."""
        kwargs = {"schema_id": self.results_schema_id}
        if since is not None:
            kwargs["modified_atgte"] = since.astimezone(timezone.utc).isoformat()

        out = []
        for page in self.benchling.assay_results.list(**kwargs):
            for result in page:
                f = result.fields.to_dict()
                out.append(
                    ExperimentResult(
                        gene=f[GENE_FIELD]["value"],
                        cell_type=f[CELL_TYPE_FIELD]["value"],
                        spacer=f[SPACER_FIELD]["value"],
                        indel_pct=float(f[INDEL_PCT_FIELD]["value"]),
                        recorded_at=result.modified_at,
                        benchling_entity_id=result.id,
                    )
                )
        return out
