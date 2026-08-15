#!/usr/bin/env python3
"""
Agent 6 — next-experiment recommendation (CellGuide AI pipeline, see ../CLAUDE.md).

Deterministic (no LLM). Two subcommands:

  recommend   Rank untested candidate guides by (expected value x uncertainty) and print
              the top picks — the guides most worth spending a real experiment on.
  record      Append a real experimental result to the log, then immediately re-run
              `recommend` so the ranking (and the next pick) reflects the new data.

Priority = recommended_score * uncertainty, where uncertainty prefers Agent 5's calibrated
confidence (output/confidence.json, confidence_numeric) when available for that
gene/cell_type, and otherwise falls back to a transparent proxy: the population standard
deviation across the three score components (sequence_efficacy, accessibility,
specificity) — guides where the three components disagree with each other are exactly the
ones a single combined score is least trustworthy for, so they're worth testing first.

Already-tested (gene, cell_type, spacer) triples are excluded from `recommend`.

Usage:
    uv run agent6_next_experiment/recommend.py recommend --candidates ../agent4_benchmarking/output/results.csv --top 5
    uv run agent6_next_experiment/recommend.py record --gene GZMA --cell-type T --spacer GACC... --indel-pct 88.0
"""

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
STATE_DIR = HERE / "state"
OUTPUT_DIR = HERE / "output"
LOG_PATH = STATE_DIR / "experiment_log.csv"
CONFIDENCE_PATH = HERE.parent / "agent5_confidence_assessment" / "output" / "confidence.json"

LOG_FIELDS = ["gene", "cell_type", "spacer", "indel_pct", "source", "recorded_at"]


def load_confidence() -> dict[tuple, float]:
    """{(gene, cell_type): confidence_numeric in [0,1]} from Agent 5's output, if present."""
    if not CONFIDENCE_PATH.exists():
        return {}
    entries = json.loads(CONFIDENCE_PATH.read_text())
    return {
        (e["gene"], e.get("cell_type")): e["confidence_numeric"]
        for e in entries
        if "confidence_numeric" in e
    }


def load_tested() -> set[tuple]:
    if not LOG_PATH.exists():
        return set()
    with open(LOG_PATH, newline="") as f:
        return {(r["gene"], r["cell_type"], r["spacer"]) for r in csv.DictReader(f)}


def uncertainty(row: pd.Series, confidence_by_gene: dict[tuple, float]) -> float:
    key = (row.get("gene"), row.get("cell_type"))
    if key in confidence_by_gene:
        return 1.0 - confidence_by_gene[key]  # low Agent-5 confidence -> high uncertainty
    components = [v for v in (row.get("sequence_efficacy"), row.get("accessibility"), row.get("specificity")) if pd.notna(v)]
    if len(components) < 2:
        return 0.5  # not enough signal to estimate disagreement — neutral prior
    return statistics.pstdev(components)


def cmd_recommend(args: argparse.Namespace) -> None:
    df = pd.read_csv(args.candidates)
    tested = load_tested()
    confidence_by_gene = load_confidence()

    df = df[~df.apply(lambda r: (r.get("gene"), r.get("cell_type"), r.get("spacer")) in tested, axis=1)]
    if df.empty:
        print("No untested candidates left in this candidate set.")
        return

    score_col = "recommended_score" if "recommended_score" in df.columns else "combined_score"
    df["uncertainty"] = df.apply(lambda r: uncertainty(r, confidence_by_gene), axis=1)
    df["priority"] = df[score_col] * df["uncertainty"]
    ranked = df.sort_values("priority", ascending=False).head(args.top)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(OUTPUT_DIR / "recommendations.csv", index=False)

    print(f"Top {len(ranked)} next-experiment recommendations (of {len(df)} untested candidates):\n")
    for row in ranked.itertuples():
        cell_type = getattr(row, "cell_type", None)
        label = f"{row.gene} ({cell_type})" if pd.notna(cell_type) else row.gene
        print(
            f"  {label}: priority={row.priority:.3f} "
            f"({score_col}={getattr(row, score_col):.3f}, uncertainty={row.uncertainty:.3f})"
        )
    print(f"\nWrote {OUTPUT_DIR / 'recommendations.csv'}")


def cmd_record(args: argparse.Namespace) -> None:
    import datetime

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    is_new = not LOG_PATH.exists()
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(
            {
                "gene": args.gene,
                "cell_type": args.cell_type,
                "spacer": args.spacer,
                "indel_pct": args.indel_pct,
                "source": args.source,
                "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        )
    print(f"Recorded: {args.gene} ({args.cell_type}) indel%={args.indel_pct} -> {LOG_PATH}")

    if args.candidates:
        print("\nRe-ranking with the new result excluded from candidates...\n")
        cmd_recommend(argparse.Namespace(candidates=args.candidates, top=args.top))


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 6 — next-experiment recommendation")
    sub = parser.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("recommend", help="Rank untested candidates by expected-value x uncertainty")
    rec.add_argument("--candidates", type=Path, required=True, help="CSV with gene, cell_type, spacer, recommended_score (or combined_score), and component columns")
    rec.add_argument("--top", type=int, default=5)
    rec.set_defaults(func=cmd_recommend)

    rec_result = sub.add_parser("record", help="Log a real experimental result and re-rank")
    rec_result.add_argument("--gene", required=True)
    rec_result.add_argument("--cell-type", required=True)
    rec_result.add_argument("--spacer", required=True)
    rec_result.add_argument("--indel-pct", type=float, required=True)
    rec_result.add_argument("--source", default="manual")
    rec_result.add_argument("--candidates", type=Path, default=None, help="If given, re-run recommend after recording")
    rec_result.add_argument("--top", type=int, default=5)
    rec_result.set_defaults(func=cmd_record)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
