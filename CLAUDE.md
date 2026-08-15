# CellGuide AI

Cell-context-aware SpCas9 guide selection: rank CRISPR guide RNAs for a target gene differently depending on the target cell's chromatin/epigenetic context, instead of using a sequence-only score. Full background: `docs/CellGuide_AI_Hackathon_Plan.pdf`.

Primary benchmark dataset: Ito et al. 2024, *Nucleic Acids Research* 52(1):141-154 — 205 gRNAs / 110 genes, primary human T cells, with a T-cell vs K562 cross-context panel. https://academic.oup.com/nar/article/52/1/141/7424430 (local copy: `papers/ito_2024/`).

## Agentic pipeline

Agents 1-4 are the linear path; agents 5, 6 and 8 close it into a loop, so new
experimental results feed back into the ranking:

```
literature -> Paperclip -> AIFG evidence graph -> guide ranking -> next experiment
   -> Benchling -> experimental result -> re-rank -> NEW ranking + NEW next experiment
```

Each stage lives in its own top-level folder with a `README.md`; run
`uv run agentN_.../run.py` (agents 1/2/4/5/8, or `recommend.py` for agent 6) rather than
invoking the `Agent` tool ad hoc, so runs are scripted and repeatable. `uv sync` installs
the shared environment (Python 3.12, managed by `uv` — see `pyproject.toml`). Secrets live
in `.env` (gitignored, never committed) — copy `.env.example` to start.

Agents 3, 4 and 6 are deterministic and need no API keys, so they run without credentials.

| # | Folder | Input | Task | Output |
|---|---|---|---|---|
| 1 | [`agent1_literature_search/`](agent1_literature_search/) | Topic seeds: CRISPR knockout/knockin/CRISPRi/CRISPRa, Perturb-seq, CROP-seq, guide sequence libraries | Claude Agent SDK script; uses the paperclip MCP tool (API-key auth, headless) to search and pull full text + metadata of relevant papers | `output/related/<slug>/{meta.json, fulltext.txt or excerpt}` + `output/related/INDEX.md` |
| 2 | [`agent2_literature_summarization/`](agent2_literature_summarization/) | Agent 1's saved papers | Claude Agent SDK script; for each paper extracts: (1) experimental design — KO / KI / CRISPRi / CRISPRa; (2) target genes; (3) outcomes — expected on-target effect and reported off-target effects; (4) data type — cell line(s), animal model, tissue type, cell type. Skips papers already summarized | `output/related/<slug>/SUMMARY.md` per paper + combined `output/SUMMARY.md` table |
| 3 | [`agent3_metric_construction/`](agent3_metric_construction/) | Agent 2's structured summaries | Not a script — the deliverable itself: `guide_scoring.py`, a per-guide scoring formulation with two components: (1) **efficiency** (expected on-target editing/knockdown/activation), (2) **specificity** (inverse of off-target risk), built from GC content/motif heuristics + pluggable external scores | `guide_scoring.py` (code) + `SPEC.md` (inputs, weights, rationale) |
| 4 | [`agent4_benchmarking/`](agent4_benchmarking/) | Agent 3's metric | Deterministic Python script (no LLM); validates the efficiency/specificity metric against the Ito et al. 2024 T-cell vs K562 ground truth (`papers/ito_2024/`) — compares predicted ranking/scores against measured indel %, and specifically checks whether the metric reproduces the paper's T-cell-open vs K562-open gene panel result. `--demo` runs against synthetic data since the real per-guide Table S1/S2 values aren't fetched yet (see the folder's README) | `output/results.csv`, `output/correlation.png`, `output/REPORT.md` |
| 5 | [`agent5_confidence_assessment/`](agent5_confidence_assessment/) | Agents 3 + 4's metric and results | Claude Agent SDK script acting as scientific skeptic: finds conflicting evidence, weak assumptions, context mismatches and confounders, and assigns each recommendation an explainable confidence | `output/confidence.json` (per-row `confidence_numeric` + `issues`), `output/CONFIDENCE_REPORT.md` |
| 6 | [`agent6_next_experiment/`](agent6_next_experiment/) | Agent 4's candidates + Agent 5's confidence | Deterministic, no LLM, stdlib-only. Ranks untested guides by `priority = combined_score * uncertainty`, where uncertainty is `1 - confidence` from Agent 5 or, failing that, the spread between Agent 3's three components. `record` logs a real result and immediately re-ranks — this is the loop's hinge | `output/recommendations.csv`, `state/experiment_log.csv` |
| 8 | [`agent8_benchling_sync/`](agent8_benchling_sync/) | Benchling `Hackathon26/AIFG` | Pulls new experiment results from Benchling, feeds each to Agent 6's `record`, pushes the refreshed ranking + confidence back. Tenant is `hackathon26.bnchdev.org` with OAuth2 app credentials — not the standard `<org>.benchling.com` + API key | updated `experiment_log.csv`, write-back to Benchling |

### Not yet built

- **Agent 7 — provenance.** Linking each guide score, claim and decision back to its
  supporting paper, extracted evidence and validation result. No folder yet.
- **Modal** (parallel/batch scoring) and **BenchFlow** (trace capture for evaluation and
  inspectability) are in the intended stack but have no code or dependency here yet.

## Repository conventions

- `docs/` — planning documents (hackathon plan PDF, etc.)
- `agent1_literature_search/` … `agent8_benchling_sync/` — pipeline stage code + that stage's output, per the table above
- `papers/` — **core reference corpus only** (the plan's explicitly-cited papers, fetched via Paperclip), one folder per paper: `meta.json`, `fulltext.txt`, `SUMMARY.md`, `structured_extraction.md`
  - `papers/ito_2024/` — primary benchmark dataset (Agent 4's ground truth)
  - `papers/MANIFEST.md` — fetch status log for the core cited papers
  - `papers/SUMMARY.md` — cross-paper synthesis tied to the hackathon plan's workstreams
  - Broader topic-searched literature (formerly `papers/related/`) now lives under `agent1_literature_search/output/related/` and `agent2_literature_summarization/output/related/` — see the pipeline table above
- Do not re-fetch papers already saved under `papers/` or `agent1_literature_search/output/` — check existing folders first.

## Tools

- **Paperclip** (`mcp__paperclip__paperclip` interactively, or the paperclip MCP server with `X-API-Key` auth from Agent 1's script): biomedical literature search/full-text filesystem. Interactively, run `paperclip skill` before first use each session to load current command docs; use `search -s pmc "<query>"`, `lookup doi/title/author`, `cat`/`head` on `content.lines`, and `map`/`reduce` for multi-paper synthesis. Full command reference: see the tool's own `skill` output — don't re-derive it from memory. API keys: https://paperclip.gxl.ai/keys.
- **Claude Agent SDK** (`claude_agent_sdk`, used by agent1/agent2's `run.py`): headless one-shot `query()` calls. OAuth-gated MCP servers don't work headlessly through it — use API-key auth instead (see `agents_common.py`).
