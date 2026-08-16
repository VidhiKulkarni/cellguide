# CellGuide AI

## The problem, in plain terms

CRISPR gene editing uses a short "guide RNA" (gRNA) to tell the Cas9 enzyme where to cut a
gene. Picking a good guide matters a lot — a bad one edits inefficiently or cuts the wrong
place. Most existing guide-design tools score a guide using only its **DNA sequence**
(things like GC content, or a machine-learning model trained on sequence patterns).

The problem: the *same* guide, with the *exact same* sequence, can work great in one cell
type and barely work at all in a different cell type. Why? Because DNA in a cell isn't
uniformly accessible — some regions are tightly packed ("closed chromatin") and hard for
Cas9 to reach, while other regions are open and easy to cut. Whether a specific gene's DNA
is open or closed depends on the cell type. A sequence-only score has no way to know this.

**CellGuide's idea**: build a guide-scoring tool that also takes the target cell type into
account — specifically, whether that region of DNA is open or closed in that cell — instead
of scoring sequence alone. We validate this against a real published experiment (Ito et al.
2024) that tested the exact same guides in two different cell types (primary human T cells
vs. K562, a different cell line) and measured how much the editing efficiency actually
changed between them.

Full background/proposal: [`docs/CellGuide_AI_Hackathon_Plan.pdf`](docs/CellGuide_AI_Hackathon_Plan.pdf).

## How it's built

Instead of one big model trying to do everything, this is broken into **small, single-job
agents** that each do one specific task, save their output to a file, and hand it to the
next step. This makes every step easy to inspect, re-run on its own, and debug
independently, instead of one big opaque process where you can't tell what happened or why.

The agents are numbered 1 through 9 in the order they were **built**, not in one single
assembly line — there are actually **two separate workflows** sharing the same scoring code:

- **Track A (agents 1-5, 7)** — how we built and validated the scoring formula in the first
  place. You run this once, as a developer, not per gene lookup.
