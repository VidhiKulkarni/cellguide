"""Tests for agent6_next_experiment/recommend.py's pure ranking logic (uncertainty()).

load_confidence()/load_tested()/cmd_recommend()/cmd_record() all do real file I/O against
this repo's own state (experiment_log.csv, agent5's confidence.json) and aren't covered here
— uncertainty() is the actual ranking math and is pure, so it's what's worth unit-testing.
"""

import pandas as pd
import pytest
from recommend import uncertainty


def test_uncertainty_uses_agent5_confidence_when_available():
    row = pd.Series({"gene": "GZMA", "cell_type": "T", "sequence_efficacy": 0.9, "accessibility": 0.9})
    confidence_by_gene = {("GZMA", "T"): 0.8}
    assert uncertainty(row, confidence_by_gene) == pytest.approx(0.2)  # 1.0 - 0.8


def test_uncertainty_falls_back_to_component_disagreement():
    row = pd.Series({"gene": "NOVEL", "cell_type": "T", "sequence_efficacy": 0.2, "accessibility": 0.8})
    result = uncertainty(row, confidence_by_gene={})
    # population stdev of [0.2, 0.8]
    assert result == pd.Series([0.2, 0.8]).std(ddof=0)


def test_uncertainty_neutral_prior_when_accessibility_missing():
    """Only one component available (no ATAC data) -- not enough signal to estimate
    disagreement, so this must return the neutral 0.5 prior, not guess or crash."""
    row = pd.Series({"gene": "NOVEL", "cell_type": "T", "sequence_efficacy": 0.7, "accessibility": None})
    assert uncertainty(row, confidence_by_gene={}) == 0.5


def test_uncertainty_agent5_confidence_takes_priority_over_components():
    row = pd.Series({"gene": "GZMA", "cell_type": "T", "sequence_efficacy": 0.1, "accessibility": 0.9})
    confidence_by_gene = {("GZMA", "T"): 0.5}
    assert uncertainty(row, confidence_by_gene) == 0.5  # 1.0 - 0.5, NOT the component stdev
