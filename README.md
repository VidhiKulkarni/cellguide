# CellGuide AI

Cell-context-aware SpCas9 guide RNA selection: rank CRISPR guide RNAs for a target gene
differently depending on the target cell's chromatin/epigenetic context, instead of relying
on a sequence-only score.

Most guide-design tools score a gRNA the same way regardless of which cell type it will be
used in. But editing efficiency depends on whether the target locus is open or closed
chromatin in that specific cell — the same guide can work well in one cell type and poorly
in another. CellGuide builds a guide-scoring metric that accounts for this, and validates it
against a real published dataset (Ito et al. 2024) that measured exactly this effect in
primary human T cells vs. K562 cells.

Full background: [`docs/CellGuide_AI_Hackathon_Plan.pdf`](docs/CellGuide_AI_Hackathon_Plan.pdf).

## How it's built: an 8-agent pipeline

Instead of one model doing everything, the project is a sequential pipeline of small, single-
purpose agents, each a standalone script in its own top-level folder. Each agent's **output
is the next agent's input** — every stage is independently re-runnable and inspectable.

| # | Agent | Input | Output |
|---|---|---|---|
| 1 | [`agent1_literature_search/`](agent1_literature_search/) | A topic string (e.g. `"CRISPRi guide RNA library screening"`) | `output/related/<slug>/{meta.json, fulltext.txt or excerpt}` per paper found via [Paperclip](https://paperclip.gxl.ai), plus `output/related/INDEX.md` |
| 2 | [`agent2_literature_summarization/`](agent2_literature_summarization/) | Agent 1's saved papers (`agent1_literature_search/output/related/`) | `output/related/<slug>/SUMMARY.md` per paper (experimental design, target genes, on-/off-target outcomes, cell type) + combined `output/SUMMARY.md` table |
| 3 | [`agent3_metric_construction/`](agent3_metric_construction/) | Agent 2's structured summaries + the plan's §4.4 formula | `guide_scoring.py` — a per-guide scoring library (`score_guide()`, taking spacer sequence, on-target scores, ATAC signal, off-target data) + `SPEC.md` documenting every input/weight/rationale |
| 4 | [`agent4_benchmarking/`](agent4_benchmarking/) | Agent 3's `guide_scoring.py` + Ito et al. 2024 ground truth (`papers/ito_2024/table_s1_for_agent4.csv`) | `output/results.csv` (per-guide scores vs. measured indel%), `output/correlation.png`, `output/REPORT.md` |
| 5 | [`agent5_confidence_assessment/`](agent5_confidence_assessment/) | Agent 3's metric + Agent 4's results | `output/confidence.json` (per gene/guide: confidence level, flagged issues, rationale) + `output/CONFIDENCE_REPORT.md` |
| 6 | [`agent6_next_experiment/`](agent6_next_experiment/) | Candidate guide scores (Agent 4's `results.csv`) + Agent 5's confidence + `state/experiment_log.csv` (what's already been tested) | `output/recommendations.csv` — ranked untested guides to test next; `record` appends a new real result to `state/experiment_log.csv` and re-ranks |
| 7 | [`agent7_provenance/`](agent7_provenance/) | Agent 3's `SPEC.md` + Agents 2/4/5 outputs | `output/provenance.json` + `output/PROVENANCE_REPORT.md` — every score component linked back to its source paper and evidence |
| 8 | [`agent8_benchling_sync/`](agent8_benchling_sync/) | Agent 6's top recommendation + new results recorded in [Benchling](https://benchling.com) (Hackathon26 / AIFG project) | Pushes the next-experiment recommendation to Benchling; pulls back recorded results and feeds them into Agent 6's `record` — closes the loop |

Each agent folder has its own `README.md` with exact run instructions and the precise
input/output file formats. Full design details (tool-permission containment rules each
LLM-driven agent runs under, etc.) are in [`CLAUDE.md`](CLAUDE.md).

## What we've found so far

Running the pipeline against Ito et al. 2024's real data (n=199 usable guides) turned up a
genuinely useful, honest result: the original linear-weighted combination (sequence +
chromatin accessibility + specificity) **underperformed just using the sequence score
alone** (Spearman ρ=0.315 vs. ρ=0.441). Agent 5's skeptical review traced this to several
concrete bugs in Agent 3's scoring code (e.g. a missing specificity input silently scoring
as "perfectly safe" instead of "unknown"), which have since been fixed — the metric now
exposes `recommended_score` (sequence-only, matching what the real data actually supports)
alongside the original transparent-but-weaker `combined` blend, and a `passes_ito_rule` gate
to check alongside it, matching how the original paper actually uses chromatin accessibility
(as a filter, not a linear term). See
[`agent4_benchmarking/output/REPORT.md`](agent4_benchmarking/output/REPORT.md) and
[`agent5_confidence_assessment/output/CONFIDENCE_REPORT.md`](agent5_confidence_assessment/output/CONFIDENCE_REPORT.md)
for the full analysis.

## Setup

Requires [`uv`](https://docs.astral.sh/uv/) (manages Python 3.12 automatically — you don't
need Python pre-installed).

```bash
uv sync
```

Create a `.env` file in the repo root (never committed — it's gitignored) with:

```bash
ANTHROPIC_API_KEY='sk-ant-...'      # for the LLM-driven agents (1, 2, 5)
PAPERCLIP_API_KEY='gxl_...'         # for Agent 1's literature search — get one at https://paperclip.gxl.ai/keys
BENCHLING_API_KEY='sk_...'          # for Agent 8 — Basic-auth key from Benchling's Developer Console
BENCHLING_TENANT_URL='https://...'
BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID='assaysch_...'
BENCHLING_RESULTS_SCHEMA_ID='assaysch_...'
```

Agents 3, 4, 6, and 7 are plain Python — no API keys needed.

## Running the pipeline

```bash
# 1. Search for literature on a topic
uv run agent1_literature_search/run.py "CRISPRi guide RNA library screening"

# 2. Summarize whatever Agent 1 found that isn't summarized yet
uv run agent2_literature_summarization/run.py

# 3. (no script — agent3_metric_construction/guide_scoring.py is used directly by agent4+)

# 4. Benchmark the scoring metric against real ground truth
uv run agent4_benchmarking/run.py --data papers/ito_2024/table_s1_for_agent4.csv
# or, to sanity-check the script itself without real data:
uv run agent4_benchmarking/run.py --demo

# 5. Get a skeptical review of the metric + results
uv run agent5_confidence_assessment/run.py --results agent4_benchmarking/output/results.csv

# 6. Get the next-experiment recommendation
uv run agent6_next_experiment/recommend.py recommend \
    --candidates agent4_benchmarking/output/results.csv --top 5

# 7. Build the provenance trail
uv run agent7_provenance/build.py --results agent4_benchmarking/output/results.csv

# 8. Sync with Benchling (push next experiment, pull back new results) — needs schemas set up first
uv run agent8_benchling_sync/run.py --candidates agent4_benchmarking/output/results.csv
```

## Repository layout

- `docs/` — planning documents (hackathon plan PDF, design notes)
- `papers/` — core reference corpus explicitly cited by the plan (Ito et al. 2024 is the
  primary benchmark dataset, in `papers/ito_2024/`)
- `agent1_literature_search/` … `agent8_benchling_sync/` — the pipeline; each folder has its
  own code + that stage's output under `output/`
- `agents_common.py` — shared setup (`.env` loading, paperclip auth) used by the LLM-driven
  agents

See [`CLAUDE.md`](CLAUDE.md) for the full pipeline spec, including the tool-permission
containment rules each LLM-driven agent runs under.
