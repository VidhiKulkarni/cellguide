#!/usr/bin/env python3
"""
Agent 9 (match step) — literature cross-reference for CellGuide AI (see ../CLAUDE.md).

Deterministic (no LLM). Combines:
  1. Real Azimuth-scored candidate guides for a gene, via
     agent3_metric_construction/score_new_gene.py (real Ensembl coordinates, real genomic
     sequence, real PAM scan, real Azimuth model).
  2. search_literature.py's output (output/<gene>/literature_guides.json) — guide sequences
     explicitly reported in the literature, with efficiency + biological context.

...and does an EXACT sequence match (forward strand + reverse complement — a guide can be
deposited in either orientation in a supplementary table) between the two. Whether a
high-scoring model guide "has been reported before" is answered by string comparison here,
not asked of the search-step LLM.

Requires step 1 to have already been run for this gene (search_literature.py) — this script
does not invoke the LLM step itself, matching this pipeline's convention that each stage's
output is the next stage's input, run in order (see ../CLAUDE.md's pipeline table). If no
literature_guides.json is found, this still reports Azimuth scores, but says explicitly
that no literature check was run — never reports a guide as "not previously found" when the
search was never actually performed.

Usage:
    uv run agent9_guide_literature_match/match_guides.py BCL11A --top 10
    uv run agent9_guide_literature_match/match_guides.py BCL11A --top 10 --atac-signal 0.42 --cell-type "CD34+ HSPC"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"

sys.path.insert(0, str(REPO_ROOT / "agent3_metric_construction"))
from genome_lookup import _reverse_complement  # noqa: E402
from score_new_gene import run as score_gene  # noqa: E402


def load_literature_guides(gene: str) -> Optional[dict]:
    path = OUTPUT_DIR / gene / "literature_guides.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def match(gene: str, top: int, atac_signal: Optional[float], cell_type: Optional[str]) -> dict:
    score_report = score_gene(gene, atac_signal=atac_signal, cell_type=cell_type, top=top)
    literature = load_literature_guides(gene)

    result: dict = {
        "gene": gene,
        "scoring_status": score_report["status"],
        "scoring_messages": score_report["messages"],
        "literature_search_run": literature is not None,
        "guides": [],
    }

    if literature is None:
        result["messages"] = [
            f"No literature search results found for {gene} — run "
            f"`uv run agent9_guide_literature_match/search_literature.py {gene}` first. "
            "Azimuth scores below are real, but 'previously reported' status is UNKNOWN, "
            "not 'no' — that distinction matters, so it's kept explicit rather than defaulting "
            "every guide to 'not found'."
        ]
    else:
        result["search_queries_tried"] = literature.get("search_queries_tried", [])
        result["papers_found_relevant"] = literature.get("papers_found_relevant", [])
        result["search_notes"] = literature.get("notes", "")

    if score_report["status"] != "OK":
        return result

    reported = literature["reported_guides"] if literature else []
    reported_by_seq = {}
    for r in reported:
        seq = r["sequence"].upper().strip()
        reported_by_seq[seq] = r
        reported_by_seq[_reverse_complement(seq)] = r  # guides can be deposited in either orientation

    for g in score_report["guides"]:
        spacer = g["spacer"].upper()
        hit = reported_by_seq.get(spacer)
        result["guides"].append({
            **g,
            "previously_reported": hit is not None if literature is not None else None,
            "literature_match": hit,
        })

    return result


def render_report(result: dict) -> str:
    lines = [f"# Agent 9 — literature cross-reference for {result['gene']}", ""]

    if result["scoring_status"] != "OK":
        lines.append(f"Scoring failed: `{result['scoring_status']}`")
        lines.extend(f"- {m}" for m in result["scoring_messages"])
        return "\n".join(lines) + "\n"

    if not result["literature_search_run"]:
        lines.extend(result["messages"])
        lines.append("")
    else:
        lines.append(f"Search queries tried: {result.get('search_queries_tried') or '(none recorded)'}")
        lines.append(f"Papers found relevant: {result.get('papers_found_relevant') or '(none)'}")
        if result.get("search_notes"):
            lines.append(f"Search notes: {result['search_notes']}")
        lines.append("")
        n_matched = sum(1 for g in result["guides"] if g["previously_reported"])
        lines.append(f"**{n_matched}/{len(result['guides'])}** top-scoring guides matched a sequence explicitly reported in the literature search.\n")

    lines.append("| Spacer | recommended_score | sequence_efficacy_source | Previously reported? | Reported efficiency | Context | Source |")
    lines.append("|---|---|---|---|---|---|---|")
    for g in result["guides"]:
        if g["previously_reported"] is True:
            m = g["literature_match"]
            lines.append(
                f"| `{g['spacer']}` | {g['recommended_score']:.3f} | {g['sequence_efficacy_source'][:40]}... | "
                f"✅ yes | {m.get('efficiency', '?')} | {m.get('cell_type', '?')} / {m.get('delivery', '?')} | {m.get('source', '?')} |"
            )
        elif g["previously_reported"] is False:
            lines.append(
                f"| `{g['spacer']}` | {g['recommended_score']:.3f} | {g['sequence_efficacy_source'][:40]}... | "
                f"not found | — | — | — |"
            )
        else:
            lines.append(
                f"| `{g['spacer']}` | {g['recommended_score']:.3f} | {g['sequence_efficacy_source'][:40]}... | "
                f"unknown (no search run) | — | — | — |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 9 (match step) — cross-reference Azimuth-scored guides against literature")
    parser.add_argument("gene")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--atac-signal", type=float, default=None)
    parser.add_argument("--cell-type", default=None)
    args = parser.parse_args()

    result = match(args.gene, args.top, args.atac_signal, args.cell_type)

    gene_dir = OUTPUT_DIR / args.gene
    gene_dir.mkdir(parents=True, exist_ok=True)
    (gene_dir / "match_result.json").write_text(json.dumps(result, indent=2))
    report = render_report(result)
    (gene_dir / "MATCH_REPORT.md").write_text(report)
    print(report)
    print(f"Wrote {gene_dir / 'match_result.json'} and {gene_dir / 'MATCH_REPORT.md'}")
    if result["scoring_status"] != "OK":
        sys.exit(1)


if __name__ == "__main__":
    main()
