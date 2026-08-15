#!/usr/bin/env python3
"""
Agent 5 — scientific skeptic / confidence assessment (CellGuide AI pipeline, ../CLAUDE.md).

Acts as a skeptical reviewer of Agent 3's guide rankings: identifies conflicting evidence
between cited papers, weak assumptions baked into the scoring formula, context mismatches
(e.g. delivery method, cell type), and potential confounders — then gives an explainable
confidence assessment per guide/gene.

Deliberately scoped tight: no Bash, no MCP/paperclip, no network access — Read/Write/Grep/
Glob only, cwd'd into this folder with read-only access to the specific sibling folders it
needs (agent2/3/4 outputs + papers/). This is a fix for a real incident: an earlier
unscoped run of agent1_literature_search (full repo cwd + Bash + bypassPermissions) wrote
files into other agents' folders on its own initiative. Agent 5 only ever needs to *read*
those folders and *write* inside its own output/, so it never gets tools that could do more
than that.

Usage:
    uv run agent5_confidence_assessment/run.py [--results path/to/agent4/results.csv]
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents_common import require_anthropic_key  # noqa: E402

from claude_agent_sdk import (  # noqa: E402
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
OUTPUT_DIR = HERE / "output"

READ_ONLY_DIRS = [
    REPO_ROOT / "agent2_literature_summarization" / "output",
    REPO_ROOT / "agent3_metric_construction",
    REPO_ROOT / "agent4_benchmarking" / "output",
    REPO_ROOT / "papers",
]

SYSTEM_PROMPT = f"""You are Agent 5 in the CellGuide AI pipeline ({REPO_ROOT}/CLAUDE.md) —
a scientific skeptic reviewing Agent 3's guide scoring metric and Agent 4's validation
results.

Read (do not modify):
- {REPO_ROOT}/agent3_metric_construction/SPEC.md and guide_scoring.py — the scoring formula,
  its inputs, weights, and the literature caveats already documented in it (several
  contradictions are already flagged there — start by checking whether they're actually
  accounted for in the combined score, or just noted and ignored).
- {REPO_ROOT}/agent2_literature_summarization/output/ — per-paper structured summaries.
- {REPO_ROOT}/agent4_benchmarking/output/ — benchmark results and report, if present.
- {REPO_ROOT}/papers/ — the core reference corpus (Ito et al. 2024, Wang et al. 2019, etc).

For each gene/guide present in Agent 4's results (or, if no results file exists yet, for the
scoring formula's three components in general), identify:
  1. Conflicting evidence between cited papers (e.g. does one paper's finding actually
     contradict the assumption another component relies on?)
  2. Weak assumptions (untuned default weights, a fallback heuristic used where a better
     score was actually available, thresholds copied from a different delivery context)
  3. Context mismatches (delivery method — RNP vs lentiviral vs stable — cell type, species)
  4. Potential confounders not modeled by the score at all

Then give an explainable confidence assessment. Do not soften findings to sound reassuring —
a real gap should read as a real gap.

Write {OUTPUT_DIR}/confidence.json: a JSON array, one object per gene/guide (or per
component if no results file), each with exactly these fields:
  gene (str), cell_type (str or null), confidence (one of "low"/"medium"/"high"),
  confidence_numeric (float 0-1, 0=least trustworthy), issues (array of short strings),
  rationale (1-3 sentences explaining the confidence level).

Also write {OUTPUT_DIR}/CONFIDENCE_REPORT.md: the same content, human-readable, with your
overall skeptical take on the metric at the top.
"""


def build_options(results_path: Path | None) -> ClaudeAgentOptions:
    extra = f"\n\nAgent 4 results file for this run: {results_path}" if results_path else ""
    return ClaudeAgentOptions(
        cwd=str(HERE),
        add_dirs=[str(d) for d in READ_ONLY_DIRS],
        system_prompt=SYSTEM_PROMPT + extra,
        permission_mode="acceptEdits",
        tools=["Read", "Write", "Glob", "Grep"],
    )


async def run(results_path: Path | None) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt = "Review Agent 3's scoring metric and Agent 4's results as a scientific skeptic, per your instructions."
    async for message in query(prompt=prompt, options=build_options(results_path)):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n--- agent5 done: {message.num_turns} turns, ${message.total_cost_usd or 0:.4f} ---")
            if message.is_error:
                sys.exit(f"agent5 run failed: {message.result}")


def main() -> None:
    require_anthropic_key()
    parser = argparse.ArgumentParser(description="Agent 5 — scientific skeptic / confidence assessment")
    parser.add_argument("--results", type=Path, default=None, help="Agent 4 results.csv to assess")
    args = parser.parse_args()
    asyncio.run(run(args.results))


if __name__ == "__main__":
    main()
