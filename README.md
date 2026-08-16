# GuideRail

Cell-context-aware CRISPR guide RNA scoring, validated against real experimental data.

## Background

CRISPR-Cas9 guide RNA (gRNA) design tools typically score candidates from sequence alone
(GC content, position-weight matrices, or sequence-trained models such as Azimuth/Doench
2016). Editing efficiency, however, also depends on whether the target locus is accessible
in the target cell type's chromatin state — a property no sequence-only score captures. The
same guide can perform well in one cell type and poorly in another purely because of
chromatin accessibility, not sequence.

GuideRail scores guides on sequence efficacy **and** cell-type-specific chromatin
accessibility (ATAC-seq signal), and validates the resulting formula against Ito et al. 2024
(*Nucleic Acids Research* 52(1):141-154) — 199 real guides tested in two cell types (primary
human T cells, K562) with measured editing outcomes.

Full proposal: [`docs/CellGuide_AI_Hackathon_Plan.pdf`](docs/CellGuide_AI_Hackathon_Plan.pdf).

## Architecture

Nine components ("agents"), numbered by build order rather than execution order, form two
workflows sharing one scoring library:

- **Track A** — build and validate the scoring formula. Run once, by a developer; not part
  of the per-query path.
- **Track B** — score an arbitrary gene on demand. The user-facing workflow.
- **Shared** — a closed experiment loop (rank next test, sync with Benchling) consuming
  candidates from either track.

### Track A — formula construction and validation

| # | Component | Input | Task | Output |
|---|---|---|---|---|
| 1 | Literature search | Topic | Retrieves relevant papers via Paperclip | `agent1_literature_search/output/` |
| 2 | Summarization | Agent 1's papers | Extracts design, target genes, outcomes, cell type per paper | `agent2_literature_summarization/output/` |
| 3 | Metric construction | Agent 2's summaries | `guide_scoring.py` — sequence efficacy + chromatin accessibility; each term cited to a specific paper, not derived wholesale from the corpus | `guide_scoring.py`, `SPEC.md` |
| 4 | Benchmarking | Agent 3's formula + Ito et al. 2024 data | Deterministic validation against measured indel% (n=199); no LLM | `agent4_benchmarking/output/` |
| 5 | Confidence assessment | Agent 3 + Agent 4 outputs | Adversarial review — flags unsupported assumptions, contradicted claims | `agent5_confidence_assessment/output/` |
| 7 | Provenance | Agent 3's spec + all outputs | Links every score component to its supporting citation | `agent7_provenance/output/` |

### Track B — score a gene on demand

Independent of Track A's run order; only requires Agent 3's library code.

| Step | Component | Input | Task | Output |
|---|---|---|---|---|
| 1 | `score_new_gene.py` (Agent 3) | Gene symbol | Real Ensembl lookup → sequence → PAM scan → Azimuth scoring; deterministic, no LLM | Ranked candidate guides (JSON) |
| 2 | Agent 9 | Top-scoring candidates | Literature search by gene name (not raw sequence), then exact-match check against candidates | `agent9_guide_literature_match/output/<gene>/` |

### Shared — closing the loop

| # | Component | Input | Task | Output |
|---|---|---|---|---|
| 6 | Next experiment | Candidates (either track) + confidence | Ranks untested guides by expected value × uncertainty; ingests real results and re-ranks | `agent6_next_experiment/output/` |
| 8 | Benchling sync | Agent 6's top recommendation | Pushes to Benchling; retrieves recorded results | Benchling + Agent 6 state |
| 10 | Proto design (planned — folder not yet in this repo) | Agent 3's candidate pool | Hard-gates candidates (efficacy, GC, specificity), ranks by paired ATAC advantage, balances selection across target genes | Ranked panel (CSV + design report) |

Each component's folder has its own README with exact commands. Full technical spec —
containment rules, cost limits, and why they exist — in [`CLAUDE.md`](CLAUDE.md).

## Validation

The formula was revised twice after real-data validation contradicted its assumptions.