- **Track B (agent 3's `score_new_gene.py` + agent 9)** — the actual "type in a gene name,
  get scored guides" product workflow. This is what an end user actually touches.
- **Agents 6 and 8** are a shared experiment-loop layer both tracks feed into: rank what to
  test next, and sync with the real lab notebook (Benchling).

### Track A — building and validating the formula

**Agent 1 — go find relevant scientific papers.**
You give it a topic (like "CRISPRi guide RNA screening"), and it searches biomedical
literature (via a tool called Paperclip) and saves the full text of whatever it finds.
- Reads: a topic you type in
- Writes: paper files under `agent1_literature_search/output/`

**Agent 2 — read those papers and pull out the useful facts.**
For every paper Agent 1 found, this extracts: what kind of experiment it was, which genes
were targeted, what the results were, and what cell type was used. Turns messy paper text
into a clean structured summary.
- Reads: Agent 1's saved papers
- Writes: one summary file per paper, plus a combined table, under `agent2_literature_summarization/output/`

**Agent 3 — turn all that literature into an actual scoring formula.**
This is the core deliverable: a Python module (`guide_scoring.py`) that takes a guide RNA
and computes a score out of it, combining sequence quality + chromatin accessibility. (A
third component, off-target risk, was attempted and removed — see "What we've actually
found so far" below.) Every part of the formula is written down and justified by a specific
paper Agent 2 found — nothing is a mystery black box.
- Reads: Agent 2's paper summaries
- Writes: `agent3_metric_construction/guide_scoring.py` (the code) and `SPEC.md` (the explanation)

**Agent 4 — check if the formula actually works, against real data.**
This doesn't use any AI at all — it's a plain data-analysis script. It runs Agent 3's
formula against Ito et al.'s real experiment (199 guides where we *know* the actual
measured editing efficiency) and checks: does the formula's ranking match what really
happened in the lab?
- Reads: Agent 3's formula + the real experiment data
- Writes: a results table, a chart, and a written verdict, under `agent4_benchmarking/output/`

**Agent 5 — play devil's advocate on everything above.**
This agent's whole job is to be skeptical: does the formula secretly contradict a paper it
cites? Is a "confident" score actually just hiding missing data? It reads all the above and
writes an honest critique with a confidence rating per guide, instead of just assuming the
pipeline is trustworthy.
- Reads: Agent 3's formula + Agent 4's results
- Writes: a confidence rating (with reasons) for each guide, under `agent5_confidence_assessment/output/`

**Agent 7 — keep an audit trail of where every number came from.**
For any score CellGuide gives you, this lets you trace it back: which paper justified this
part of the formula, what did that paper actually say, and how confident are we. This is
what makes the whole system explainable instead of "trust the AI."
- Reads: Agent 3's spec + everyone else's outputs
- Writes: a traceable link from every score to its source paper, under `agent7_provenance/output/`

### Track B — score a gene on demand

This is the workflow an actual end user touches: type in a gene name, get back ranked guide
candidates, and see whether any of them have already been tested and reported elsewhere.
It doesn't need Track A to have been (re-)run first — it only needs Agent 3's scoring
library code to exist.

**Agent 3's `score_new_gene.py` — score a gene that isn't in our benchmark dataset.**
Given a gene symbol, this looks up its real coordinates, fetches its real genomic sequence,
scans for real candidate guide sites, and scores each one with a real trained on-target model
(Azimuth). No AI involved — pure lookup + a published model. Every failure (gene not found,
sequence fetch failed, model not installed) is reported in plain language, never silently
guessed around.
- Reads: a gene name you type in
- Writes: ranked candidate guides with scores, printed / returned as JSON

**Agent 9 — check whether a high-scoring guide has been reported before.**
Takes the top-scoring guides from `score_new_gene.py` and searches the literature **by gene
name** (not by pasting in a raw DNA sequence — that's not how literature search engines work)
for any paper that explicitly reports testing one of those exact sequences, at what
efficiency, and in what cell type / delivery method. The actual "does this sequence match" 
check is a plain string comparison done in code afterward, not something asked of the AI.
- Reads: a gene name (searches literature) + `score_new_gene.py`'s top candidates (matches against them)
- Writes: which candidates matched a prior report (and what it said), under `agent9_guide_literature_match/output/<gene>/`

### Shared — closing the loop with real experiments

**Agent 6 — decide what to test next in the lab.**
Given all the candidate guides (from either track) and how confident/uncertain we are about
each one, this picks the guide that's most worth spending a real wet-lab experiment on (high
potential + high uncertainty = most worth resolving). Once a real result comes back, you feed
it in here and it updates its recommendation — this is the "closing the loop" part.
- Reads: candidate guide scores + Agent 5's confidence + a log of what's already been tested
- Writes: ranked next-experiment suggestions, under `agent6_next_experiment/output/`

**Agent 8 — connect to the real lab notebook system (Benchling).**
This pushes Agent 6's "test this next" recommendation into Benchling (where the actual wet
lab team works), and pulls back real recorded results once they exist — so the loop from
"AI recommends an experiment" to "human runs it" to "AI updates its ranking" is fully
connected, not just simulated locally.
- Reads: Agent 6's top recommendation + new results recorded in Benchling
- Writes: pushes to Benchling; feeds new results back into Agent 6

