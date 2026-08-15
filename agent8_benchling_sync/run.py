#!/usr/bin/env python3
"""
Agent 8 — Benchling sync (CellGuide AI pipeline, see ../CLAUDE.md).

Closes the loop end-to-end:
  1. Pull any new results Benchling has for guides Agent 6 doesn't know about yet ->
     feed each into agent6_next_experiment/recommend.py's `record` (updates the ranking).
  2. Push Agent 6's new top recommendation to Benchling as the next experiment to run.

Requires BENCHLING_API_KEY, BENCHLING_TENANT_URL, BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID,
BENCHLING_RESULTS_SCHEMA_ID in ../.env — see README.md for what to set up in Benchling
first. Not runnable until those exist.

Usage:
    uv run agent8_benchling_sync/run.py --candidates ../agent4_benchmarking/output/results.csv
"""

import argparse
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
RECOMMEND_SCRIPT = REPO_ROOT / "agent6_next_experiment" / "recommend.py"

load_dotenv(REPO_ROOT / ".env")
sys.path.insert(0, str(HERE))
from client import BenchlingClient  # noqa: E402


def sync(client: BenchlingClient, candidates_csv: Path) -> None:
    new_results = client.fetch_new_results()
    print(f"Found {len(new_results)} new result(s) in Benchling.")
    for result in new_results:
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

    recommend = subprocess.run(
        [sys.executable, str(RECOMMEND_SCRIPT), "recommend", "--candidates", str(candidates_csv), "--top", "1"],
        check=True, capture_output=True, text=True,
    )
    print(recommend.stdout)

    import pandas as pd
    top = pd.read_csv(HERE.parent / "agent6_next_experiment" / "output" / "recommendations.csv").iloc[0]
    client.push_next_experiment(
        gene=top["gene"],
        cell_type=top.get("cell_type", ""),
        spacer=top.get("spacer", ""),
        priority=top["priority"],
        rationale=f"combined_score={top['combined_score']:.3f}, uncertainty={top['uncertainty']:.3f}",
    )
    print(f"Pushed next-experiment recommendation to Benchling: {top['gene']} ({top.get('cell_type', '?')})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 8 — Benchling sync")
    parser.add_argument("--candidates", type=Path, default=REPO_ROOT / "agent4_benchmarking" / "output" / "results.csv")
    args = parser.parse_args()

    client = BenchlingClient.from_env()
    sync(client, args.candidates)


if __name__ == "__main__":
    main()
