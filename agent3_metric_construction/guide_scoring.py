"""
CellGuide AI — Agent 3: per-guide efficiency scoring.

Implements the plan's §4.4 formula:
    score(g, c) = w_seq * sequence_efficacy(g) + w_atac * accessibility(g, c)
... but with weights renormalized over whatever components actually have data (see
score_guide), and with `recommended_score` exposed as the empirically better ranking value
(see below) — both fixes came directly out of Agent 5's skeptical review
(agent5_confidence_assessment/output/CONFIDENCE_REPORT.md) of the original version of this
module. That review's specific findings and this file's response to each:

1. specificity() — REMOVED (not just fixed). It used to return 1.0 ("perfectly safe")
   whenever no off-target data was supplied, silently rewarding guides nobody had checked;
   a later fix made it return None instead, but no real off-target data source was ever
   wired in (crispAI/CrisprBERT require API access we don't have; GuideScan2 requires a
   genome-wide index we couldn't build in this environment — see agent1_literature_search/
   output/related/schmidt2025_guidescan2/ for that dead end). Rather than keep a component
   that has never once returned a real value, it's gone: no OffTargetSite, no
   cfd_specificity(), no external_specificity_score input, no specificity field on
   GuideScoreResult. If a real off-target data source becomes available later, re-add it
   deliberately rather than resurrecting dead code.
2. accessibility_score() had no way to express delivery method, despite this module's own
   docstring warning that the accessibility term is validated for transient RNP only
   (Ito et al. 2024) and does NOT transfer to lentiviral/stable delivery (Wang et al. 2019).
   Fixed: GuideScoreInputs.delivery gates it — lentiviral/vector/stable contexts exclude
   accessibility from the combined score (None, renormalized away) rather than silently
   applying an unvalidated term.
3. Real-data benchmarking (agent4_benchmarking/output/REPORT.md, n=199 Ito et al. guides)
   found the linear `combined` score UNDERPERFORMS sequence_efficacy alone (rho=0.315 vs
   0.441) — because Ito et al. never linearly blend ATAC into a ranking score; they use it
   as an AND-gate filter on top of sequence scores (DeepSpCas9>=60 AND CHOPCHOP>=0.3 AND
   ATAC>=0.1, see passes_ito_thresholds()). Fixed: GuideScoreResult.recommended_score
   implements that — sequence_efficacy as the ranking value, passes_ito_rule as the
   accompanying gate to check separately, matching what the paper (and the benchmark) both
   support. `combined` is kept for transparency/comparison, not as the recommended value.
4. sequence_motif_score() (the fallback used when no external on-target score is supplied)
   double-counted GC content: spacer-wide GC and seed-region GC are highly correlated (the
   seed is a literal subset of the spacer) but were weighted as if independent, and the
   seed term reused the whole-spacer "50%-optimal" curve, an unvalidated transfer. Fixed:
   dropped the separate seed-region term; the fallback is now spacer GC + poly-T only.
5. poly_t_penalty() (U6-promoter transcription terminates on TTTT+) was applied
   unconditionally, including to Ito et al.'s guides — which are chemically synthesized RNP
   with no U6 promoter involved at all. Fixed: gated by GuideScoreInputs.delivery, same as
   accessibility; only applies when delivery indicates U6-driven vector expression.

Literature basis (see papers/ for full sources):
- ito_2024: empirical rule DeepSpCas9>=60 AND CHOPCHOP>=0.3 AND ATAC>=0.1 ->
  reliably efficient guide in primary human T cells (transient RNP delivery).
- wang_2019_deephf: best on-target model = RNN + hand-crafted features
  (GC content, melting temperature / secondary-structure accessibility);
  DNase-I accessibility fine-tuning did NOT help in their lentiviral-integrated
  assay, unlike Ito's transient-RNP result -> accessibility's value is
  delivery-context-dependent, not universal.
- riesenberg2025_synthetic_grna: indel% can also *underestimate* true cutting
  activity -> treat sequence_efficacy as a ranking signal, not a calibrated
  probability.
"""

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