Each agent's folder has its own `README.md` with the exact commands to run it. The full
technical spec (including safety rules about what each agent is and isn't allowed to touch)
is in [`CLAUDE.md`](CLAUDE.md).

## What we've actually found so far

We ran this against real data, and it gave us an honest, humbling result — twice, as we dug
deeper.

**Round 1**: our first version of the scoring formula (sequence + chromatin accessibility +
off-target risk, all blended together) actually scored **worse** at predicting real editing
efficiency than just using the sequence part alone (correlation of 0.315 for the blended
formula vs. 0.441 for sequence alone, out of 199 real guides). Agent 5's critique found
concrete bugs behind this — e.g. the "off-target risk" part of the formula defaulted to
"perfectly safe" whenever no off-target data existed, instead of "unknown," silently making
every guide look safer than it actually was. We fixed these (see
[`agent3_metric_construction/SPEC.md`](agent3_metric_construction/SPEC.md)), and the formula
now exposes `recommended_score` (sequence-only) instead of pretending the blended version
was better.

**Round 2**, after re-running Agent 5 against the fixed formula, it went further and
initially concluded chromatin accessibility — this project's core premise — hadn't
demonstrated value on this benchmark:
- Off-target risk (specificity) was never evaluated for any of the 199 guides — no
  off-target data source ever got wired in (crispAI/CrisprBERT need API access we don't have;
  GuideScan2 needs a genome index we couldn't build). **It's since been removed from the
  scoring library entirely** rather than kept as a permanently-empty field — see
  `agent3_metric_construction/SPEC.md`. The score is a 2-component blend now, openly.
- The underlying ATAC-seq measurement is unstable: the source data has two replicate
  measurements for the same guides, and switching between them flips which guides "pass" the
  accessibility threshold for the majority of borderline cases. **This one still stands too**
  — real caution is warranted regardless of what follows.
- The specific claim CellGuide is named after — that the *same* guide performs differently
  in different cell types — still has no data in this benchmark that can actually test it.
  **Also still stands** — this is the biggest open gap.

We also tried two follow-ups to see if a sequence-side signal could be rescued: scoring
guides with only our own from-scratch sequence heuristic (instead of the two external tools
we normally prefer), and averaging the two ATAC replicates instead of using one. Neither
helped — the heuristic has no real signal on its own (ρ=0.043, not significant), and
averaged ATAC is still not statistically significant (ρ=0.062, p=0.386). See
[`agent4_benchmarking/output/MOTIF_AND_ACCESSIBILITY_CHECKS.md`](agent4_benchmarking/output/MOTIF_AND_ACCESSIBILITY_CHECKS.md).

**Round 3**: Round 2 also claimed the accessibility gate "reduces prediction quality"
(F1 0.593 → 0.431) and that accessibility overall showed no real signal (marginal
correlation ρ=0.084, not significant). Re-running Agent 5 a second time against the more
transparent report, it caught that **both of those were the wrong statistical test** —
Ito et al.'s actual published claim is conditional ("high ATAC-seq scores were significantly
associated with efficient indel formation *among gRNAs with above-median [sequence] scores*"),
not a marginal effect across every guide, and F1 mechanically penalizes any added
precision-focused filter regardless of whether it's a good one. Tested the way the paper
actually frames it
([`agent4_benchmarking/output/INTERACTION_EFFECT_CHECK.md`](agent4_benchmarking/output/INTERACTION_EFFECT_CHECK.md)):
**the conditional effect reproduces — ρ=0.232, p=0.008 among the 131 guides with
above-median sequence scores** — and the gate's precision does rise as designed (0.741 →
0.862). So the corrected, current honest read is: **accessibility has real conditional
predictive value that the first test missed, but it isn't correctly folded into a single
score yet** — a more defensible (and more interesting) position than either "it clearly
works" or "it clearly doesn't."

**Open, in progress**: the ρ=0.441 number above comes entirely from Ito's own precomputed
DeepSpCas9/CHOPCHOP scores — not Azimuth, the model Track B's `score_new_gene.py` actually
uses for genes outside Ito's 199. Conflating the two would be the same kind of
unearned-credibility mistake as the specificity fallback, so we're separately validating
Azimuth in-context: reconstructing real genomic 30-mer context for Ito's own guides (gene
lookup → real sequence → real PAM scan → exact spacer match, no fabrication) and running
Azimuth on them directly, to get a real number for that specific path. This is a
multi-minute batch job (real Ensembl lookups for ~75 genes) and wasn't finished as of this
writing — check
[`agent4_benchmarking/output/AZIMUTH_VALIDATION_CHECK.md`](agent4_benchmarking/output/AZIMUTH_VALIDATION_CHECK.md)
for whether it's since completed before citing a number from it (an early n=4 smoke-test
version of this file exists and is not the real result — check the `n` in its table before
trusting it).

Full numbers: [`agent4_benchmarking/output/REPORT.md`](agent4_benchmarking/output/REPORT.md)
and [`agent4_benchmarking/output/REPLICATE_SENSITIVITY_REPORT.md`](agent4_benchmarking/output/REPLICATE_SENSITIVITY_REPORT.md).
Full critique: [`agent5_confidence_assessment/output/CONFIDENCE_REPORT.md`](agent5_confidence_assessment/output/CONFIDENCE_REPORT.md).

