"""
Agent 8 — Benchling sync (CellGuide AI pipeline, see ../CLAUDE.md).

STUB — no Benchling account/API key is available yet. Every method below raises
NotImplementedError with what's needed to make it real. Nothing here makes a network call.

To complete this integration, you need:
  1. A Benchling API key (Settings -> Developer Console -> API keys in your tenant)
  2. Your tenant subdomain, e.g. "your-org" for https://your-org.benchling.com
  3. The schema ID (or name) of the custom entity / result table your workspace uses to
     record CRISPR guide experiment results (gene, cell type, spacer, indel %) — this is
     workspace-specific and can't be guessed; check Benchling's Feature Library / schema
     registry for whatever your team already uses, or create one for this pipeline.

Benchling's REST API is documented at https://benchling.com/api/reference — the relevant
resources are almost certainly `custom-entities` or `results` (POST to write, GET with
`schemaId` + `modifiedAt>` filters to read incrementally).
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExperimentResult:
    gene: str
    cell_type: str
    spacer: str
    indel_pct: float
    recorded_at: datetime
    benchling_entity_id: str


class BenchlingClient:
    def __init__(self, api_key: str, tenant: str, results_schema_id: str):
        """
        api_key: Benchling API key (Bearer token)
        tenant: subdomain, e.g. "your-org" (base URL becomes https://your-org.benchling.com)
        results_schema_id: schema ID of the custom entity/result type holding guide results
        """
        self.api_key = api_key
        self.tenant = tenant
        self.results_schema_id = results_schema_id

    def fetch_new_results(self, since: datetime | None = None) -> list[ExperimentResult]:
        """Pull experiment results recorded in Benchling since `since` (or all, if None).

        Intended to feed agent6_next_experiment/recommend.py's `record` subcommand — one
        `record` call per ExperimentResult returned here.
        """
        raise NotImplementedError(
            "Needs a Benchling API key + tenant + results schema ID. "
            "GET https://{tenant}.benchling.com/api/v2/custom-entities?schemaId={results_schema_id}"
            "&modifiedAt>{since.isoformat()}, then map each entity's fields to ExperimentResult."
        )

    def push_ranking_update(self, gene: str, cell_type: str, combined_score: float, confidence: float) -> None:
        """Write Agent 3's updated combined_score + Agent 5's confidence back to Benchling
        for the matching entity, so ranking state stays visible in the lab notebook."""
        raise NotImplementedError(
            "Needs the Benchling entity ID to PATCH (look it up by gene/cell_type first), "
            "then PATCH https://{tenant}.benchling.com/api/v2/custom-entities/{entity_id} "
            "with the combined_score/confidence fields."
        )
