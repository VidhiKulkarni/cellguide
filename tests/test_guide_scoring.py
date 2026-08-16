"""Tests for agent3_metric_construction/guide_scoring.py — the core scoring library.

Covers the real bugs found and fixed during this project's critique cycles (see SPEC.md):
missing-data handling (None, not a guessed default), delivery gating, renormalization, and
the tier-preference order in sequence_efficacy_with_source(). Azimuth-dependent tests are
skipped when the isolated conda env isn't set up on this machine (see README.md) rather than
failing — that's an optional capability, not a hard requirement of this module.
"""

import pytest
from guide_scoring import (
    GuideScoreInputs,
    GuideScoreWeights,
    SOURCE_AZIMUTH,
    SOURCE_GC_MOTIF_HEURISTIC,
    SOURCE_REAL_TOOLS,
    accessibility_score,
    azimuth_available,
    gc_content,
    gc_content_score,
    passes_ito_thresholds,
    poly_t_penalty,
    score_guide,
    sequence_efficacy_with_source,
)

SPACER = "GACCTGAAGCTGAGCGAGTG"  # 20nt, arbitrary real-looking spacer


# ---------------------------------------------------------------------------
# gc_content / gc_content_score
# ---------------------------------------------------------------------------

def test_gc_content_all_gc():
    assert gc_content("GCGCGCGCGC") == 1.0


def test_gc_content_all_at():
    assert gc_content("ATATATATAT") == 0.0


def test_gc_content_score_peaks_at_50_percent():
    half_gc = "GCGCATATGCGCATAT"  # 8/16 = 50%
    assert gc_content_score(half_gc) == pytest.approx(1.0)


def test_gc_content_score_decays_away_from_50_percent():
    assert gc_content_score("GCGCGCGCGC") < gc_content_score("GCGCATATGCGCATAT")


# ---------------------------------------------------------------------------
# poly_t_penalty — delivery gating (this was bug #5 in SPEC.md's fix history)
# ---------------------------------------------------------------------------

def test_poly_t_penalty_not_applied_for_rnp():
    """Ito et al.'s guides are chemically synthesized RNP — no U6 promoter, so TTTT+
    shouldn't be penalized even if present."""
    spacer_with_ttttt = "GACCTGAATTTTAGCGAGTG"
    assert poly_t_penalty(spacer_with_ttttt, delivery="rnp") == 1.0
    assert poly_t_penalty(spacer_with_ttttt, delivery=None) == 1.0


def test_poly_t_penalty_applied_for_vector_delivery():
    spacer_with_tttt = "GACCTGAATTTTAGCGAGTG"
    assert poly_t_penalty(spacer_with_tttt, delivery="vector") == 0.0
    assert poly_t_penalty(spacer_with_tttt, delivery="lentiviral") == 0.0
    assert poly_t_penalty(spacer_with_tttt, delivery="stable") == 0.0


def test_poly_t_penalty_neutral_without_tttt():
    assert poly_t_penalty(SPACER, delivery="vector") == 1.0


# ---------------------------------------------------------------------------
# accessibility_score — None handling (bug #1/#2 fix history) + delivery gate
# ---------------------------------------------------------------------------

def test_accessibility_none_when_no_atac_signal():
    assert accessibility_score(None) is None


def test_accessibility_none_when_vector_delivery_even_with_signal():
    """Wang et al. 2019 vs Ito et al. 2024 contradiction — accessibility only validated for
    RNP, so it must not silently apply to lentiviral/vector contexts even if ATAC data exists."""
    assert accessibility_score(0.5, delivery="lentiviral") is None
    assert accessibility_score(0.5, delivery="vector") is None
    assert accessibility_score(0.5, delivery="stable") is None


def test_accessibility_saturates_at_threshold():
    assert accessibility_score(0.1, delivery="rnp") == pytest.approx(1.0)
    assert accessibility_score(1.0, delivery="rnp") == pytest.approx(1.0)  # saturates, doesn't exceed 1.0


def test_accessibility_scales_below_threshold():
    assert accessibility_score(0.05, delivery="rnp") == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# passes_ito_thresholds
# ---------------------------------------------------------------------------

def test_passes_ito_thresholds_all_pass():
    assert passes_ito_thresholds(deepspcas9=60, chopchop=0.3, atac_signal=0.1) is True


def test_passes_ito_thresholds_fails_below_any_threshold():
    assert passes_ito_thresholds(deepspcas9=59.9, chopchop=0.3, atac_signal=0.1) is False
    assert passes_ito_thresholds(deepspcas9=60, chopchop=0.29, atac_signal=0.1) is False
    assert passes_ito_thresholds(deepspcas9=60, chopchop=0.3, atac_signal=0.099) is False


