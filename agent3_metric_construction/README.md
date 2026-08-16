# Agent 3 — metric construction

Not an automated script — this is the deliverable itself: a documented, transparent
scoring function derived from [Agent 2](../agent2_literature_summarization/)'s structured
literature summaries.

- `guide_scoring.py` — the scoring library (`score_guide`, `sequence_efficacy`,
  `accessibility_score`, `passes_ito_thresholds`, ...). No `specificity` — it was tried and
  removed; see `SPEC.md` "Known limitations" for why.
- `SPEC.md` — inputs, weights, and the literature rationale behind each term

## Use

```python
from guide_scoring import GuideScoreInputs, score_guide

score_guide(GuideScoreInputs(spacer="...", deepspcas9_score=71.2, chopchop_score=0.61, atac_signal=0.42))

# for a guide with no deepspcas9/chopchop score (e.g. not in Ito et al.'s dataset), give the
# full 30-mer genomic context instead and it'll use a real trained model (Azimuth) if set up:
score_guide(GuideScoreInputs(spacer="...", context_30mer="ACAGCTGATCTCCAGATATGACCATGGGTT"))
```

Consumed by [Agent 4](../agent4_benchmarking/) for validation.

## Scoring a gene NOT in Ito et al.'s dataset

```bash
uv run agent3_metric_construction/score_new_gene.py BCL11A --window 2000 --top 10
```

End-to-end: real Ensembl gene lookup → real sequence fetch → real NGG PAM scan (both
strands) → batched Azimuth scoring. Every result and every failure is reported in plain
language (`status`, `messages`) — gene not found, sequence fetch failed, Azimuth not set up,
no ATAC data given, etc. — this is the "honest UI" entry point: whatever this script prints
is safe to show a user directly, nothing is silently guessed. See `genome_lookup.py` for the
sequence/PAM-scanning half.

## Azimuth on-target model setup (optional, for guides outside Ito et al.'s dataset)

`sequence_efficacy()` uses a real trained model (Doench et al. 2016 Rule Set 2,
[PMID 26780180](https://pubmed.ncbi.nlm.nih.gov/26780180/)) when `context_30mer` is given and
no `deepspcas9_score`/`chopchop_score` is available. It needs an isolated conda environment
(old scikit-learn/biopython, incompatible with this project's main Python 3.12 env):

```bash
# one-time setup, if ~/miniforge3 doesn't already exist:
curl -fsSL -o /tmp/Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh"
bash /tmp/Miniforge3.sh -b -p "$HOME/miniforge3"

"$HOME/miniforge3/bin/mamba" create -y -n azimuth -c conda-forge "python<3.9" "scikit-learn=0.24.1" numpy scipy pandas biopython pip
"$HOME/miniforge3/bin/mamba" run -n azimuth pip install --no-deps "git+https://github.com/Biomatters/Azimuth.git"
"$HOME/miniforge3/bin/mamba" install -y -n azimuth -c conda-forge "biopython<1.77"  # modern biopython removed Tm_staluc, which this old codebase needs
```

`guide_scoring.azimuth_available()` checks whether this is set up; `azimuth_score()` returns
`None` gracefully if not, so the rest of the pipeline works fine without it — this only
unlocks scoring for genes/guides outside Ito et al.'s own 199-guide dataset.
