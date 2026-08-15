# Agent 1 — literature search

Searches biomedical literature via the paperclip MCP tool and saves full text + metadata
for relevant papers.

## Run

```bash
uv run agent1_literature_search/run.py "<topic seed>"
```

Requires `PAPERCLIP_API_KEY` and `ANTHROPIC_API_KEY` in `../.env` (paperclip uses API-key
auth here, not the OAuth login used interactively in Claude Code, so this script can run
headlessly — see https://paperclip.gxl.ai/docs).

## Output

`output/related/<slug>/{meta.json, fulltext.txt or excerpt.md}` per paper, plus
`output/related/INDEX.md` listing what was found and why it's relevant.

Input to [Agent 2](../agent2_literature_summarization/).

## Containment

Scoped to its own folder (`cwd`), `tools=["Read","Write","Glob","Grep"]` + the paperclip
MCP tool — no Bash, no subagents, `max_budget_usd=2.0`, `max_turns=30`. This is a fix after
an earlier unscoped run (full repo `cwd`, default toolset, no caps) spent ~$20 over 80
minutes autonomously doing real work in *other* agents' folders that was never asked for —
see git history around 2026-08-15 if you want the full story.
