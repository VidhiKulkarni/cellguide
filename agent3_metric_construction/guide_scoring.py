"""
CellGuide AI — Agent 3: per-guide efficiency + specificity scoring.

Implements the plan's §4.4 formula:
    score(g, c) = w_seq * sequence_efficacy(g) + w_atac * accessibility(g, c) + w_spec * specificity(g)

Design principle (per docs/CellGuide_AI_Hackathon_Plan.pdf §2): keep every
component inspectable and swappable. Each function here accepts an optional
external model score (e.g. DeepHF, CHOPCHOP, crispAI, CrisprBERT) and falls
back to a transparent sequence-only heuristic when none is supplied, so the
pipeline never depends on a single black-box predictor.

Literature basis (see papers/ for full sources):
- ito_2024: empirical rule DeepSpCas9>=60 AND CHOPCHOP>=0.3 AND ATAC>=0.1 ->
  reliably efficient guide in primary human T cells (transient RNP delivery).
  Ito et al. report NO off-target data, so specificity must come from elsewhere.
- wang_2019_deephf: best on-target model = RNN + hand-crafted features
  (GC content, melting temperature / secondary-structure accessibility);
  DNase-I accessibility fine-tuning did NOT help in their lentiviral-integrated
  assay, unlike Ito's transient-RNP result -> accessibility's value is
  delivery-context-dependent, not universal.
- ozden2024_crispai_uncertainty / sari2025_crisprbert: off-target predictors
  trained on the same CHANGE-seq primary-T-cell dataset Ito's cohort comes
  from -> recommended external specificity scorers.
- riesenberg2025_synthetic_grna: indel% can also *underestimate* true cutting
  activity -> treat sequence_efficacy as a ranking signal, not a calibrated
  probability.
"""

from dataclasses import dataclass
from typing import Optional, Sequence


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


def poly_t_penalty(spacer: str) -> float:
    """U6-promoter transcription terminates on TTTT+ -> guides containing it are penalized."""
    return 0.0 if "TTTT" in spacer.upper() else 1.0


def seed_gc_score(spacer: str, seed_len: int = 10) -> float:
    """GC content of the PAM-proximal seed region (last `seed_len` nt), which dominates
    Cas9 binding/cleavage specificity and activity (Doench-style seed-region weighting)."""
    seed = spacer[-seed_len:]
    return gc_content_score(seed)


def sequence_motif_score(spacer: str) -> float:
    """Composite transparent sequence heuristic: GC content + seed-region GC + poly-T penalty.
    Used as the sequence_efficacy fallback when no external on-target model score is given."""
    return (
        0.4 * gc_content_score(spacer)
        + 0.4 * seed_gc_score(spacer)
        + 0.2 * poly_t_penalty(spacer)
    )


def sequence_efficacy(
    spacer: str,
    deepspcas9_score: Optional[float] = None,
    chopchop_score: Optional[float] = None,
) -> float:
    """On-target efficacy in [0, 1]. Prefers Ito et al.'s own two sequence-only
    tools when available — deepspcas9_score on its native 0-100 scale, chopchop_score
    already on 0-1 — averaging whichever are supplied; falls back to the transparent
    GC/motif heuristic when neither is given."""
    normalized = []
    if deepspcas9_score is not None:
        normalized.append(max(0.0, min(1.0, deepspcas9_score / 100.0)))
    if chopchop_score is not None:
        normalized.append(max(0.0, min(1.0, chopchop_score)))
    if normalized:
        return sum(normalized) / len(normalized)
    return sequence_motif_score(spacer)


# ---------------------------------------------------------------------------
# Accessibility (cell context)
# ---------------------------------------------------------------------------

def accessibility_score(atac_signal: Optional[float], threshold: float = 0.1) -> float:
    """Cell-context chromatin accessibility term, per Ito et al.'s empirical ATAC>=0.1 cutoff.
    `atac_signal` is the median ATAC read-count/signal over the guide's target window in the
    target cell type (see docs/CellGuide_AI_Hackathon_Plan.pdf §3.1, §4.1). Returns 0 when no
    ATAC data is available for that context, so the term drops out of the combined score
    rather than being guessed."""
    if atac_signal is None:
        return 0.0
    return min(1.0, atac_signal / threshold) if threshold > 0 else float(atac_signal > 0)


