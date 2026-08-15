"""
Agent 8 — Benchling sync (CellGuide AI pipeline, see ../CLAUDE.md).

Uses the official `benchling-sdk` package to close the loop from the sponsor flow:

    Guide ranking -> Next experiment -> Benchling -> Experimental result -> AIFG re-runs

i.e. Agent 6's top recommendation gets written to Benchling (so the wet-lab team sees what
to run next), and once they've recorded a real result there, this pulls it back so Agent 6
can `record` it and re-rank.

Implemented against **Custom Entity** schemas (not Assay Result schemas — that's what
actually got created in the Hackathon26/AIFG workspace; Custom Entities are Benchling's
general-purpose "things in the registry" type, scoped by folder_id rather than project_id,
and — unlike Results — *can* be updated in place, though this client always creates fresh
records for a simple, auditable history instead of mutating one entity in place).

Requires, in `../.env`:
  BENCHLING_API_KEY                    - Basic-auth API key (Benchling -> Developer Console -> API keys)
  BENCHLING_TENANT_URL                 - e.g. https://hackathon26.bnchdev.org
  BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID  - schema ID for "what to test next" records (Custom Entity schema)
  BENCHLING_RESULTS_SCHEMA_ID          - schema ID for recorded experimental results (Custom Entity schema)
  BENCHLING_FOLDER_ID                  - the AIFG folder's ID (find both with list_resources.py)

Field names below (GENE_FIELD etc.) must match your schemas' field *names* exactly
(Benchling UI: schema field "name", not necessarily what's displayed) — edit them if you
name the fields differently when creating the schemas.
"""

import os
from dataclasses import dataclass
from datetime import datetime

from benchling_sdk.auth.api_key_auth import ApiKeyAuth
from benchling_sdk.benchling import Benchling
from benchling_sdk.helpers.serialization_helpers import fields
from benchling_sdk.models import CustomEntityCreate

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
        folder_id: str,
    ):
        self.next_experiment_schema_id = next_experiment_schema_id
        self.results_schema_id = results_schema_id
        self.folder_id = folder_id
        self.benchling = Benchling(url=tenant_url, auth_method=ApiKeyAuth(api_key))

    @classmethod
    def from_env(cls) -> "BenchlingClient":
        env = {
            "BENCHLING_API_KEY": os.environ.get("BENCHLING_API_KEY"),
            "BENCHLING_TENANT_URL": os.environ.get("BENCHLING_TENANT_URL"),
            "BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID": os.environ.get("BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID"),
            "BENCHLING_RESULTS_SCHEMA_ID": os.environ.get("BENCHLING_RESULTS_SCHEMA_ID"),
            "BENCHLING_FOLDER_ID": os.environ.get("BENCHLING_FOLDER_ID"),
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
            env["BENCHLING_FOLDER_ID"],
        )

    def push_next_experiment(self, gene: str, cell_type: str, spacer: str, priority: float, rationale: str) -> None:
        """Write Agent 6's top recommendation to Benchling so the wet-lab team can see what
        to run next. Called once per recommend() run — see run.py."""
        entity = CustomEntityCreate(
            schema_id=self.next_experiment_schema_id,
            folder_id=self.folder_id,
            name=f"{gene} ({cell_type})",
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
        self.benchling.custom_entities.create(entity)

    def fetch_new_results(self, since: datetime | None = None) -> list[ExperimentResult]:
        """Pull guide experiment results recorded in Benchling since `since` (or all, if
        None). Feeds agent6_next_experiment/recommend.py's `record` subcommand — one
        `record` call per ExperimentResult returned here."""
        out = []
        for page in self.benchling.custom_entities.list(schema_id=self.results_schema_id):
            for entity in page:
                if since is not None and entity.modified_at is not None and entity.modified_at < since:
                    continue
                f = entity.fields.to_dict()
                out.append(
                    ExperimentResult(
                        gene=f[GENE_FIELD]["value"],
                        cell_type=f[CELL_TYPE_FIELD]["value"],
                        spacer=f[SPACER_FIELD]["value"],
                        indel_pct=float(f[INDEL_PCT_FIELD]["value"]),
                        recorded_at=entity.modified_at,
                        benchling_entity_id=entity.id,
                    )
                )
        return out
