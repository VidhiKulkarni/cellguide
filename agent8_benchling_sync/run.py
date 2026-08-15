#!/usr/bin/env python3
"""
Agent 8 — Benchling sync (CellGuide AI pipeline, see ../CLAUDE.md).

Closes the loop: pull new results from the AIFG folder in Benchling -> feed each into
Agent 6's `record` (which re-ranks) -> push the fresh combined_score + Agent 5 confidence
back to Benchling so the lab notebook shows current ranking state.

    uv run agent8_benchling_sync/run.py                # sync everything
    uv run agent8_benchling_sync/run.py --dry-run      # show what would sync, write nothing
    uv run agent8_benchling_sync/run.py --no-push      # pull + re-rank, don't write back

Config lives in ../.env — see ../.env.example. No CLI flags for credentials.
"""

import argparse
import csv
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
RECOMMEND_SCRIPT = REPO_ROOT / "agent6_next_experiment" / "recommend.py"
RECOMMENDATIONS_CSV = REPO_ROOT / "agent6_next_experiment" / "output" / "recommendations.csv"

load_dotenv(REPO_ROOT / ".env")

from client import BenchlingClient  # noqa: E402  (must follow load_dotenv)


def record_result(result, candidates_csv):
    """Hand one Benchling result to Agent 6, which logs it and re-ranks."""
    subprocess.run(
        [
            sys.executable, str(RECOMMEND_SCRIPT), "record",
            "--gene", result.gene,
            "--cell-type", result.cell_type,
            "--spacer", result.spacer,
            "--indel-pct", str(result.indel_pct),
            "--source", "benchling",
            "--candidates", str(candidates_csv),
        ],
        check=True,
    )


def top_recommendation():
    """Read back Agent 6's current top pick, so we can publish it to Benchling."""
    if not RECOMMENDATIONS_CSV.exists():
        return None
    with open(RECOMMENDATIONS_CSV, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return rows[0] if rows else None


def sync(client, candidates_csv, push=True, dry_run=False):
    results = client.fetch_new_results()
    print("Benchling: {} result(s) in AIFG".format(len(results)))

    if dry_run:
        for result in results:
            print("  would record: {} / {} / {} -> {}%".format(
                result.gene, result.cell_type or "-", result.spacer or "-", result.indel_pct))
        return

    for result in results:
        record_result(result, candidates_csv)

    if not push:
        return

    top = top_recommendation()
    if top is None:
        print("No recommendations to push back.")
        return

    pushed = client.push_ranking_update(
        gene=top.get("gene", ""),
        cell_type=top.get("cell_type", ""),
        combined_score=float(top.get("combined_score") or 0.0),
        confidence=1.0 - float(top.get("uncertainty") or 0.0),
    )
    if pushed:
        print("Pushed updated ranking for {} back to Benchling.".format(top.get("gene")))
    else:
        print("No matching Benchling entity for {} — nothing pushed.".format(top.get("gene")))


def main():
    parser = argparse.ArgumentParser(description="Agent 8 — Benchling sync")
    parser.add_argument("--candidates", type=Path,
                        default=REPO_ROOT / "agent4_benchmarking" / "output" / "results.csv")
    parser.add_argument("--dry-run", action="store_true", help="show what would sync, write nothing")
    parser.add_argument("--no-push", dest="push", action="store_false",
                        help="pull and re-rank, but don't write back to Benchling")
    args = parser.parse_args()

    sync(BenchlingClient(), args.candidates, push=args.push, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