Delivery = str  # "rnp" | "lentiviral" | "vector" | "stable" | None (unknown, treated as RNP-like)
_VECTOR_DELIVERIES = {"lentiviral", "vector", "stable"}

_AZIMUTH_SCORER = Path(__file__).resolve().parent / "azimuth_scorer.py"
_AZIMUTH_MAMBA = Path.home() / "miniforge3" / "bin" / "mamba"


# ---------------------------------------------------------------------------
# Sequence efficacy (on-target)
# ---------------------------------------------------------------------------

def gc_content(spacer: str) -> float:
    """Fraction of G/C bases in the 20-nt spacer. Optimal range ~40-60% (Wang et al. 2019)."""
    spacer = spacer.upper()
    return sum(b in "GC" for b in spacer) / len(spacer)


def gc_content_score(spacer: str) -> float:
    """Transparent GC heuristic: 1.0 at 50% GC, decaying linearly to 0 at 20%/80%."""
    gc = gc_content(spacer)
    return max(0.0, 1.0 - abs(gc - 0.5) / 0.3)


def poly_t_penalty(spacer: str, delivery: Optional[Delivery] = None) -> float:
    """U6-promoter transcription terminates on TTTT+ -> guides containing it are penalized
    *only* when delivery is U6-driven vector expression. Chemically synthesized RNP guides
    (Ito et al.'s method, and the default here) involve no promoter, so the rule doesn't
    mechanistically apply and is skipped (neutral 1.0) rather than misapplied."""
    if delivery not in _VECTOR_DELIVERIES:
        return 1.0
    return 0.0 if "TTTT" in spacer.upper() else 1.0


def sequence_motif_score(spacer: str, delivery: Optional[Delivery] = None) -> float:
    """Transparent sequence heuristic: GC content + poly-T penalty. Used as the
    sequence_efficacy fallback when no external on-target model score is given.

    No separate seed-region GC term: the seed (last ~10nt) is a subset of the spacer, so a
    second GC term over it double-counts a correlated feature, and reusing the whole-spacer
    "50%-optimal" curve for that shorter window is an unvalidated transfer — dropped rather
    than kept as an uncalibrated inflation of this heuristic's confidence.

    Caveat (agent4_benchmarking/output/MOTIF_AND_ACCESSIBILITY_CHECKS.md): tested against
    real data with DeepSpCas9/CHOPCHOP deliberately ignored, this heuristic has no
    statistically significant signal on its own (rho=0.043, p=0.544, n=199) — it's a
    reasonable-looking fallback for when no external score is available, not a validated
    predictor. Prefer supplying deepspcas9_score/chopchop_score whenever possible."""
    return 0.7 * gc_content_score(spacer) + 0.3 * poly_t_penalty(spacer, delivery)


def azimuth_available() -> bool:
    """Whether the isolated `azimuth` conda env (~/miniforge3/envs/azimuth) is set up on this
    machine. Azimuth (Doench et al. 2016 Rule Set 2, PMID 26780180) needs an old scikit-learn/
    biopython stack that can't coexist with this project's main Python 3.12 environment, so
    it runs as a subprocess in its own conda env instead — see azimuth_scorer.py."""
    return _AZIMUTH_MAMBA.exists() and _AZIMUTH_SCORER.exists()


