# CellGuide AI

Cell-context-aware SpCas9 guide selection: rank CRISPR guide RNAs for a target gene differently depending on the target cell's chromatin/epigenetic context, instead of using a sequence-only score. Full background: `docs/CellGuide_AI_Hackathon_Plan.pdf`.

Primary benchmark dataset: Ito et al. 2024, *Nucleic Acids Research* 52(1):141-154 — 205 gRNAs / 110 genes, primary human T cells, with a T-cell vs K562 cross-context panel. https://academic.oup.com/nar/article/52/1/141/7424430 (local copy: `papers/ito_2024/`).

## Two workflows, one shared codebase

The folders are numbered `agent1`...`agent9` in the order each was **built**, not in a single
logical flow — that's a real source of confusion (agent9 doesn't come "after" agent8 in any
pipeline sense). There are actually two separate workflows sharing the same scoring code,
plus a shared experiment-loop layer both can feed into. Folder names/paths are unchanged from
their build order (renaming would break every hardcoded cross-folder reference below, and
this is a repo other people also work in) — this section is the map that makes the real
structure legible. `uv sync` installs the shared environment (Python 3.12, managed by `uv` —
see `pyproject.toml`). Secrets (`PAPERCLIP_API_KEY`, `ANTHROPIC_API_KEY`) live in `.env`
(gitignored, never committed).

### Track A — build & validate the scoring methodology (agents 1-5, 7)

Run once (or whenever the methodology itself changes), **not** per end-user query. Each
stage's output is the next stage's input — run in order as standalone reproducible code, via
`uv run agentN_.../run.py` (agents 1/2/4) rather than invoking the `Agent` tool ad hoc.

| # | Folder | Input | Task | Output |
|---|---|---|---|---|
| 1 | [`agent1_literature_search/`](agent1_literature_search/) | Topic seeds: CRISPR knockout/knockin/CRISPRi/CRISPRa, Perturb-seq, CROP-seq, guide sequence libraries | Claude Agent SDK script; uses the paperclip MCP tool (API-key auth, headless) to search and pull full text + metadata of relevant papers | `output/related/<slug>/{meta.json, fulltext.txt or excerpt}` + `output/related/INDEX.md` |
| 2 | [`agent2_literature_summarization/`](agent2_literature_summarization/) | Agent 1's saved papers | Claude Agent SDK script; for each paper extracts: (1) experimental design — KO / KI / CRISPRi / CRISPRa; (2) target genes; (3) outcomes — expected on-target effect and reported off-target effects; (4) data type — cell line(s), animal model, tissue type, cell type. Skips papers already summarized | `output/related/<slug>/SUMMARY.md` per paper + combined `output/SUMMARY.md` table |
| 3 | [`agent3_metric_construction/`](agent3_metric_construction/) | Agent 2's structured summaries | Not a script — the deliverable itself: `guide_scoring.py`, a per-guide scoring formulation with two components: (1) **sequence efficacy** (on-target, from DeepSpCas9/CHOPCHOP, real Azimuth/Doench 2016 predictions, or a GC/motif fallback — see `sequence_efficacy_with_source()`), (2) **accessibility** (cell-context, from ATAC signal). A third component, specificity/off-target risk, was tried and removed — never got real data, see `SPEC.md` "Known limitations" | `guide_scoring.py` (code) + `SPEC.md` (inputs, weights, rationale) |
| 4 | [`agent4_benchmarking/`](agent4_benchmarking/) | Agent 3's metric | Deterministic Python script (no LLM); validates `recommended_score`/`passes_ito_rule` against Ito et al. 2024's real measured indel% (`papers/ito_2024/table_s1_for_agent4.csv`, n=199). Includes follow-up checks: `interaction_effect_check.py` (Ito's actual conditional accessibility claim), `motif_and_accessibility_checks.py`, `replicate_sensitivity_check.py`, `azimuth_validation_check.py` (validates the Azimuth path specifically, in-context, by reconstructing real genomic context for Ito's own 199 guides — separate from the tier-1 DeepSpCas9/CHOPCHOP number) | `output/results.csv`, `output/correlation.png`, `output/REPORT.md` + per-check `.md` reports |
| 5 | [`agent5_confidence_assessment/`](agent5_confidence_assessment/) | Agent 3's metric + Agent 4's results | Claude Agent SDK script acting as a scientific skeptic — flags conflicting evidence between cited papers, weak assumptions, context mismatches, confounders | `output/confidence.json` (per gene/guide) + `output/CONFIDENCE_REPORT.md` |
| 7 | [`agent7_provenance/`](agent7_provenance/) | Agent 3's `SPEC.md` (parsed, not hand-copied) + Agents 2/4/5 outputs | Deterministic script; links every score component and per-guide result back to its source paper + evidence snippet | `output/provenance.json` + `output/PROVENANCE_REPORT.md` |

### Track B — score a gene on demand (agent 3's `score_new_gene.py` + agent 9)

