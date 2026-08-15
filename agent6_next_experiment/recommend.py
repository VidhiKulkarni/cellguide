"""
Agent 6 — next-experiment recommendation (CellGuide AI pipeline, see ../CLAUDE.md).

Deterministic, no LLM, no API keys. Ranks untested candidate guides by

    priority = combined_score * uncertainty

so the top pick is the one that is both plausibly good and least well understood —
the experiment with the most information to gain.

Uncertainty comes from Agent 5's calibrated confidence when a candidate has one
(uncertainty = 1 - confidence_numeric). Otherwise it falls back to a transparent proxy:
the spread between Agent 3's three score components, on the reasoning that a guide whose
sequence/accessibility/specificity terms disagree is one the metric understands poorly.

Deliberately stdlib-only (no pandas), so it runs under plain `python3` without `uv sync`.

    python3 agent6_next_experiment/recommend.py recommend \
        --candidates agent4_benchmarking/output/results.csv --top 5

    python3 agent6_next_experiment/recommend.py record \
        --gene GZMA --cell-type T --spacer GACCTGAAGCTGAGCGAGTG --indel-pct 88.0 \
        --candidates agent4_benchmarking/output/results.csv --top 5
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENT_DIR.parent
LOG_PATH = AGENT_DIR / "state" / "experiment_log.csv"
OUTPUT_PATH = AGENT_DIR / "output" / "recommendations.csv"
CONFIDENCE_PATH = REPO_ROOT / "agent5_confidence_assessment" / "output" / "confidence.json"

LOG_FIELDS = ["gene", "cell_type", "spacer", "indel_pct", "source", "recorded_at"]
COMPONENTS = ["sequence_efficacy", "accessibility", "specificity"]


def resolve(path_str):
    """Accept paths relative to cwd, to the repo root, or to this agent's folder.

    The README documents `../agent4_benchmarking/...` while the command runs from the
    repo root, so both spellings have to work.
    """
    candidates = [Path(path_str), REPO_ROOT / path_str, AGENT_DIR / path_str]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    sys.exit(
        "Candidates file not found: {}\nTried:\n  {}".format(
            path_str, "\n  ".join(str(c) for c in candidates)
        )
    )


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def norm(value):
    """Normalize a key field. Agent 4's results.csv leaves cell_type blank on some rows."""
    return (value or "").strip()


# --------------------------------------------------------------------------- load


def load_candidates(path):
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        sys.exit("No candidate rows in {}".format(path))
    return rows