| Round | Claim tested | Result |
|---|---|---|
| 1 | 3-component blend (sequence + accessibility + off-target) vs. sequence alone | Blend underperformed: ρ=0.315 vs. ρ=0.441 (n=199). Root cause: the off-target term defaulted to "safe" when no data existed, instead of "unknown" — fixed by removing the term entirely, not by patching the default. |
| 2 | Accessibility's standalone (marginal) predictive value | No signal (ρ=0.084, p=0.24, n.s.). ATAC measurement also found replicate-sensitive (borderline guides flip pass/fail between the two real replicates). Cross-cell-type transfer — the project's core premise — remains untested by this benchmark. |
| 3 | Accessibility's *conditional* value, per Ito et al.'s actual published claim (effect appears only among above-median-sequence-score guides) | Reproduces: ρ=0.232, p=0.008 (n=131). AND-gate precision rises as designed, 0.741→0.862. Round 2's marginal test and F1-based conclusion were the wrong statistics for this claim. |

Current state: `recommended_score` is sequence-only (the empirically better ranking value);
`passes_ito_rule` is checked separately as a gate. Accessibility has real conditional
predictive value not yet folded into a single score.

**Azimuth validated separately.** The ρ=0.441 figure above is DeepSpCas9/CHOPCHOP's, not
Azimuth — the model Track B's `score_new_gene.py` uses for genes outside Ito's 199.
Reconstructing real genomic context for Ito's own guides and scoring them with Azimuth
directly (context recoverable for 89/199 guides; Ensembl lookup/fetch failed for the rest)
gives ρ=0.346, p=0.0009 — real and significant, but weaker than DeepSpCas9/CHOPCHOP on the
same 89-guide subset (ρ=0.518). Track B's guides inherit a real but weaker validated signal;
ρ=0.441 should not be quoted for Track B.

Sources: [`agent4_benchmarking/output/REPORT.md`](agent4_benchmarking/output/REPORT.md),
[`REPLICATE_SENSITIVITY_REPORT.md`](agent4_benchmarking/output/REPLICATE_SENSITIVITY_REPORT.md),
[`INTERACTION_EFFECT_CHECK.md`](agent4_benchmarking/output/INTERACTION_EFFECT_CHECK.md),
[`MOTIF_AND_ACCESSIBILITY_CHECKS.md`](agent4_benchmarking/output/MOTIF_AND_ACCESSIBILITY_CHECKS.md),
[`AZIMUTH_VALIDATION_CHECK.md`](agent4_benchmarking/output/AZIMUTH_VALIDATION_CHECK.md),
[`agent5_confidence_assessment/output/CONFIDENCE_REPORT.md`](agent5_confidence_assessment/output/CONFIDENCE_REPORT.md).

### Key numbers (for slides)

| Claim | Number | Source |
|---|---|---|
| Sequence-only predicts real editing efficiency | ρ = 0.441, p = 7×10⁻¹¹, n = 199 | `REPORT.md` |
| Shipped blended score is *worse* than sequence alone | ρ = 0.315 (blend) vs 0.441 (sequence) | same |
| Accessibility has **no** marginal effect (naive test) | ρ = 0.084, p = 0.24, n.s. | same |
| Accessibility **does** have a real conditional effect (correct test) | ρ = 0.232, p = 0.008, n = 131 | `INTERACTION_EFFECT_CHECK.md` |
| GC/motif fallback heuristic has no real signal | ρ = 0.043, p = 0.54, n.s. | `MOTIF_AND_ACCESSIBILITY_CHECKS.md` |
| Track B's model (Azimuth) predicts efficiency too, weaker than Track A's tools | ρ = 0.346, p = 0.0009, n = 89 | `AZIMUTH_VALIDATION_CHECK.md` |
| Off-target/specificity assessment | not implemented — no real data source, removed | `SPEC.md` |
| ATAC measurement is replicate-sensitive | passing-guide set changes between the two real replicates | `REPLICATE_SENSITIVITY_REPORT.md` |