def azimuth_score(context_30mer: str) -> Optional[float]:
    """Real Doench 2016 Rule Set 2 on-target score, via the isolated azimuth conda env.

    Requires the FULL 30-mer context — [4nt upstream][20nt spacer][NGG PAM][3nt downstream]
    — not just the bare 20nt spacer stored in GuideScoreInputs.spacer. A bare spacer padded
    with placeholder flanking bases would NOT be a valid substitute: Azimuth's model uses
    that flanking sequence (especially the PAM) as real features. Returns None (not a guess)
    when the azimuth env isn't set up, the input isn't a real 30-mer, or the subprocess
    fails — never fabricates a score from insufficient context.

    Known caveat: the installed model was trained under scikit-learn 0.23.2 and is loaded
    under 0.24.1 (the closest combination that would actually run in this environment —
    see agent3_metric_construction/README.md) — sklearn itself warns this "might lead to
    breaking code or invalid results." Predictions land in a sane range in spot checks, but
    this hasn't been independently re-validated against a known-answer set."""
    if not azimuth_available():
        return None
    if len(context_30mer) != 30:
        return None
    try:
        result = subprocess.run(
            [str(_AZIMUTH_MAMBA), "run", "-n", "azimuth", "python", str(_AZIMUTH_SCORER)],
            input=json.dumps([context_30mer]),
            capture_output=True,
            text=True,
            timeout=60,
        )
        scores = json.loads(result.stdout.strip().splitlines()[-1])
        return scores[0]  # None if azimuth_scorer.py itself couldn't score it
    except (subprocess.SubprocessError, json.JSONDecodeError, IndexError, ValueError):
        return None


def azimuth_score_batch(context_30mers: list[str]) -> list[Optional[float]]:
    """Same model as azimuth_score(), but scores every sequence in ONE subprocess call
    instead of one call per sequence — each `mamba run -n azimuth ...` invocation has real
    startup overhead (conda env activation, loading the pickled model), so scoring many
    candidate guides one at a time (e.g. score_new_gene.py scanning a whole gene) is
    impractically slow. Use this for anything beyond a single guide. Returns a list the same
    length as the input, with None per-entry for anything that isn't a valid 30-mer or that
    the subprocess couldn't score — never fabricates a value for a failed entry."""
    if not azimuth_available() or not context_30mers:
        return [None] * len(context_30mers)
    try:
        result = subprocess.run(
            [str(_AZIMUTH_MAMBA), "run", "-n", "azimuth", "python", str(_AZIMUTH_SCORER)],
            input=json.dumps(context_30mers),
            capture_output=True,
            text=True,
            timeout=300,
        )
        scores = json.loads(result.stdout.strip().splitlines()[-1])
        if len(scores) != len(context_30mers):
            return [None] * len(context_30mers)
        return scores
    except (subprocess.SubprocessError, json.JSONDecodeError, ValueError):
        return [None] * len(context_30mers)


SOURCE_REAL_TOOLS = "real tool score(s) (DeepSpCas9/CHOPCHOP) — validated against real Ito et al. 2024 outcomes, rho=0.441, n=199 (agent4_benchmarking/output/REPORT.md)"
SOURCE_AZIMUTH = "Azimuth (Doench et al. 2016) predictive model on real 30-mer genomic context — a real trained model, but not independently re-validated in this pipeline (see guide_scoring.README's sklearn-version caveat)"
SOURCE_GC_MOTIF_HEURISTIC = "GC/motif heuristic fallback — proven to have NO statistically significant predictive power on its own (rho=0.043, p=0.544, n=199, agent4_benchmarking/output/MOTIF_AND_ACCESSIBILITY_CHECKS.md); treat this score as a placeholder, not a real efficacy estimate"


def sequence_efficacy_with_source(
    spacer: str,
    deepspcas9_score: Optional[float] = None,
    chopchop_score: Optional[float] = None,
    delivery: Optional[Delivery] = None,
    context_30mer: Optional[str] = None,
    precomputed_azimuth_score: Optional[float] = None,
) -> tuple[float, str]:
    """Same as sequence_efficacy(), but also returns a human-readable string saying which
    tier actually produced the value — this is the "tell the user what data this came from"
    mechanism: every score is traceable to real-tool / real-model / unvalidated-heuristic,
    not just a bare float that requires reading source code to interpret."""
    normalized = []
    if deepspcas9_score is not None:
        normalized.append(max(0.0, min(1.0, deepspcas9_score / 100.0)))
    if chopchop_score is not None:
        normalized.append(max(0.0, min(1.0, chopchop_score)))
    if normalized:
        return sum(normalized) / len(normalized), SOURCE_REAL_TOOLS
    if precomputed_azimuth_score is not None:
        return max(0.0, min(1.0, precomputed_azimuth_score)), SOURCE_AZIMUTH
    if context_30mer is not None:
        az = azimuth_score(context_30mer)
        if az is not None:
            return max(0.0, min(1.0, az)), SOURCE_AZIMUTH
    return sequence_motif_score(spacer, delivery), SOURCE_GC_MOTIF_HEURISTIC


