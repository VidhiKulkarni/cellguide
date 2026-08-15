#!/usr/bin/env python3
"""
Agent 8 — Benchling sync (CellGuide AI pipeline, see ../CLAUDE.md).

STUB pipeline glue — not runnable yet (see client.py for what's missing). Once
BenchlingClient is implemented, this loop is: pull new results from Benchling -> feed each
into Agent 6's `record` (updates the ranking) -> push the new top ranking + Agent 5's
confidence back to Benchling.

Usage (once client.py is implemented):
    uv run agent8_benchling_sync/run.py --tenant your-org --schema-id <id>
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from client import BenchlingClient

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
RECOMMEND_SCRIPT = REPO_ROOT / "agent6_next_experiment" / "recommend.py"


def sync(client: BenchlingClient, candidates_csv: Path) -> None:
    for result in client.fetch_new_results():
        subprocess.run(
            [
                sys.executable,
                str(RECOMMEND_SCRIPT),
                "record",
                "--gene", result.gene,
                "--cell-type", result.cell_type,
                "--spacer", result.spacer,
                "--indel-pct", str(result.indel_pct),
                "--source", "benchling",
                "--candidates", str(candidates_csv),
            ],
            check=True,
        )
        # TODO once push_ranking_update is implemented: read the fresh recommendations.csv
        # row for (result.gene, result.cell_type) and client.push_ranking_update(...) it back.


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 8 — Benchling sync (stub)")
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--schema-id", required=True)
    parser.add_argument("--candidates", type=Path, default=REPO_ROOT / "agent4_benchmarking" / "output" / "results.csv")
    args = parser.parse_args()

    api_key = os.environ.get("BENCHLING_API_KEY")
    if not api_key:
        sys.exit("BENCHLING_API_KEY not set — add it to .env once you have a Benchling account (see client.py docstring)")

    client = BenchlingClient(api_key=api_key, tenant=args.tenant, results_schema_id=args.schema_id)
    sync(client, args.candidates)


if __name__ == "__main__":
    main()
