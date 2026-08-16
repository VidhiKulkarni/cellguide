"""
Real genomic sequence retrieval + candidate guide RNA enumeration (CellGuide AI pipeline).

Fills the gap flagged in SPEC.md and README.md: guide_scoring.azimuth_score() needs a real
30-mer genomic context ([4nt upstream][20nt spacer][NGG PAM][3nt downstream]), and this
module is how you actually get one — for a gene not in Ito et al.'s 199-guide dataset, look
up its real genomic coordinates and sequence via the Ensembl REST API (free, no auth, no
local genome download), then scan for real NGG PAM sites on both strands.

No fabrication: every candidate guide returned here corresponds to a real PAM site found in
real sequence at a real genomic coordinate, stamped with the genome build it came from
(SPEC.md hard-gate precedent: "genome build stamped on every coordinate").

Usage:
    from genome_lookup import lookup_gene, fetch_sequence, find_candidate_guides

    gene = lookup_gene("BCL11A")
    seq = fetch_sequence(gene["chromosome"], gene["start"], gene["start"] + 2000)
    candidates = find_candidate_guides(seq, chromosome=gene["chromosome"], region_start=gene["start"])
"""

from dataclasses import dataclass
from typing import Optional

import requests

ENSEMBL_REST = "https://rest.ensembl.org"
_TIMEOUT = 30
_COMPLEMENT = str.maketrans("ACGTacgt", "TGCAtgca")


@dataclass
class GeneInfo:
    symbol: str
    ensembl_id: str
    chromosome: str
    start: int
    end: int
    strand: int  # 1 or -1, as reported by Ensembl — the gene's own strand, NOT which
    # strand a candidate guide is on (find_candidate_guides scans both regardless)
    assembly: str  # e.g. "GRCh38" — stamp this on every downstream coordinate


@dataclass
class CandidateGuide:
    spacer: str  # 20nt
    context_30mer: str  # for guide_scoring.azimuth_score()
    chromosome: str
    pam_start: int  # genomic coordinate of the first PAM base
    strand: str  # "+" or "-" — which strand this candidate guide is on
    assembly: str


def lookup_gene(symbol: str, species: str = "homo_sapiens") -> Optional[GeneInfo]:
    """Real gene lookup via Ensembl REST — returns None (not a guess) if the symbol isn't
    found, rather than raising or fabricating coordinates."""
    try:
        r = requests.get(
            f"{ENSEMBL_REST}/lookup/symbol/{species}/{symbol}",
            headers={"Content-Type": "application/json"},
            timeout=_TIMEOUT,
        )
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
    except requests.RequestException:
        return None

    return GeneInfo(
        symbol=data.get("display_name", symbol),
        ensembl_id=data["id"],
        chromosome=data["seq_region_name"],
        start=data["start"],
        end=data["end"],
        strand=data["strand"],
        assembly=data.get("assembly_name", "unknown"),
    )


def fetch_sequence(chromosome: str, start: int, end: int, species: str = "homo_sapiens") -> Optional[str]:
    """Real sequence for a genomic region (1-based, inclusive, Ensembl convention), always
    on the + strand as Ensembl returns it — find_candidate_guides scans both strands from
    this single + strand sequence via reverse-complementation, so this is sufficient
    regardless of the gene's own strand. Returns None (not a guess) on any failure."""
    try:
        r = requests.get(
            f"{ENSEMBL_REST}/sequence/region/{species}/{chromosome}:{start}-{end}",
            headers={"Content-Type": "application/json"},
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["seq"]
    except (requests.RequestException, KeyError):
        return None


def _reverse_complement(seq: str) -> str:
    return seq.translate(_COMPLEMENT)[::-1]


def _scan_strand(seq: str, chromosome: str, region_start: int, strand: str, assembly: str) -> list[CandidateGuide]:
    """Find every NGG PAM in `seq` (already the correct strand's sequence) with enough
    flanking sequence for a full 30-mer, and enough for the 20nt spacer before the PAM."""
    out = []
    for i in range(24, len(seq) - 6):
        # candidate PAM at seq[i:i+3]: needs to match NGG (positions i+1, i+2 == 'G')
        if seq[i + 1 : i + 3].upper() != "GG":
            continue
        context_30mer = seq[i - 24 : i + 6]
        spacer = seq[i - 20 : i]
        if len(context_30mer) != 30 or len(spacer) != 20:
            continue  # too close to the edge of the fetched window

        if strand == "+":
            genomic_pam_start = region_start + i
        else:
            # seq here is the reverse complement of the + strand region; map index i back
            # to a + strand coordinate for reporting.
            genomic_pam_start = region_start + (len(seq) - 1 - i) - 2

        out.append(
            CandidateGuide(
                spacer=spacer,
                context_30mer=context_30mer,
                chromosome=chromosome,
                pam_start=genomic_pam_start,
                strand=strand,
                assembly=assembly,
            )
        )
    return out


def find_candidate_guides(
    seq: str, chromosome: str, region_start: int, assembly: str = "GRCh38"
) -> list[CandidateGuide]:
    """Scan real sequence for real NGG PAM sites on both strands. `seq` must be the + strand
    sequence as returned by fetch_sequence(); `region_start` is that fetch's `start` argument
    (needed to report real genomic coordinates on each candidate, not just an offset into the
    fetched window)."""
    forward = _scan_strand(seq, chromosome, region_start, "+", assembly)
    reverse = _scan_strand(_reverse_complement(seq), chromosome, region_start, "-", assembly)
    return forward + reverse