def test_passes_ito_thresholds_false_not_guessed_when_missing():
    """Bug fix history: missing data must return False, not silently assume pass/fail."""
    assert passes_ito_thresholds(deepspcas9=None, chopchop=0.3, atac_signal=0.1) is False
    assert passes_ito_thresholds() is False


# ---------------------------------------------------------------------------
# sequence_efficacy_with_source — tier preference order + honest source labeling
# ---------------------------------------------------------------------------

def test_prefers_real_tools_over_everything():
    value, source = sequence_efficacy_with_source(SPACER, deepspcas9_score=80.0, chopchop_score=0.6)
    assert value == pytest.approx((0.8 + 0.6) / 2)
    assert source == SOURCE_REAL_TOOLS


def test_falls_back_to_gc_motif_heuristic_with_no_data_and_no_context():
    """No real tool scores, no precomputed Azimuth score, and no 30-mer context given at
    all — azimuth_score() is never even reached (it needs context_30mer), regardless of
    whether the conda env happens to be installed on this machine."""
    value, source = sequence_efficacy_with_source(SPACER)
    assert source == SOURCE_GC_MOTIF_HEURISTIC
    assert 0.0 <= value <= 1.0


def test_precomputed_azimuth_score_used_directly_without_subprocess():
    """The batch-scoring path (score_new_gene.py): a precomputed Azimuth score should be
    used and labeled correctly without triggering another subprocess call."""
    value, source = sequence_efficacy_with_source(SPACER, precomputed_azimuth_score=0.73)
    assert value == pytest.approx(0.73)
    assert source == SOURCE_AZIMUTH


def test_real_tools_take_priority_even_with_precomputed_azimuth_score():
    value, source = sequence_efficacy_with_source(
        SPACER, deepspcas9_score=80.0, chopchop_score=0.6, precomputed_azimuth_score=0.1
    )
    assert source == SOURCE_REAL_TOOLS
    assert value == pytest.approx((0.8 + 0.6) / 2)


@pytest.mark.skipif(not azimuth_available(), reason="azimuth conda env not set up on this machine")
def test_azimuth_called_when_context_30mer_given_and_no_real_tools():
    context_30mer = "ACAGCTGATCTCCAGATATGACCATGGGTT"  # known-good 30mer from Azimuth's own README example
    value, source = sequence_efficacy_with_source(SPACER, context_30mer=context_30mer)
    assert source == SOURCE_AZIMUTH
    assert 0.0 <= value <= 1.0


# ---------------------------------------------------------------------------
# score_guide — renormalization + combined vs recommended_score
# ---------------------------------------------------------------------------

def test_score_guide_recommended_score_is_sequence_efficacy_only():
    """Real-data finding: recommended_score should NOT include accessibility (SPEC.md —
    the blended score underperformed sequence-only on real data)."""
    result = score_guide(GuideScoreInputs(spacer=SPACER, deepspcas9_score=80.0, chopchop_score=0.6, atac_signal=0.5, delivery="rnp"))
    assert result.recommended_score == result.sequence_efficacy


def test_score_guide_combined_equals_recommended_when_accessibility_missing():
    """Renormalization: with only one component available, combined must equal that
    component exactly, not some diluted/guessed value."""
    result = score_guide(GuideScoreInputs(spacer=SPACER, deepspcas9_score=80.0, chopchop_score=0.6))
    assert result.accessibility is None
    assert result.combined == pytest.approx(result.sequence_efficacy)


def test_score_guide_combined_is_weighted_average_when_both_available():
    weights = GuideScoreWeights(w_seq=0.4, w_atac=0.3)
    result = score_guide(
        GuideScoreInputs(spacer=SPACER, deepspcas9_score=100.0, chopchop_score=1.0, atac_signal=1.0, delivery="rnp"),
        weights,
    )
    # seq_eff = 1.0, acc = 1.0 (saturated) -> combined should be 1.0 regardless of weights
    assert result.combined == pytest.approx(1.0)


def test_score_guide_has_no_specificity_field():
    """specificity was removed entirely from the scoring library (SPEC.md) — assert it
    doesn't silently reappear."""
    result = score_guide(GuideScoreInputs(spacer=SPACER))
    assert not hasattr(result, "specificity")


def test_score_guide_sources_are_always_populated():
    """Every result must be traceable to a real data source or an honest explanation of
    why a component is missing — never a bare, unexplained value."""
    result = score_guide(GuideScoreInputs(spacer=SPACER))
    assert result.sequence_efficacy_source  # non-empty string
    assert result.accessibility_source  # non-empty string, even though accessibility is None