We think surfacing this — instead of quietly shipping a demo that only shows the flattering
numbers — is itself evidence the validation loop here is real: a rigged pipeline doesn't
keep finding new ways it might be wrong.

### Key numbers at a glance (for slides)

| Claim | Number | Source |
|---|---|---|
| Sequence-only predicts real editing efficiency | ρ = 0.441, p = 7×10⁻¹¹, n = 199 | `agent4_benchmarking/output/REPORT.md` |
| Our shipped blended score is *worse* than sequence alone | ρ = 0.315 (blend) vs 0.441 (sequence) | same |
| Accessibility has **no** marginal effect (naive test) | ρ = 0.084, p = 0.24, n.s. | same |
| Accessibility **does** have a real conditional effect (correct test, Ito's actual claim) | ρ = 0.232, p = 0.008, n = 131 (above-median-sequence subset) | `INTERACTION_EFFECT_CHECK.md` |
| Our own GC/motif fallback heuristic has no real signal | ρ = 0.043, p = 0.54, n.s. | `MOTIF_AND_ACCESSIBILITY_CHECKS.md` |
| Off-target/specificity assessment | **not implemented** — tried, no real data source, removed | `agent3_metric_construction/SPEC.md` |
| ATAC measurement is replicate-sensitive | passing-guide set changes between the two real replicates | `REPLICATE_SENSITIVITY_REPORT.md` |

**One-paragraph pitch, if you need it**: sequence-only CRISPR guide scores don't transfer
across cell types because they can't see chromatin accessibility — and the naive way to fix
that (a linear blend) makes things worse, not better, unless you know exactly how accessibility
actually interacts with sequence (conditionally, not additively). We built a pipeline that
found that the hard way, on real data, and stayed honest about it — including everywhere it
still doesn't work.

**Careful with these claims on a slide** (things that are easy to overstate):
- Don't say "CellGuide predicts off-target risk" — it explicitly doesn't; say so if asked.
- Don't present ρ=0.441 as "our model's accuracy" — it's DeepSpCas9/CHOPCHOP's (published,
  external tools), validated in our pipeline; our own added value is 2 pts of validation to that.
- Don't call the accessibility result a clean win — it's "real conditional signal not yet
  folded into the shipped score," which is a more defensible and more interesting claim than
  "it works."
- Track B (score a real new gene) is real and runnable, but its Azimuth-scored guides for
  genes outside Ito's 199 are **not** covered by the ρ=0.441 number — that path's own
  in-context validation is a separate, still-running check (see the paragraph above);
  don't imply Track B inherits Track A's validated accuracy until that finishes.

## Dashboard

[`dashboard/cellguide-dashboard.html`](dashboard/cellguide-dashboard.html) is a single
self-contained HTML file (no server, no build step) — open it directly in a browser for a
visual walkthrough. Good for screenshots/screen-recording for a slide deck.

- Tabs 01-06 are **Track A**: a scripted *replay* of a real prior pipeline run (real numbers,
  canned animation — the page says so explicitly; it does not re-execute anything live).
- Tab 07 ("Score a Gene") is **Track B**: a static demo of the real `score_new_gene.py` +
  Agent 9 output for one real example gene (BCL11A), including a real example of the
  honest-failure output when a data source (paperclip) wasn't available.
- Every tab carries the same warnings as the "key numbers" table above (a persistent banner
  at the top, plus inline caveats near each chart) — if you're pulling a screenshot for a
  slide, keep the caveat text in frame, or restate it in your own words on the slide.

## Setup

You need [`uv`](https://docs.astral.sh/uv/) installed (it manages Python for you — you don't
need Python already installed separately).

```bash
uv sync
```

This reads `pyproject.toml` and installs everything into a local `.venv/` folder.

Then create a `.env` file in the repo's root folder (this file holds secrets, so it's
git-ignored — it will never get committed or pushed anywhere):

