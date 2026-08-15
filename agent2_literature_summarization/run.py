#!/usr/bin/env python3
"""
Agent 2 — literature summarization (CellGuide AI pipeline stage 2, see ../CLAUDE.md).

Reads Agent 1's saved papers (../agent1_literature_search/output/related/<slug>/) and,
for each one not yet summarized, extracts: (1) experimental design (KO/KI/CRISPRi/CRISPRa),
(2) target genes, (3) outcomes (on-target + off-target), (4) data type (cell line/tissue).
Writes a per-paper SUMMARY.md plus a combined cross-paper table.

Usage:
    uv run agent2_literature_summarization/run.py
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents_common import REPO_ROOT, require_anthropic_key  # noqa: E402

from claude_agent_sdk import (  # noqa: E402
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"
AGENT1_OUTPUT = REPO_ROOT / "agent1_literature_search" / "output"

SYSTEM_PROMPT = f"""You are Agent 2 in the CellGuide AI pipeline ({REPO_ROOT}/CLAUDE.md).

Input: papers saved by Agent 1 under {AGENT1_OUTPUT}/related/<slug>/ (meta.json,
fulltext.txt or excerpt.md).

For each slug that does NOT already have a SUMMARY.md under {OUTPUT_DIR}/related/<slug>/,
read its saved text and extract:
  1. Experimental design — KO / KI / CRISPRi / CRISPRa
  2. Target genes
  3. Outcomes — expected on-target effect and reported off-target effects
  4. Data type — cell line(s), animal model, tissue type, cell type

Write {OUTPUT_DIR}/related/<slug>/SUMMARY.md for each paper with those four fields.

When all papers are processed, write/overwrite {OUTPUT_DIR}/SUMMARY.md: a single markdown
table with one row per slug and columns for the four fields above, plus a short cross-paper
synthesis paragraph at the top.
"""


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(REPO_ROOT),
        system_prompt=SYSTEM_PROMPT,
        permission_mode="bypassPermissions",
    )


async def run() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt = "Summarize every paper from Agent 1's output that doesn't have a SUMMARY.md yet."
    async for message in query(prompt=prompt, options=build_options()):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n--- agent2 done: {message.num_turns} turns, ${message.total_cost_usd or 0:.4f} ---")
            if message.is_error:
                sys.exit(f"agent2 run failed: {message.result}")


def main() -> None:
    require_anthropic_key()
    argparse.ArgumentParser(description="Agent 2 — literature summarization").parse_args()
    asyncio.run(run())


if __name__ == "__main__":
    main()