The actual "user types a gene name" product workflow. Independent of Track A's run order —
only depends on `agent3_metric_construction`'s library code (not on agents 1/2/4/5/7 having
been run). Two steps:

| Step | Folder / script | Input | Task | Output |
|---|---|---|---|---|
| B1 | [`agent3_metric_construction/score_new_gene.py`](agent3_metric_construction/score_new_gene.py) | Gene symbol | Deterministic (no LLM): real Ensembl coordinate lookup → real genomic sequence → real NGG PAM scan (both strands) → batched real Azimuth on-target scoring. Every result/failure reported in plain language (`status`, `messages`) — this is the "honest UI" entry point | ranked candidate guides with `recommended_score` + `sequence_efficacy_source` |
| B2 | [`agent9_guide_literature_match/`](agent9_guide_literature_match/) | B1's top-scoring guides | Two sub-steps: `search_literature.py` (LLM, paperclip — searches **by gene name**, not by raw sequence, extracts any explicitly-reported guide sequences/efficiency/context); `match_guides.py` (deterministic — exact sequence match, forward + reverse complement, against B1's candidates; never collapses "search not run" into "not found") | `output/<gene>/literature_guides.json`, `match_result.json`, `MATCH_REPORT.md` |

### Shared — experiment loop (agents 6, 8)

Consumes candidate scores from **either** track and closes the loop with real wet-lab results.

| # | Folder | Input | Task | Output |
|---|---|---|---|---|
| 6 | [`agent6_next_experiment/`](agent6_next_experiment/) | Candidate guide scores (from Track A's benchmark set or Track B's `score_new_gene.py` output) + Agent 5's confidence (or a component-disagreement proxy) | Deterministic script; ranks untested guides by `combined_score x uncertainty` and recommends what to test next; `record` ingests a real result and re-ranks | `output/recommendations.csv`, `state/experiment_log.csv` |
| 8 | [`agent8_benchling_sync/`](agent8_benchling_sync/) | Benchling experiment results (Hackathon26 / AIFG folder) | Real implementation via the official `benchling-sdk` — pushes Agent 6's top recommendation to Benchling as the next experiment, pulls back recorded results and feeds them into Agent 6's `record`. **Not runnable yet**: needs a tenant URL + two Result schema IDs created in Benchling first (see the folder's README) | n/a until Benchling schemas exist |

**Containment**: agents 1/2/5/9 (and any future LLM-driven stage) must set `cwd` to their own
folder, `add_dirs` for read-only access to specific sibling folders they need, an explicit
`tools` allowlist (no `Bash`, no subagents unless truly needed), and `max_budget_usd` /
`max_turns` caps. This is not optional boilerplate — an earlier unscoped run (full repo
`cwd`, default toolset, no caps) autonomously did ~$20 of unplanned work across other
agents' folders. See [`agent1_literature_search/README.md`](agent1_literature_search/README.md#containment).

## Repository conventions

- `docs/` — planning documents (hackathon plan PDF, etc.)
- `agent1_literature_search/`, `agent2_literature_summarization/`, `agent3_metric_construction/`, `agent4_benchmarking/`, `agent5_confidence_assessment/`, `agent6_next_experiment/`, `agent7_provenance/`, `agent8_benchling_sync/`, `agent9_guide_literature_match/` — pipeline stage code + that stage's output, per the tracks above (folder numbers = build order, not flow order — see "Two workflows" above for which track each one belongs to)
- `papers/` — **core reference corpus only** (the plan's explicitly-cited papers, fetched via Paperclip), one folder per paper: `meta.json`, `fulltext.txt`, `SUMMARY.md`, `structured_extraction.md`
  - `papers/ito_2024/` — primary benchmark dataset (Agent 4's ground truth)
  - `papers/MANIFEST.md` — fetch status log for the core cited papers
  - `papers/SUMMARY.md` — cross-paper synthesis tied to the hackathon plan's workstreams
  - Broader topic-searched literature (formerly `papers/related/`) now lives under `agent1_literature_search/output/related/` and `agent2_literature_summarization/output/related/` — see the pipeline table above
- Do not re-fetch papers already saved under `papers/` or `agent1_literature_search/output/` — check existing folders first.

## Tools

- **Paperclip** (`mcp__paperclip__paperclip` interactively, or the paperclip MCP server with `X-API-Key` auth from Agent 1's script): biomedical literature search/full-text filesystem. Interactively, run `paperclip skill` before first use each session to load current command docs; use `search -s pmc "<query>"`, `lookup doi/title/author`, `cat`/`head` on `content.lines`, and `map`/`reduce` for multi-paper synthesis. Full command reference: see the tool's own `skill` output — don't re-derive it from memory. API keys: https://paperclip.gxl.ai/keys.
- **Claude Agent SDK** (`claude_agent_sdk`, used by agent1/agent2's `run.py`): headless one-shot `query()` calls. OAuth-gated MCP servers don't work headlessly through it — use API-key auth instead (see `agents_common.py`).