```bash
ANTHROPIC_API_KEY='sk-ant-...'      # lets Agents 1, 2, 5, 9 call Claude
PAPERCLIP_API_KEY='gxl_...'         # lets Agents 1 and 9 search literature — get a key at https://paperclip.gxl.ai/keys
BENCHLING_API_KEY='sk_...'          # lets Agent 8 talk to Benchling — get one from Benchling's Developer Console
BENCHLING_TENANT_URL='https://...'
BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID='assaysch_...'
BENCHLING_RESULTS_SCHEMA_ID='assaysch_...'
```

Agent 3 (including `score_new_gene.py`), Agent 4, Agent 6, Agent 7, and Agent 9's
`match_guides.py` are plain Python with no AI calls — they don't need any API keys at all.
Only Agent 9's `search_literature.py` step needs `ANTHROPIC_API_KEY` + `PAPERCLIP_API_KEY`
(same as Agent 1).

### Tests

```bash
uv run pytest tests/
```

Unit tests for the deterministic parts of the pipeline (`guide_scoring.py`, `genome_lookup.py`,
`recommend.py`'s ranking math, `agent7_provenance/build.py`'s SPEC.md parsing) — no network
calls, no API keys needed. One test in `test_guide_scoring.py` exercises the real Azimuth model
if `~/miniforge3/envs/azimuth` is set up on your machine (see
[agent3_metric_construction/README.md](agent3_metric_construction/README.md)); it's skipped
automatically otherwise.

## How to actually run it, step by step

Run each of these from the repo's root folder.

**Track A — build/validate the formula (run once, as a developer):**

```bash
# Step 1: search for papers on a topic
uv run agent1_literature_search/run.py "CRISPRi guide RNA library screening"

# Step 2: summarize whatever new papers Step 1 found
uv run agent2_literature_summarization/run.py

# (Step 3 has no command to run — it's just the guide_scoring.py file, used by Steps 4+)

# Step 4: check the scoring formula against real experimental data
uv run agent4_benchmarking/run.py --data papers/ito_2024/table_s1_for_agent4.csv
# (or, just to check the script itself works, without needing real data:)
uv run agent4_benchmarking/run.py --demo

# Step 5: get a critical review of the formula and Step 4's results
uv run agent5_confidence_assessment/run.py --results agent4_benchmarking/output/results.csv

# Step 7: build the "which paper backs this number" trace
uv run agent7_provenance/build.py --results agent4_benchmarking/output/results.csv
```

**Track B — score an actual gene (the end-user workflow):**

```bash
# Score a gene not in our benchmark dataset — no AI, just real lookup + a real model
uv run agent3_metric_construction/score_new_gene.py BCL11A --top 10

# Check whether the top-scoring guides were reported before (step 1: LLM search by gene name)
uv run agent9_guide_literature_match/search_literature.py BCL11A

# Then match those literature results against the scored candidates (step 2: no AI, exact match)
uv run agent9_guide_literature_match/match_guides.py BCL11A --top 10
```

**Shared — closing the loop with real experiments (feed in candidates from either track):**

```bash
# Get a recommendation for what to test next
uv run agent6_next_experiment/recommend.py recommend \
    --candidates agent4_benchmarking/output/results.csv --top 5

# Sync recommendations/results with Benchling (needs schemas set up first — see agent8_benchling_sync/README.md)
uv run agent8_benchling_sync/run.py --candidates agent4_benchmarking/output/results.csv
```

Each command prints what it did, and writes its full output into that agent's own `output/`
folder, so you can always go look at exactly what was produced.

## What's in this folder

- `docs/` — the original project plan (PDF) and design notes
- `papers/` — the core scientific papers the whole project is built on (most importantly,
  `papers/ito_2024/`, the real experiment we validate against)
- `agent1_literature_search/` through `agent9_guide_literature_match/` — the steps described
  above (numbered by build order, not flow order — see "How it's built" for which track each
  one belongs to); each one is self-contained with its own code and its own `output/` folder
- `agents_common.py` — a small shared helper file (loads `.env`, sets up the literature
  search connection) used by Agents 1, 2, 5, and 9

For the full technical spec — exactly what each agent is allowed to read/write, cost limits,
and why those limits exist — see [`CLAUDE.md`](CLAUDE.md).
