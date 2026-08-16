"""Tests for agent3_metric_construction/genome_lookup.py — PAM scanning and coordinate math.

No network calls here: lookup_gene()/fetch_sequence() need the live Ensembl REST API and are
intentionally NOT covered by this file (there's nothing to unit-test in a thin HTTP wrapper
beyond "does the network work today"). This file covers _reverse_complement() and the PAM
scanning / genomic coordinate math in _scan_strand(), against hand-constructed, hand-verified
synthetic sequences — including the reverse-strand coordinate formula that was flagged as a
possible bug earlier in this project (a verification script reported a 3bp discrepancy) and,
after careful manual re-derivation, was confirmed correct; the worked example below is that
re-derivation turned into a concrete regression test.
"""

from genome_lookup import _reverse_complement, find_candidate_guides


# ---------------------------------------------------------------------------
# _reverse_complement
# ---------------------------------------------------------------------------

def test_reverse_complement_basic():
    assert _reverse_complement("ACGT") == "ACGT"  # palindromic
    assert _reverse_complement("AAAA") == "TTTT"
    assert _reverse_complement("GATTACA") == "TGTAATC"


def test_reverse_complement_lowercase():
    assert _reverse_complement("acgt") == "acgt"


# ---------------------------------------------------------------------------
# find_candidate_guides — forward strand
# ---------------------------------------------------------------------------
# seq = 24x'A' + 'CGG' + 23x'T'  (len 50) -> exactly one NGG PAM ('CGG') at 0-based index 24.
# No G at all elsewhere in seq or in its reverse complement, so this is a clean,
# single-candidate fixture on the '+' strand only.

FORWARD_SEQ = "A" * 24 + "CGG" + "T" * 23
REGION_START = 1000


def test_find_candidate_guides_forward_strand():
    candidates = find_candidate_guides(FORWARD_SEQ, chromosome="1", region_start=REGION_START, assembly="GRCh38")
    forward = [c for c in candidates if c.strand == "+"]
    reverse = [c for c in candidates if c.strand == "-"]

    assert len(forward) == 1
    assert reverse == []  # this fixture has no G at all on the reverse-complement strand

    c = forward[0]
    assert c.spacer == "A" * 20  # seq[4:24]
    assert c.context_30mer == "A" * 24 + "CGG" + "TTT"  # seq[0:30]
    assert c.chromosome == "1"
    assert c.assembly == "GRCh38"
    # + strand: genomic coordinate of seq[i] is simply region_start + i (1-based Ensembl offset)
    assert c.pam_start == REGION_START + 24


# ---------------------------------------------------------------------------
# find_candidate_guides — reverse strand (the coordinate math re-derived this session)
# ---------------------------------------------------------------------------
# seq chosen so it has ZERO 'G' bases at all (no forward-strand PAM possible), but its
# reverse complement contains exactly one clean NGG PAM ('TGG') at rc-index 24.
#
# Worked derivation (n = len(seq) = 50, PAM found at rc-index j = 24):
#   rc[j:j+3] = rc[24:27] = "TGG" maps back to + strand offsets {n-1-j, n-2-j, n-3-j}
#             = {25, 24, 23} -- i.e. the 3nt PAM footprint spans + strand offsets 23-25.
#   leftmost (reported) genomic offset = n - 3 - j = 50 - 3 - 24 = 23
#   pam_start = region_start + 23 = 1023
# ...which is exactly what the module's formula `region_start + (len(seq) - 1 - i) - 2`
# computes: 1000 + (50 - 1 - 24) - 2 = 1000 + 25 - 2 = 1023.

REVERSE_SEQ = "A" * 23 + "CCA" + "T" * 24  # reverse_complement of this is "A"*24 + "TGG" + "T"*23


def test_reverse_complement_of_fixture_has_expected_pam():
    assert _reverse_complement(REVERSE_SEQ) == "A" * 24 + "TGG" + "T" * 23


def test_find_candidate_guides_reverse_strand():
    candidates = find_candidate_guides(REVERSE_SEQ, chromosome="1", region_start=REGION_START, assembly="GRCh38")
    forward = [c for c in candidates if c.strand == "+"]
    reverse = [c for c in candidates if c.strand == "-"]

    assert forward == []  # no G bases in REVERSE_SEQ itself
    assert len(reverse) == 1

    c = reverse[0]
    assert c.spacer == "A" * 20  # rc[4:24]
    assert c.context_30mer == "A" * 24 + "TGG" + "TTT"  # rc[0:30]
    assert c.chromosome == "1"
    assert c.assembly == "GRCh38"
    assert c.pam_start == REGION_START + 23


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_find_candidate_guides_no_pam_sites():
    assert find_candidate_guides("A" * 100, chromosome="1", region_start=REGION_START) == []


def test_find_candidate_guides_sequence_too_short_for_any_full_context():
    """29nt gives range(24, 29-6) = range(24, 23), an empty range -- too short for even one
    candidate's full 30-mer context, so this must return no candidates, not raise or crash."""
    assert find_candidate_guides("A" * 29, chromosome="1", region_start=REGION_START) == []