def sequence_efficacy(
    spacer: str,
    deepspcas9_score: Optional[float] = None,
    chopchop_score: Optional[float] = None,
    delivery: Optional[Delivery] = None,
    context_30mer: Optional[str] = None,
) -> float:
    """On-target efficacy in [0, 1]. Preference order: (1) Ito et al.'s own two sequence-only
    tools when available — deepspcas9_score on its native 0-100 scale, chopchop_score already
    on 0-1 — averaging whichever are supplied (this is what's validated against real Ito
    outcome data, ρ=0.441, n=199 — see agent4_benchmarking/output/REPORT.md); (2) a real
    trained model (Azimuth/Doench 2016) if the full 30-mer genomic context is available and
    the azimuth conda env is set up (see azimuth_score()) — for guides that aren't in Ito's
    own dataset and so have no deepspcas9_score/chopchop_score to use; (3) the transparent
    GC/motif heuristic, which has no proven signal on its own (see sequence_motif_score) —
    last resort only. See sequence_efficacy_with_source() for which tier was actually used."""
    return sequence_efficacy_with_source(spacer, deepspcas9_score, chopchop_score, delivery, context_30mer)[0]


# ---------------------------------------------------------------------------
# Accessibility (cell context)
# ---------------------------------------------------------------------------

def accessibility_score(
    atac_signal: Optional[float],
    delivery: Optional[Delivery] = None,
    threshold: float = 0.1,
) -> Optional[float]:
    """Cell-context chromatin accessibility term, per Ito et al.'s empirical ATAC>=0.1 cutoff
    (validated for transient RNP delivery only). `atac_signal` is the median ATAC read-count/
    signal over the guide's target window in the target cell type (see
    docs/CellGuide_AI_Hackathon_Plan.pdf §3.1, §4.1).

    Returns None (excluded from the combined score, not guessed) when: no ATAC data is
    available, OR delivery indicates lentiviral/vector/stable expression — Wang et al. 2019
    found accessibility fine-tuning did NOT help in that context, so applying this term
    there would be extrapolating past what's been validated, not filling a data gap."""
    if delivery in _VECTOR_DELIVERIES:
        return None
    if atac_signal is None:
        return None
    return min(1.0, atac_signal / threshold) if threshold > 0 else float(atac_signal > 0)


# ---------------------------------------------------------------------------
# Combined CellGuide score
# ---------------------------------------------------------------------------

@dataclass
class GuideScoreWeights:
    """Default weights are a starting point (plan §4.4: "Start with transparent
    weights ... compare against sequence-only"), not fit to data. Real-data benchmarking
    (agent4_benchmarking/output/REPORT.md) found the resulting linear `combined` score
    underperforms sequence_efficacy alone — see GuideScoreResult.recommended_score for the
    empirically better ranking value; these weights remain for the transparent, comparable
    `combined` field. Two components only — specificity was removed, see module docstring."""
    w_seq: float = 0.4
    w_atac: float = 0.3


@dataclass
class GuideScoreInputs:
    spacer: str
    deepspcas9_score: Optional[float] = None  # native 0-100 scale
    chopchop_score: Optional[float] = None  # native 0-1 scale
    atac_signal: Optional[float] = None
    delivery: Optional[Delivery] = None  # "rnp" | "lentiviral" | "vector" | "stable" | None
    context_30mer: Optional[str] = None  # [4nt upstream][20nt spacer][NGG PAM][3nt downstream] — for azimuth_score()
    precomputed_azimuth_score: Optional[float] = None  # if you already batch-scored this guide via
    # azimuth_score_batch() (much faster for many guides), pass the result here instead of
    # context_30mer to skip a redundant single-guide subprocess call


