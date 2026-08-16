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

Instead of one big model trying to do everything, this is broken into **8 small, single-job
agents that run one after another** — like a factory assembly line. Each agent does one
specific task, saves its output to a file, and the next agent reads that file as its input.
This makes every step easy to inspect, re-run on its own, and debug independently, instead
of one big opaque process where you can't tell what happened or why.

Here's the assembly line, in order:

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
and computes a score out of it, combining sequence quality + chromatin accessibility +
off-target risk. Every part of the formula is written down and justified by a specific paper
Agent 2 found — nothing is a mystery black box.
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

**Agent 6 — decide what to test next in the lab.**
Given all the candidate guides and how confident/uncertain we are about each one, this picks
the guide that's most worth spending a real wet-lab experiment on (high potential + high
uncertainty = most worth resolving). Once a real result comes back, you feed it in here and
it updates its recommendation — this is the "closing the loop" part.
- Reads: candidate guide scores + Agent 5's confidence + a log of what's already been tested
- Writes: ranked next-experiment suggestions, under `agent6_next_experiment/output/`

**Agent 7 — keep an audit trail of where every number came from.**
For any score CellGuide gives you, this lets you trace it back: which paper justified this
part of the formula, what did that paper actually say, and how confident are we. This is
what makes the whole system explainable instead of "trust the AI."
- Reads: Agent 3's spec + everyone else's outputs
- Writes: a traceable link from every score to its source paper, under `agent7_provenance/output/`

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

Full numbers: [`agent4_benchmarking/output/REPORT.md`](agent4_benchmarking/output/REPORT.md)
and [`agent4_benchmarking/output/REPLICATE_SENSITIVITY_REPORT.md`](agent4_benchmarking/output/REPLICATE_SENSITIVITY_REPORT.md).
Full critique: [`agent5_confidence_assessment/output/CONFIDENCE_REPORT.md`](agent5_confidence_assessment/output/CONFIDENCE_REPORT.md).

We think surfacing this — instead of quietly shipping a demo that only shows the flattering
numbers — is itself evidence the validation loop here is real: a rigged pipeline doesn't
keep finding new ways it might be wrong.

Full write-up: [`agent4_benchmarking/output/REPORT.md`](agent4_benchmarking/output/REPORT.md)
(the numbers) and
[`agent5_confidence_assessment/output/CONFIDENCE_REPORT.md`](agent5_confidence_assessment/output/CONFIDENCE_REPORT.md)
(the critique).

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
ANTHROPIC_API_KEY='sk-ant-...'      # lets Agents 1, 2, 5 call Claude
PAPERCLIP_API_KEY='gxl_...'         # lets Agent 1 search literature — get a key at https://paperclip.gxl.ai/keys
BENCHLING_API_KEY='sk_...'          # lets Agent 8 talk to Benchling — get one from Benchling's Developer Console
BENCHLING_TENANT_URL='https://...'
BENCHLING_NEXT_EXPERIMENT_SCHEMA_ID='assaysch_...'
BENCHLING_RESULTS_SCHEMA_ID='assaysch_...'
```

Agents 3, 4, 6, and 7 are plain Python with no AI calls — they don't need any API keys at all.

## How to actually run it, step by step

Run each of these from the repo's root folder:

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

# Step 6: get a recommendation for what to test next
uv run agent6_next_experiment/recommend.py recommend \
    --candidates agent4_benchmarking/output/results.csv --top 5

# Step 7: build the "which paper backs this number" trace
uv run agent7_provenance/build.py --results agent4_benchmarking/output/results.csv

# Step 8: sync recommendations/results with Benchling (needs schemas set up first — see agent8_benchling_sync/README.md)
uv run agent8_benchling_sync/run.py --candidates agent4_benchmarking/output/results.csv
```

Each command prints what it did, and writes its full output into that agent's own `output/`
folder, so you can always go look at exactly what was produced.

## What's in this folder

- `docs/` — the original project plan (PDF) and design notes
- `papers/` — the core scientific papers the whole project is built on (most importantly,
  `papers/ito_2024/`, the real experiment we validate against)
- `agent1_literature_search/` through `agent8_benchling_sync/` — the 8 steps described
  above; each one is self-contained with its own code and its own `output/` folder
- `agents_common.py` — a small shared helper file (loads `.env`, sets up the literature
  search connection) used by Agents 1, 2, and 5

For the full technical spec — exactly what each agent is allowed to read/write, cost limits,
and why those limits exist — see [`CLAUDE.md`](CLAUDE.md).
