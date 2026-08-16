#!/usr/bin/env python3
"""
Agent 7 — provenance tracking (CellGuide AI pipeline, see ../CLAUDE.md).

Deterministic (no LLM): links every guide score/claim/decision back to its supporting
paper, experimental context, extracted evidence, and validation result, by combining:
  - agent3's SPEC.md (which paper backs each score component — parsed, not hand-copied,
    so this can't silently drift from SPEC.md)
  - agent2's per-paper SUMMARY.md (the extracted evidence for each cited paper)
  - agent4's REPORT.md / results.csv (validation outcome), when present
  - agent5's CONFIDENCE_REPORT.md (skeptic's assessment), when present

Read-only outside this folder — writes only under output/.

Usage:
    uv run agent7_provenance/build.py [--results path/to/agent4/results.csv]
"""

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"

SPEC_PATH = REPO_ROOT / "agent3_metric_construction" / "SPEC.md"
PAPERS_DIR = REPO_ROOT / "papers"
AGENT1_RELATED = REPO_ROOT / "agent1_literature_search" / "output" / "related"
AGENT2_RELATED = REPO_ROOT / "agent2_literature_summarization" / "output" / "related"
AGENT4_REPORT = REPO_ROOT / "agent4_benchmarking" / "output" / "REPORT.md"
AGENT4_RESULTS = REPO_ROOT / "agent4_benchmarking" / "output" / "results.csv"
AGENT5_REPORT = REPO_ROOT / "agent5_confidence_assessment" / "output" / "CONFIDENCE_REPORT.md"

# Known paper slugs, resolved to wherever they actually live post-reorg.
KNOWN_SLUGS: dict[str, Path] = {p.name: p for p in PAPERS_DIR.iterdir() if p.is_dir()}
if AGENT1_RELATED.exists():
    KNOWN_SLUGS.update({p.name: p for p in AGENT1_RELATED.iterdir() if p.is_dir()})

SLUG_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{4,}")


def extract_slugs(text: str) -> list[str]:
    """Every token in `text` that matches a known paper slug, in first-seen order."""
    seen = []
    for tok in SLUG_TOKEN_RE.findall(text):
        if tok in KNOWN_SLUGS and tok not in seen:
            seen.append(tok)
    return seen


def paper_summary_snippet(slug: str, max_chars: int = 400) -> str | None:
    """Pull the first non-empty lines of a paper's SUMMARY.md as its evidence snippet."""
    for candidate in (AGENT2_RELATED / slug / "SUMMARY.md", PAPERS_DIR / slug / "SUMMARY.md"):
        if candidate.exists():
            text = candidate.read_text().strip()
            return text[:max_chars] + ("..." if len(text) > max_chars else "")
    return None


def parse_component_sources() -> dict[str, dict]:
    """Split SPEC.md into '## Component N — name' sections and extract each one's cited
    paper slugs + full prose, so this stays in sync with SPEC.md instead of duplicating it."""
    spec_text = SPEC_PATH.read_text()
    # Split on every "## " heading (not just "## Component ...") so a component section
    # stops at the *next* heading of any kind, instead of swallowing the rest of the file.
    all_sections = re.split(r"(?m)^## ", spec_text)[1:]
    components = {}
    for section in all_sections:
        header, _, body = section.partition("\n")
        if not header.startswith("Component "):
            continue
        header = header.split("—", 1)[-1].strip()
        name_match = re.match(r"`(\w+)\(", header)
        name = name_match.group(1) if name_match else header.strip()
        components[name] = {
            "spec_text": (header + "\n" + body).strip(),
            "cited_papers": extract_slugs(header + " " + body),
        }
    return components


def load_results(results_path: Path | None) -> pd.DataFrame | None:
    path = results_path or AGENT4_RESULTS
    if not path.exists():
        return None
    return pd.read_csv(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 7 — provenance tracking")
    parser.add_argument("--results", type=Path, default=None, help="Agent 4 results.csv to attach validation provenance for")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    components = parse_component_sources()
    for name, info in components.items():
        info["sources"] = {
            slug: {"path": str(KNOWN_SLUGS[slug].relative_to(REPO_ROOT)), "evidence": paper_summary_snippet(slug)}
            for slug in info["cited_papers"]
        }

    provenance = {
        "score_components": components,
        "validation": {
            "report": str(AGENT4_REPORT.relative_to(REPO_ROOT)) if AGENT4_REPORT.exists() else None,
            "results_csv": str(AGENT4_RESULTS.relative_to(REPO_ROOT)) if AGENT4_RESULTS.exists() else None,
        },
        "confidence_assessment": {
            "report": str(AGENT5_REPORT.relative_to(REPO_ROOT)) if AGENT5_REPORT.exists() else None,
        },
    }

    results_df = load_results(args.results)
    per_guide = []
    if results_df is not None:
        for row in results_df.itertuples():
            per_guide.append(
                {
                    "gene": getattr(row, "gene", None),
                    "cell_type": getattr(row, "cell_type", None),
                    "combined_score": getattr(row, "combined_score", None),
                    "sequence_efficacy": {
                        "value": getattr(row, "sequence_efficacy", None),
                        "sources": list(components.get("sequence_efficacy", {}).get("sources", {}).keys()),
                    },
                    "accessibility": {
                        "value": getattr(row, "accessibility", None),
                        "sources": list(components.get("accessibility", {}).get("sources", {}).keys()),
                    },
                }
            )
    provenance["per_guide"] = per_guide

    (OUTPUT_DIR / "provenance.json").write_text(json.dumps(provenance, indent=2))

    lines = ["# Agent 7 — provenance report", ""]
    for name, info in components.items():
        lines.append(f"## `{name}`")
        lines.append("")
        for slug, src in info["sources"].items():
            lines.append(f"- **{slug}** (`{src['path']}`)")
            if src["evidence"]:
                lines.append(f"  > {src['evidence'][:200].replace(chr(10), ' ')}")
        lines.append("")
    if per_guide:
        lines.append(f"## Per-guide provenance ({len(per_guide)} guides)")
        lines.append("")
        lines.append("See `provenance.json` — every combined_score's three components are linked to the")
        lines.append("same source papers listed above.")
    else:
        lines.append("## Per-guide provenance")
        lines.append("")
        lines.append("No `results.csv` found yet (run agent4_benchmarking first) — component-level")
        lines.append("provenance above is still valid on its own.")

    (OUTPUT_DIR / "PROVENANCE_REPORT.md").write_text("\n".join(lines) + "\n")
    print(f"Wrote {OUTPUT_DIR / 'provenance.json'} and {OUTPUT_DIR / 'PROVENANCE_REPORT.md'}")
    print(f"Components traced: {list(components.keys())}")
    for name, info in components.items():
        print(f"  {name}: {list(info['sources'].keys())}")


if __name__ == "__main__":
    main()
