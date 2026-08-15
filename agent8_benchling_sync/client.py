"""
Agent 8 — Benchling sync (CellGuide AI pipeline, see ../CLAUDE.md).

Talks to the re:AGENT hackathon tenant, whose shape differs from a standard Benchling
deployment in three ways the original stub guessed wrong:

  1. Host is `hackathon26.bnchdev.org`, NOT `<tenant>.benchling.com`. Pass the full base
     URL, don't build it from a subdomain.
  2. Auth is OAuth2 client-credentials via a Developer Console **App** (client_id +
     client_secret), not a Bearer API key.
  3. Data lives in project `Hackathon26`, folder `AIFG` — writes must be addressed to that
     folder or they land somewhere nobody is looking.

Config comes from ../.env (see .env.example):
    BENCHLING_TENANT_URL, BENCHLING_CLIENT_ID, BENCHLING_CLIENT_SECRET,
    BENCHLING_AIFG_FOLDER_ID, BENCHLING_RESULTS_SCHEMA_ID
"""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from benchling_sdk.auth.client_credentials_oauth2 import ClientCredentialsOAuth2
from benchling_sdk.benchling import Benchling

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TENANT_URL = "https://hackathon26.bnchdev.org"


@dataclass
class ExperimentResult:
    gene: str
    cell_type: str
    spacer: str
    indel_pct: float
    recorded_at: datetime
    benchling_entity_id: str


def _require(name, default=None):
    value = os.environ.get(name, default)
    if not value or str(value).startswith("paste_"):
        raise SystemExit(
            "{} is not set. Add it to {}/.env — see agent8_benchling_sync/README.md.".format(
                name, REPO_ROOT.name
            )
        )
    return value


class BenchlingClient:
    """Thin wrapper over benchling-sdk, scoped to the AIFG folder."""

    def __init__(self, tenant_url=None, client_id=None, client_secret=None,
                 folder_id=None, results_schema_id=None):
        self.tenant_url = tenant_url or os.environ.get("BENCHLING_TENANT_URL", DEFAULT_TENANT_URL)
        self.client_id = client_id or _require("BENCHLING_CLIENT_ID")
        self.client_secret = client_secret or _require("BENCHLING_CLIENT_SECRET")
        self.folder_id = folder_id or _require("BENCHLING_AIFG_FOLDER_ID")
        self.results_schema_id = results_schema_id or os.environ.get("BENCHLING_RESULTS_SCHEMA_ID")

        self._benchling = Benchling(
            url=self.tenant_url,
            auth_method=ClientCredentialsOAuth2(
                client_id=self.client_id, client_secret=self.client_secret
            ),
        )

    # ------------------------------------------------------------------ read

    def fetch_new_results(self, since=None):
        """Pull guide experiment results from the AIFG folder, newest first.

        Feeds agent6_next_experiment/recommend.py's `record` subcommand — one `record`
        call per ExperimentResult returned here.
        """
        kwargs = {"folder_id": self.folder_id}
        if self.results_schema_id:
            kwargs["schema_id"] = self.results_schema_id
        if since is not None:
            kwargs["modified_at"] = "> {}".format(since.isoformat())

        results = []
        for page in self._benchling.custom_entities.list(**kwargs):
            for entity in page:
                fields = getattr(entity, "fields", None) or {}

                def field(name, default=""):
                    """Entity fields come back as {name: {value: ...}} or plain values."""
                    raw = fields.get(name) if hasattr(fields, "get") else None
                    if raw is None:
                        return default
                    value = getattr(raw, "value", None)
                    return value if value is not None else (raw if not hasattr(raw, "value") else default)

                indel = field("indel_pct", None)
                try:
                    indel = float(indel)
                except (TypeError, ValueError):
                    continue  # not a guide-result entity — skip rather than guess

                results.append(ExperimentResult(
                    gene=str(field("gene")),
                    cell_type=str(field("cell_type")),
                    spacer=str(field("spacer")),
                    indel_pct=indel,
                    recorded_at=getattr(entity, "modified_at", None) or datetime.now(),
                    benchling_entity_id=getattr(entity, "id", ""),
                ))
        return results

    # ----------------------------------------------------------------- write

    def push_ranking_update(self, gene, cell_type, combined_score, confidence):
        """Write Agent 3's combined_score and Agent 5's confidence back onto the matching
        entity, so ranking state stays visible in the lab notebook."""
        entity_id = self._find_entity_id(gene, cell_type)
        if entity_id is None:
            return False

        from benchling_sdk.models import CustomEntityUpdate, Fields

        self._benchling.custom_entities.update(
            entity_id=entity_id,
            entity=CustomEntityUpdate(
                fields=Fields.from_dict({
                    "combined_score": {"value": float(combined_score)},
                    "confidence": {"value": float(confidence)},
                })
            ),
        )
        return True

    def _find_entity_id(self, gene, cell_type):
        for result in self.fetch_new_results():
            if result.gene == gene and (not cell_type or result.cell_type == cell_type):
                return result.benchling_entity_id
        return None
