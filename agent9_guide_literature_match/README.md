# Agent 9 — guide/literature cross-reference

Given a gene name: score candidate guides with the real Azimuth model
([Agent 3](../agent3_metric_construction/)'s `score_new_gene.py`), then check whether any of
the top-scoring guides have been **explicitly reported** in the literature before — and if so,
with what efficiency, in what biological context (cell type, delivery method).

Two steps, run in order (same convention as the rest of this pipeline — each stage's output
is the next stage's input):

## Step 1 — search (LLM, uses paperclip)

```bash
uv run agent9_guide_literature_match/search_literature.py BCL11A
```

Searches literature **by gene name** (e.g. "BCL11A CRISPR guide RNA knockout efficiency") —
not by raw DNA sequence, since paperclip is a literature search tool, not a sequence
database. Extracts every guide spacer sequence that's *explicitly* given in a found paper's
text/tables, with its reported efficiency and biological context. Never infers or guesses a
sequence, number, or context that isn't explicitly stated — an empty `reported_guides` list
is the correct output when nothing explicit was found.

Writes `output/<gene>/literature_guides.json`.

Same containment as [Agent 1](../agent1_literature_search/) (`cwd` scoped to this folder, no
Bash/subagents, `max_budget_usd`/`max_turns` capped).

## Step 2 — match (deterministic, no LLM)

```bash
uv run agent9_guide_literature_match/match_guides.py BCL11A --top 10
```

Calls Agent 3's `score_new_gene.run()` for real Azimuth-scored candidates, then does an
**exact sequence match** (forward strand + reverse complement) against step 1's
`reported_guides` — whether a specific high-scoring guide "has been reported before" is a
plain string comparison here, not something asked of the search-step LLM.

If step 1 hasn't been run yet for this gene, still reports the Azimuth scores, but marks
every guide's "previously reported?" status as **unknown**, not "no" — those are different
claims, and this script never collapses "we didn't check" into "we checked and found
nothing."

Writes `output/<gene>/match_result.json` and `output/<gene>/MATCH_REPORT.md`.