**Claims to avoid overstating**: GuideRail does not assess off-target risk. ρ=0.441 is
DeepSpCas9/CHOPCHOP's validated accuracy, not GuideRail's own model. The accessibility
result is a real conditional signal not yet folded into the shipped score, not a clean
win. Track B's guides validate at ρ=0.346, not ρ=0.441.

## Dashboard

[`dashboard/cellguide-dashboard.html`](dashboard/cellguide-dashboard.html) — single
self-contained HTML file, no server or build step required.

- Tabs 01–06 (Track A): a scripted replay of a prior real pipeline run — real numbers, but
  a canned animation, explicitly labeled as such. Does not re-execute anything live.
- Tab 07 ("Score a Gene", Track B): static demo of real `score_new_gene.py` + Agent 9
  output for one example gene (BCL11A), including an honest-failure example from Agent 9's
  search step when a data source was unavailable.
- Caveats from the table above appear as a collapsible banner on the Overview tab and as
  inline notes near relevant charts.

## Setup

Requires [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

Create a `.env` file in the repo root (gitignored):

```bash
ANTHROPIC_API_KEY='sk-ant-...'      # Agents 1, 2, 5, 9
PAPERCLIP_API_KEY='gxl_...'         # Agents 1, 9 — https://paperclip.gxl.ai/keys
BENCHLING_API_KEY='sk_...'          # Agent 8 — Benchling Developer Console
BENCHLING_TENANT_URL='https://...'
BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID='assaysch_...'
BENCHLING_RESULTS_SCHEMA_ID='assaysch_...'
```

Agent 3 (including `score_new_gene.py`), Agent 4, Agent 6, Agent 7, and Agent 9's
`match_guides.py` require no API keys. Only Agent 9's `search_literature.py` needs
`ANTHROPIC_API_KEY` + `PAPERCLIP_API_KEY` (same as Agent 1).

### Tests

```bash
uv run pytest tests/
```

Unit tests for the deterministic components (`guide_scoring.py`, `genome_lookup.py`,
`recommend.py`, `agent7_provenance/build.py`) — no network calls, no API keys. One test
exercises the real Azimuth model if `~/miniforge3/envs/azimuth` exists (see
[`agent3_metric_construction/README.md`](agent3_metric_construction/README.md)); skipped
otherwise.

## Commands

**Track A** (run once, as a developer):

```bash
uv run agent1_literature_search/run.py "CRISPRi guide RNA library screening"
uv run agent2_literature_summarization/run.py
# Agent 3 has no command — guide_scoring.py is imported by Agents 4+
uv run agent4_benchmarking/run.py --data papers/ito_2024/table_s1_for_agent4.csv
uv run agent5_confidence_assessment/run.py --results agent4_benchmarking/output/results.csv
uv run agent7_provenance/build.py --results agent4_benchmarking/output/results.csv
```

**Track B**:

```bash
uv run agent3_metric_construction/score_new_gene.py BCL11A --top 10
uv run agent9_guide_literature_match/search_literature.py BCL11A
uv run agent9_guide_literature_match/match_guides.py BCL11A --top 10
```

**Shared** (either track's candidates):

```bash
uv run agent6_next_experiment/recommend.py recommend \
    --candidates agent4_benchmarking/output/results.csv --top 5
uv run agent8_benchling_sync/run.py --candidates agent4_benchmarking/output/results.csv
```

Each command writes its full output to that component's own `output/` folder.

## Repository layout

- `docs/` — project plan (PDF) and design notes
- `papers/` — core reference corpus, notably `papers/ito_2024/` (Agent 4's ground truth)
- `agent1_literature_search/` through `agent9_guide_literature_match/` — pipeline
  components (numbered by build order, not flow order — see Architecture above)
- `agents_common.py` — shared setup (`.env` loading, literature search config) for
  Agents 1, 2, 5, 9

Full technical spec — read/write permissions per agent, cost limits, and rationale — in
[`CLAUDE.md`](CLAUDE.md).
