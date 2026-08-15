#!/usr/bin/env python3
"""
Agent 1 — literature search (CellGuide AI pipeline stage 1, see ../CLAUDE.md).

Uses the paperclip MCP tool (authenticated via PAPERCLIP_API_KEY) to search
biomedical literature for the given topic and save full text + metadata for
relevant papers under output/related/<slug>/.

Usage:
    uv run agent1_literature_search/run.py "CRISPRi guide RNA library screening"
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

# Hard containment, added after an earlier unscoped run (full repo cwd, default toolset —
# which includes Bash and the Task/subagent tool) spent ~$20 and 80 minutes doing real work
# on OTHER agents' folders (fetching+parsing agent4's ground-truth data, running a real
# benchmark) that was never asked for. This run is now boxed to exactly what Agent 1 needs:
# read/write only inside its own folder, no Bash, no subagents, and hard cost/turn caps.
MAX_BUDGET_USD = 2.0
MAX_TURNS = 30

SYSTEM_PROMPT = f"""You are Agent 1 in the CellGuide AI pipeline ({REPO_ROOT}/CLAUDE.md).

Task: search biomedical literature for the given topic using the paperclip MCP tool
(run `paperclip skill` first to load current command docs). For each relevant paper,
save its full text (or an excerpt if full text isn't available) and metadata to
{OUTPUT_DIR}/related/<slug>/{{meta.json, fulltext.txt or excerpt.md}}, where <slug> is a
short author-year-topic identifier like "smith2024_crispr_screen".

Before fetching, check {OUTPUT_DIR}/related/ for existing slugs — do not re-fetch a paper
already saved there.

When done, write/update {OUTPUT_DIR}/related/INDEX.md listing every slug you found or
already had, with a one-line note on why each is relevant to the topic.
"""


def build_options() -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=str(HERE),
        system_prompt=SYSTEM_PROMPT,
        permission_mode="acceptEdits",
        tools=["Read", "Write", "Glob", "Grep"],
        mcp_servers=paperclip_mcp_config(),
        max_budget_usd=MAX_BUDGET_USD,
        max_turns=MAX_TURNS,
    )


async def run(topic: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt = f"Search for literature on: {topic}"
    async for message in query(prompt=prompt, options=build_options()):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)
        elif isinstance(message, ResultMessage):
            print(f"\n--- agent1 done: {message.num_turns} turns, ${message.total_cost_usd or 0:.4f} ---")
            if message.is_error:
                sys.exit(f"agent1 run failed: {message.result}")


def main() -> None:
    require_anthropic_key()
    parser = argparse.ArgumentParser(description="Agent 1 — literature search")
    parser.add_argument("topic", help="Topic seed, e.g. 'CRISPRi guide RNA library screening'")
    args = parser.parse_args()
    asyncio.run(run(args.topic))


if __name__ == "__main__":
    main()
