#!/usr/bin/env python3
"""
Agent 9 (search step) — literature cross-reference for CellGuide AI (see ../CLAUDE.md).

Given a gene symbol, uses the paperclip MCP tool (API-key auth, headless — see
agents_common.py) to search biomedical literature BY GENE NAME (not by raw DNA sequence —
paperclip is a literature search tool, not a sequence database) for CRISPR guide RNA design
and editing-efficiency data on that gene. Extracts every guide RNA spacer sequence that's
EXPLICITLY given in a found paper's text/tables, with its reported efficiency and biological
context (cell type, delivery method) — never inferred or estimated.

This is intentionally the ONLY LLM-driven step. Whether any of those literature sequences
match our own Azimuth-scored candidates is a deterministic string comparison, done afterward
by match_guides.py — not asked of the model, per this project's convention of keeping
LLM judgment and deterministic computation in separate, auditable stages.

Usage:
    uv run agent9_guide_literature_match/search_literature.py BCL11A
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents_common import REPO_ROOT, paperclip_mcp_config, require_anthropic_key  # noqa: E402

from claude_agent_sdk import (  # noqa: E402
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"

# Same containment convention as agent1/agent2 (see agent1_literature_search/README.md#containment):
# own folder only, no Bash, no subagents, hard cost/turn caps.
MAX_BUDGET_USD = 2.0
MAX_TURNS = 30

SYSTEM_PROMPT = f"""You are Agent 9 (search step) in the CellGuide AI pipeline ({REPO_ROOT}/CLAUDE.md).

Task: given a gene symbol, use the paperclip MCP tool (run `paperclip skill` first to load
current command docs) to search biomedical literature for CRISPR guide RNA design / editing
efficiency for THIS GENE. Search BY GENE NAME — e.g. "<GENE> CRISPR guide RNA knockout
efficiency", "<GENE> sgRNA screen indel" — not by DNA sequence. paperclip is a literature
search tool, not a sequence database; do not expect it to find a paper by pasting a raw
20-nt string into the query.

For every relevant paper you find, extract ONLY guide RNA spacer sequences that are
EXPLICITLY given as a literal DNA sequence in the paper's text, tables, or supplementary
material, together with:
  - the exact sequence as written (note if it's given with an extra 5' G or a PAM appended)
  - the reported editing efficiency/outcome (indel %, cutting efficiency, etc.) EXACTLY as
    stated — do not compute, round, or estimate a number yourself
  - the biological context: cell type/line, tissue, delivery method (RNP / lentiviral /
    plasmid / etc.), exactly as stated
  - which paper it came from (full citation, or paperclip's identifier for it)

Do NOT include guides that are only vaguely referenced ("we designed guides against exon 2")
without an actual sequence given. Do NOT guess, estimate, or infer a sequence, efficiency
number, or biological context that isn't explicitly stated in the source text — an empty
result is the CORRECT output if nothing explicit was found in the papers you retrieved. A
fabricated-but-plausible entry here would be worse than an honest empty list.

Write your findings to {OUTPUT_DIR}/<gene>/literature_guides.json with exactly this schema:
{{
  "gene": "<gene symbol>",
  "search_queries_tried": ["<query 1>", "<query 2>", ...],
  "papers_found_relevant": ["<citation or paperclip identifier>", ...],
  "reported_guides": [
    {{"sequence": "...", "efficiency": "...", "cell_type": "...", "delivery": "...",
      "source": "...", "evidence_snippet": "..."}}
  ],
  "notes": "<why nothing was found, ambiguity, search terms that didn't work, etc. — always
    fill this in even when reported_guides is non-empty, so a reader knows how thorough the
    search was>"
}}
If you find zero relevant papers or zero explicit sequences, still write this file with an
empty "reported_guides" list — never skip writing the file, and never omit "notes"."""


def build_options(gene: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(HERE),
        system_prompt=SYSTEM_PROMPT,
        permission_mode="acceptEdits",
        tools=["Read", "Write", "Glob", "Grep"],
        mcp_servers=paperclip_mcp_config(),
        max_budget_usd=MAX_BUDGET_USD,
        max_turns=MAX_TURNS,
    )


async def run(gene: str) -> None:
    (OUTPUT_DIR / gene).mkdir(parents=True, exist_ok=True)
    prompt = f"Search literature for CRISPR guide RNA sequences and editing-efficiency data for the gene: {gene}"
    async for message in query(prompt=prompt, options=build_options(gene)):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n--- agent9 search done: {message.num_turns} turns, ${message.total_cost_usd or 0:.4f} ---")
            if message.is_error:
                sys.exit(f"agent9 search run failed: {message.result}")


def main() -> None:
    require_anthropic_key()
    parser = argparse.ArgumentParser(description="Agent 9 (search step) — literature search for a gene's guide RNAs")
    parser.add_argument("gene", help="Gene symbol, e.g. BCL11A")
    args = parser.parse_args()
    asyncio.run(run(args.gene))


if __name__ == "__main__":
    main()
