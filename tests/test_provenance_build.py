"""Tests for agent7_provenance/build.py's SPEC.md parsing (extract_slugs, parse_component_sources).

Runs against the real agent3_metric_construction/SPEC.md and the real papers/ directory in
this repo rather than a fixture — this module's whole job is staying in sync with those real
files (see its own docstring: "so this can't silently drift from SPEC.md"), so testing against
a synthetic stand-in wouldn't actually verify that.
"""

from build import extract_slugs, parse_component_sources


def test_extract_slugs_finds_known_papers_in_order():
    text = "Backed by ito_2024's empirical rule; see also wang_2019_deephf for the GC/Tm model."
    assert extract_slugs(text) == ["ito_2024", "wang_2019_deephf"]


def test_extract_slugs_dedupes():
    text = "ito_2024 ... ito_2024 again"
    assert extract_slugs(text) == ["ito_2024"]


def test_extract_slugs_ignores_unknown_tokens():
    text = "some_unrelated_token that is not a real paper slug"
    assert extract_slugs(text) == []


def test_parse_component_sources_has_no_specificity():
    """specificity() was removed from guide_scoring.py and SPEC.md entirely -- this must not
    silently reappear as a parsed component."""
    components = parse_component_sources()
    assert "specificity" not in components


def test_parse_component_sources_finds_both_real_components():
    components = parse_component_sources()
    assert set(components.keys()) == {"sequence_efficacy", "accessibility"}


def test_parse_component_sources_does_not_swallow_trailing_sections():
    """Regression test for the original bug: splitting only on '## Component N — ' headers
    let the LAST component section run to end-of-file, swallowing '## Default weights',
    '## passes_ito_thresholds(...)', and '## Known limitations' into accessibility's
    spec_text. Fixed by splitting on every '## ' heading instead."""
    components = parse_component_sources()
    accessibility_text = components["accessibility"]["spec_text"]
    assert "Known limitations" not in accessibility_text
    assert "Default weights" not in accessibility_text


def test_parse_component_sources_cites_real_papers():
    components = parse_component_sources()
    # accessibility's key caveat (delivery-context-dependence) comes from wang_2019_deephf
    assert "wang_2019_deephf" in components["accessibility"]["cited_papers"]