SOURCE_MEASURED_ATAC = "measured ATAC-seq signal for this cell type"
SOURCE_ACCESSIBILITY_UNAVAILABLE_NO_DATA = "unavailable: no ATAC signal was supplied for this guide/cell-type"
SOURCE_ACCESSIBILITY_UNAVAILABLE_DELIVERY = "unavailable: delivery method indicates lentiviral/vector/stable expression, and this term is only validated for transient RNP (Wang et al. 2019 vs Ito et al. 2024 — see SPEC.md Component 2)"


@dataclass
class GuideScoreResult:
    sequence_efficacy: float
    sequence_efficacy_source: str  # human-readable: which tier actually produced the value —
    # see SOURCE_REAL_TOOLS / SOURCE_AZIMUTH / SOURCE_GC_MOTIF_HEURISTIC
    accessibility: Optional[float]
    accessibility_source: str  # human-readable, always set even when accessibility is None —
    # see SOURCE_MEASURED_ATAC / SOURCE_ACCESSIBILITY_UNAVAILABLE_*
    combined: float
    recommended_score: float
    passes_ito_rule: bool


def score_guide(inputs: GuideScoreInputs, weights: GuideScoreWeights = GuideScoreWeights()) -> GuideScoreResult:
    """Compute the CellGuide score for one guide in one cell context.

    `combined`: the original transparent linear blend, kept for inspectability — weights
    are renormalized over whichever of (sequence, accessibility) actually have data for this
    guide, instead of guessing a value for a component nobody assessed.

    `recommended_score`: what to actually rank by. Real-data validation (n=199 Ito et al.
    guides) showed the linear blend underperforms sequence_efficacy alone (rho=0.315 vs
    0.441) — Ito et al.'s own method never linearly blends ATAC in; they gate on it. So
    recommended_score IS sequence_efficacy; check passes_ito_rule alongside it as the
    accessibility gate, rather than folding accessibility into the score continuously.
    """
    seq_eff, seq_eff_source = sequence_efficacy_with_source(
        inputs.spacer, inputs.deepspcas9_score, inputs.chopchop_score, inputs.delivery,
        inputs.context_30mer, inputs.precomputed_azimuth_score,
    )
    acc = accessibility_score(inputs.atac_signal, inputs.delivery)
    if acc is not None:
        acc_source = SOURCE_MEASURED_ATAC
    elif inputs.delivery in _VECTOR_DELIVERIES:
        acc_source = SOURCE_ACCESSIBILITY_UNAVAILABLE_DELIVERY
    else:
        acc_source = SOURCE_ACCESSIBILITY_UNAVAILABLE_NO_DATA

    components = [(weights.w_seq, seq_eff)]
    if acc is not None:
        components.append((weights.w_atac, acc))
    total_weight = sum(w for w, _ in components)
    combined = sum(w * v for w, v in components) / total_weight if total_weight else seq_eff

    return GuideScoreResult(
        sequence_efficacy=seq_eff,
        sequence_efficacy_source=seq_eff_source,
        accessibility=acc,
        accessibility_source=acc_source,
        combined=combined,
        recommended_score=seq_eff,
        passes_ito_rule=passes_ito_thresholds(
            deepspcas9=inputs.deepspcas9_score,
            chopchop=inputs.chopchop_score,
            atac_signal=inputs.atac_signal,
        ),
    )


def passes_ito_thresholds(
    deepspcas9: Optional[float] = None,
    chopchop: Optional[float] = None,
    atac_signal: Optional[float] = None,
    deepspcas9_cutoff: float = 60.0,
    chopchop_cutoff: float = 0.3,
    atac_cutoff: float = 0.1,
) -> bool:
    """Ito et al. 2024's empirical rule-based classifier (their raw thresholds, not
    the normalized [0,1] scores used elsewhere in this module): DeepSpCas9>=60 AND
    CHOPCHOP>=0.3 AND ATAC>=0.1 -> reliably efficient. Any missing input makes this
    unknown -> returns False rather than guessing."""
    if deepspcas9 is None or chopchop is None or atac_signal is None:
        return False
    return deepspcas9 >= deepspcas9_cutoff and chopchop >= chopchop_cutoff and atac_signal >= atac_cutoff
