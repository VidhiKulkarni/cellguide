# Agent 3 — metric construction

Not an automated script — this is the deliverable itself: a documented, transparent
scoring function derived from [Agent 2](../agent2_literature_summarization/)'s structured
literature summaries.

- `guide_scoring.py` — the scoring library (`score_guide`, `sequence_efficacy`,
  `accessibility_score`, `specificity`, `passes_ito_thresholds`, ...)
- `SPEC.md` — inputs, weights, and the literature rationale behind each term

## Use

```python
from guide_scoring import GuideScoreInputs, score_guide

score_guide(GuideScoreInputs(spacer="...", deepspcas9_score=71.2, chopchop_score=0.61, atac_signal=0.42))
```

Consumed by [Agent 4](../agent4_benchmarking/) for validation.