# ---------------------------------------------------------------------------
# Specificity (off-target)
# ---------------------------------------------------------------------------

@dataclass
class OffTargetSite:
    mismatches: int
    mismatch_positions: Sequence[int]  # 0 = PAM-distal end, 19 = PAM-proximal
    cfd_pam_score: float = 1.0  # non-NGG PAM penalty, 1.0 for canonical NGG


# Doench et al. 2016 CFD mismatch-position weight table (position-dependent tolerance;
# PAM-proximal mismatches are far more disruptive than PAM-distal ones).
_CFD_POSITION_WEIGHTS = [
    0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91,
    0.87, 0.78, 0.68, 0.61, 0.55, 0.42, 0.33, 0.24, 0.18, 0.11,
]


def _site_cfd_penalty(site: OffTargetSite) -> float:
    """Approximate CFD-style penalty for one off-target site: product of per-mismatch
    position weights, scaled by the PAM score. 1.0 = fully tolerated (dangerous),
    0.0 = fully rejected (safe)."""
    penalty = site.cfd_pam_score
    for pos in site.mismatch_positions:
        idx = min(max(pos, 0), len(_CFD_POSITION_WEIGHTS) - 1)
        penalty *= _CFD_POSITION_WEIGHTS[idx]
    return penalty


def cfd_specificity(offtargets: Sequence[OffTargetSite]) -> float:
    """Aggregate specificity score in [0, 1] from an enumerated off-target site list
    (e.g. from Cas-OFFinder/GuideScan2 — see papers/related/schmidt2025_guidescan2/).
    1.0 = no tolerated off-target sites found; approaches 0 as tolerated sites accumulate.
    This is the standard CFD aggregate: 1 / (1 + sum of per-site penalties)."""
    if not offtargets:
        return 1.0
    total_penalty = sum(_site_cfd_penalty(s) for s in offtargets)
    return 1.0 / (1.0 + total_penalty)


def specificity(
    offtargets: Optional[Sequence[OffTargetSite]] = None,
    external_score: Optional[float] = None,
) -> float:
    """Specificity in [0, 1] (1 = highly specific / low off-target risk).
    Prefers a pluggable external off-target model — crispAI (papers/related/
    ozden2024_crispai_uncertainty/) or CrisprBERT (papers/related/sari2025_crisprbert/),
    both trained on the same primary-T-cell CHANGE-seq data Ito et al.'s cohort comes
    from, which is recommended here because Ito et al. report no off-target data of
    their own. Falls back to CFD aggregation over an enumerated off-target site list."""
    if external_score is not None:
        return max(0.0, min(1.0, external_score))
    return cfd_specificity(offtargets or [])


# ---------------------------------------------------------------------------
# Combined CellGuide score
# ---------------------------------------------------------------------------

@dataclass
class GuideScoreWeights:
    """Default weights are a starting point (plan §4.4: "Start with transparent
    weights ... compare against sequence-only"), not fit to data. Re-derive via
    regression against papers/ito_2024/ ground truth in Agent 4."""
    w_seq: float = 0.4
    w_atac: float = 0.3
    w_spec: float = 0.3


@dataclass
class GuideScoreInputs:
    spacer: str
    deepspcas9_score: Optional[float] = None  # native 0-100 scale
    chopchop_score: Optional[float] = None  # native 0-1 scale
    atac_signal: Optional[float] = None
    offtargets: Optional[Sequence[OffTargetSite]] = None
    external_specificity_score: Optional[float] = None


@dataclass
class GuideScoreResult:
    sequence_efficacy: float
    accessibility: float
    specificity: float
    combined: float
    passes_ito_rule: bool


def score_guide(inputs: GuideScoreInputs, weights: GuideScoreWeights = GuideScoreWeights()) -> GuideScoreResult:
    """Compute the CellGuide score for one guide in one cell context."""
    seq_eff = sequence_efficacy(inputs.spacer, inputs.deepspcas9_score, inputs.chopchop_score)
    acc = accessibility_score(inputs.atac_signal)
    spec = specificity(inputs.offtargets, inputs.external_specificity_score)
    combined = weights.w_seq * seq_eff + weights.w_atac * acc + weights.w_spec * spec
    return GuideScoreResult(
        sequence_efficacy=seq_eff,
        accessibility=acc,
        specificity=spec,
        combined=combined,
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
