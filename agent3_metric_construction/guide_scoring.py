"""
CellGuide AI — Agent 3: per-guide efficiency + specificity scoring.

Implements the plan's §4.4 formula:
    score(g, c) = w_seq * sequence_efficacy(g) + w_atac * accessibility(g, c) + w_spec * specificity(g)
... but with weights renormalized over whatever components actually have data (see
score_guide), and with `recommended_score` exposed as the empirically better ranking value
(see below) — both fixes came directly out of Agent 5's skeptical review
(agent5_confidence_assessment/output/CONFIDENCE_REPORT.md) of the original version of this
module. That review's specific findings and this file's response to each:

1. specificity() used to return 1.0 ("perfectly safe") whenever no off-target data was
   supplied, silently rewarding guides nobody had checked. Fixed: specificity() now returns
   None when truly nothing is known (no off-target list AND no external score) — an empty
   *enumerated* off-target list (a real search that found nothing) still legitimately scores
   1.0. score_guide() excludes None components and renormalizes the remaining weights,
   instead of guessing in either direction.
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

Delivery = str  # "rnp" | "lentiviral" | "vector" | "stable" | None (unknown, treated as RNP-like)
_VECTOR_DELIVERIES = {"lentiviral", "vector", "stable"}


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
    than kept as an uncalibrated inflation of this heuristic's confidence."""
    return 0.7 * gc_content_score(spacer) + 0.3 * poly_t_penalty(spacer, delivery)


def sequence_efficacy(
    spacer: str,
    deepspcas9_score: Optional[float] = None,
    chopchop_score: Optional[float] = None,
    delivery: Optional[Delivery] = None,
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
    return sequence_motif_score(spacer, delivery)


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
    """Aggregate specificity score in [0, 1] from an *enumerated* off-target site list
    (e.g. from Cas-OFFinder/GuideScan2 — see agent1_literature_search/output/related/
    schmidt2025_guidescan2/). 1.0 = a candidate search was run and found no tolerated
    off-target sites; approaches 0 as tolerated sites accumulate. This is the standard CFD
    aggregate: 1 / (1 + sum of per-site penalties). Only call this with a real (possibly
    empty) enumerated list — an empty list here means "searched, found nothing," which is
    different from specificity()'s `offtargets=None` ("never searched")."""
    if not offtargets:
        return 1.0
    total_penalty = sum(_site_cfd_penalty(s) for s in offtargets)
    return 1.0 / (1.0 + total_penalty)


def specificity(
    offtargets: Optional[Sequence[OffTargetSite]] = None,
    external_score: Optional[float] = None,
) -> Optional[float]:
    """Specificity in [0, 1] (1 = highly specific / low off-target risk), or None when truly
    unassessed. Prefers a pluggable external off-target model — crispAI
    (agent1_literature_search/output/related/ozden2024_crispai_uncertainty/) or CrisprBERT
    (agent1_literature_search/output/related/sari2025_crisprbert/), both trained on the same
    primary-T-cell CHANGE-seq data Ito et al.'s cohort comes from, recommended here because
    Ito et al. report no off-target data of their own. Falls back to CFD aggregation over an
    enumerated off-target site list when `offtargets` is given (including an empty list —
    that's real evidence, see cfd_specificity). Returns None — not 1.0 — when NEITHER an
    external score NOR an off-target list was supplied, i.e. specificity was never actually
    assessed for this guide; score_guide() excludes None components rather than treating
    "never checked" as "confirmed safe"."""
    if external_score is not None:
        return max(0.0, min(1.0, external_score))
    if offtargets is not None:
        return cfd_specificity(offtargets)
    return None


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
    `combined` field."""
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
    delivery: Optional[Delivery] = None  # "rnp" | "lentiviral" | "vector" | "stable" | None


@dataclass
class GuideScoreResult:
    sequence_efficacy: float
    accessibility: Optional[float]
    specificity: Optional[float]
    combined: float
    recommended_score: float
    passes_ito_rule: bool


def score_guide(inputs: GuideScoreInputs, weights: GuideScoreWeights = GuideScoreWeights()) -> GuideScoreResult:
    """Compute the CellGuide score for one guide in one cell context.

    `combined`: the original transparent linear blend, kept for inspectability — weights
    are renormalized over whichever of (sequence, accessibility, specificity) actually have
    data for this guide, instead of guessing a value for a component nobody assessed.

    `recommended_score`: what to actually rank by. Real-data validation (n=199 Ito et al.
    guides) showed the linear blend underperforms sequence_efficacy alone (rho=0.315 vs
    0.441) — Ito et al.'s own method never linearly blends ATAC in; they gate on it. So
    recommended_score IS sequence_efficacy; check passes_ito_rule alongside it as the
    accessibility gate, rather than folding accessibility into the score continuously.
    """
    seq_eff = sequence_efficacy(inputs.spacer, inputs.deepspcas9_score, inputs.chopchop_score, inputs.delivery)
    acc = accessibility_score(inputs.atac_signal, inputs.delivery)
    spec = specificity(inputs.offtargets, inputs.external_specificity_score)

    components = [(weights.w_seq, seq_eff)]
    if acc is not None:
        components.append((weights.w_atac, acc))
    if spec is not None:
        components.append((weights.w_spec, spec))
    total_weight = sum(w for w, _ in components)
    combined = sum(w * v for w, v in components) / total_weight if total_weight else seq_eff

    return GuideScoreResult(
        sequence_efficacy=seq_eff,
        accessibility=acc,
        specificity=spec,
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
