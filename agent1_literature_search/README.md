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