def load_confidence():
    """Map (gene, cell_type) -> confidence_numeric from Agent 5, if it has run.

    Also indexes by gene alone, because Agent 4's results.csv frequently has a blank
    cell_type while Agent 5's confidence.json records one (e.g. "T").
    """
    if not CONFIDENCE_PATH.exists():
        return {}, {}
    try:
        entries = json.loads(CONFIDENCE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print("  ! could not read {}: {}".format(CONFIDENCE_PATH.name, exc), file=sys.stderr)
        return {}, {}

    by_pair, by_gene = {}, {}
    for entry in entries:
        value = entry.get("confidence_numeric")
        if value is None:
            continue
        gene, cell_type = norm(entry.get("gene")), norm(entry.get("cell_type"))
        by_pair[(gene, cell_type)] = float(value)
        by_gene.setdefault(gene, float(value))
    return by_pair, by_gene


def load_log():
    """Return the set of already-tested keys, at both (gene, cell_type, spacer) and
    (gene, cell_type) granularity — candidate rows have no spacer column to match on."""
    tested_triples, tested_pairs, tested_genes = set(), set(), set()
    if not LOG_PATH.exists():
        return tested_triples, tested_pairs, tested_genes
    with open(LOG_PATH, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            gene, cell_type = norm(row.get("gene")), norm(row.get("cell_type"))
            tested_triples.add((gene, cell_type, norm(row.get("spacer"))))
            tested_pairs.add((gene, cell_type))
            tested_genes.add(gene)
    return tested_triples, tested_pairs, tested_genes


# ---------------------------------------------------------------------- scoring


def component_spread(row):
    """Fallback uncertainty: how much Agent 3's three components disagree, in [0, 1]."""
    values = [to_float(row.get(name)) for name in COMPONENTS if row.get(name) not in (None, "")]
    if len(values) < 2:
        return 0.5  # no basis to judge — sit at the midpoint rather than fake certainty
    return max(values) - min(values)


def uncertainty_for(row, by_pair, by_gene):
    gene, cell_type = norm(row.get("gene")), norm(row.get("cell_type"))
    confidence = by_pair.get((gene, cell_type))
    if confidence is None and cell_type == "":
        confidence = by_gene.get(gene)
    if confidence is not None:
        return max(0.0, min(1.0, 1.0 - confidence)), "agent5"
    return max(0.0, min(1.0, component_spread(row))), "component-spread"


def rank(rows, top):
    by_pair, by_gene = load_confidence()
    tested_triples, tested_pairs, tested_genes = load_log()

    ranked = []
    skipped = 0
    for row in rows:
        gene, cell_type = norm(row.get("gene")), norm(row.get("cell_type"))
        spacer = norm(row.get("spacer"))
        # Exact triple when we have one. Agent 4's results.csv carries neither spacer nor
        # cell_type, so fall back to progressively coarser keys rather than silently
        # re-recommending something the lab has already run.
        already_tested = (
            (gene, cell_type, spacer) in tested_triples
            or (spacer == "" and (gene, cell_type) in tested_pairs)
            or (spacer == "" and cell_type == "" and gene in tested_genes)
        )
        if already_tested:
            skipped += 1
            continue

        score = to_float(row.get("combined_score"))
        unc, source = uncertainty_for(row, by_pair, by_gene)
        entry = dict(row)
        entry["uncertainty"] = round(unc, 6)
        entry["uncertainty_source"] = source
        entry["priority"] = round(score * unc, 6)
        ranked.append(entry)

    ranked.sort(key=lambda r: r["priority"], reverse=True)
    return ranked[:top], skipped, len(ranked)


def write_recommendations(ranked):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ranked:
        OUTPUT_PATH.write_text("", encoding="utf-8")
        return
    fieldnames = list(ranked[0].keys())
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ranked)


# --------------------------------------------------------------------- commands


def cmd_recommend(args):
    rows = load_candidates(resolve(args.candidates))
    ranked, skipped, remaining = rank(rows, args.top)

    print("Candidates: {} total, {} already tested, {} eligible".format(
        len(rows), skipped, remaining))

    if not ranked:
        print("\nNothing left to recommend — every candidate is in the experiment log.")
        write_recommendations(ranked)
        return

    print("\nTop {} next experiments (priority = combined_score x uncertainty):\n".format(
        len(ranked)))
    print("  {:<12} {:<6} {:>9} {:>9} {:>9}  {}".format(
        "gene", "cell", "score", "uncert", "priority", "uncertainty from"))
    for entry in ranked:
        print("  {:<12} {:<6} {:>9.4f} {:>9.4f} {:>9.4f}  {}".format(
            norm(entry.get("gene"))[:12],
            norm(entry.get("cell_type"))[:6] or "-",
            to_float(entry.get("combined_score")),
            entry["uncertainty"],
            entry["priority"],
            entry["uncertainty_source"],
        ))

    write_recommendations(ranked)
    print("\nWrote {}".format(OUTPUT_PATH.relative_to(REPO_ROOT)))

    if all(e["uncertainty_source"] == "component-spread" for e in ranked):
        print("\nNote: no Agent 5 confidence matched these rows — uncertainty is the "
              "component-spread proxy. Run Agent 5 for calibrated values.")


def cmd_record(args):
    """Append a real experimental result, then immediately re-rank — this is the loop."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    is_new = not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0

    with open(LOG_PATH, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({
            "gene": args.gene,
            "cell_type": args.cell_type,
            "spacer": args.spacer,
            "indel_pct": args.indel_pct,
            "source": args.source,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        })

    print("Recorded: {} / {} / {} -> {}% indel (source: {})\n".format(
        args.gene, args.cell_type, args.spacer, args.indel_pct, args.source))
    cmd_recommend(args)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_shared(sub):
        sub.add_argument("--candidates", required=True,
                         help="CSV of scored candidates (e.g. agent4_benchmarking/output/results.csv)")
        sub.add_argument("--top", type=int, default=5, help="how many to recommend (default 5)")

    recommend_parser = subparsers.add_parser("recommend", help="rank current candidates")
    add_shared(recommend_parser)
    recommend_parser.set_defaults(func=cmd_recommend)

    record_parser = subparsers.add_parser("record", help="log a real result, then re-rank")
    record_parser.add_argument("--gene", required=True)
    record_parser.add_argument("--cell-type", required=True, dest="cell_type")
    record_parser.add_argument("--spacer", required=True)
    record_parser.add_argument("--indel-pct", required=True, type=float, dest="indel_pct")
    record_parser.add_argument("--source", default="manual",
                               help="where the result came from (e.g. 'benchling', default 'manual')")
    add_shared(record_parser)
    record_parser.set_defaults(func=cmd_record)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
