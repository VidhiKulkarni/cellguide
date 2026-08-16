#!/usr/bin/env python3
"""
Score candidate guides for a gene NOT in Ito et al. 2024's 199-guide benchmark dataset —
the end-to-end entry point that connects genome_lookup.py (real Ensembl sequence + PAM
scanning) to guide_scoring.py (real Azimuth model when available).

This is the "honest UI" entry point: every result — and every failure — is reported in
plain language with an explicit reason, not a silent None or a fabricated number. If you're
building a UI on top of this, `run()`'s return value (or this script's JSON output) is
exactly what should be shown to the user: what we found, what we used to score it, and what
we don't have.

Usage:
    uv run agent3_metric_construction/score_new_gene.py BCL11A
    uv run agent3_metric_construction/score_new_gene.py BCL11A --window 2000 --atac-signal 0.42 --cell-type "CD34+ HSPC"
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from genome_lookup import find_candidate_guides, fetch_sequence, lookup_gene  # noqa: E402
from guide_scoring import GuideScoreInputs, azimuth_available, azimuth_score_batch, score_guide  # noqa: E402


def run(
    gene_symbol: str,
    window: int = 2000,
    atac_signal: float | None = None,
    cell_type: str | None = None,
    top: int = 10,
) -> dict:
    """Returns a dict that is ALWAYS safe to show a user directly — every field either has
    real data or an explicit, specific explanation of why it doesn't."""
    report: dict = {"gene_requested": gene_symbol, "status": None, "messages": [], "guides": []}

    gene = lookup_gene(gene_symbol)
    if gene is None:
        report["status"] = "GENE_NOT_FOUND"
        report["messages"].append(
            f"Could not find {gene_symbol!r} via Ensembl. Check the gene symbol, or this "
            "gene/species combination may not be in Ensembl's database. No guides can be "
            "scored without real genomic coordinates."
        )
        return report

    report["gene"] = {
        "symbol": gene.symbol, "ensembl_id": gene.ensembl_id, "chromosome": gene.chromosome,
        "start": gene.start, "end": gene.end, "strand": gene.strand, "assembly": gene.assembly,
    }

    fetch_start = gene.start
    fetch_end = min(gene.start + window, gene.end)
    seq = fetch_sequence(gene.chromosome, fetch_start, fetch_end)
    if seq is None:
        report["status"] = "SEQUENCE_FETCH_FAILED"
        report["messages"].append(
            f"Found the gene ({gene.ensembl_id}, {gene.chromosome}:{fetch_start}-{fetch_end}, "
            f"{gene.assembly}) but the Ensembl sequence API request failed (network error or "
            "timeout). No guides can be scored without real sequence — try again, this is "
            "not a permanent gap."
        )
        return report

    report["sequence_window"] = {"chromosome": gene.chromosome, "start": fetch_start, "end": fetch_end, "length": len(seq)}

    candidates = find_candidate_guides(seq, chromosome=gene.chromosome, region_start=fetch_start, assembly=gene.assembly)
    if not candidates:
        report["status"] = "NO_PAM_SITES_FOUND"
        report["messages"].append(
            f"Fetched real sequence ({len(seq)}bp) but found zero NGG PAM sites — unusual for "
            f"a {len(seq)}bp window; try a larger --window."
        )
        return report

    if not azimuth_available():
        report["messages"].append(
            "NOTE: the Azimuth on-target model isn't set up on this machine "
            "(~/miniforge3/envs/azimuth missing — see agent3_metric_construction/README.md). "
            "Every candidate below will fall back to the GC/motif heuristic, which has NO "
            "proven predictive power (rho=0.043, n.s. — see "
            "agent4_benchmarking/output/MOTIF_AND_ACCESSIBILITY_CHECKS.md). Treat these scores "
            "as placeholders until Azimuth is set up."
        )

    if atac_signal is None:
        report["messages"].append(
            "NOTE: no --atac-signal given, so accessibility/passes_ito_rule can't be assessed "
            "for this cell type — sequence_efficacy alone is being used to rank."
        )

    # One batched subprocess call for every candidate's Azimuth score, instead of one
    # subprocess per guide (each `mamba run -n azimuth ...` has real startup overhead —
    # scoring a whole gene's worth of candidates one at a time is impractically slow).
    azimuth_scores = azimuth_score_batch([c.context_30mer for c in candidates])

    scored = []
    for c, az_score in zip(candidates, azimuth_scores):
        result = score_guide(GuideScoreInputs(
            spacer=c.spacer, precomputed_azimuth_score=az_score, atac_signal=atac_signal, delivery="rnp",
        ))
        scored.append({
            "spacer": c.spacer, "chromosome": c.chromosome, "pam_start": c.pam_start,
            "strand": c.strand, "assembly": c.assembly,
            "recommended_score": result.recommended_score,
            "sequence_efficacy_source": result.sequence_efficacy_source,
            "accessibility": result.accessibility,
            "accessibility_source": result.accessibility_source,
            "passes_ito_rule": result.passes_ito_rule,
            "cell_type": cell_type,
        })

    scored.sort(key=lambda r: r["recommended_score"], reverse=True)
    report["status"] = "OK"
    report["guides"] = scored[:top]
    report["messages"].append(f"Found {len(candidates)} candidate guides in the fetched window, showing top {min(top, len(candidates))}.")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Score candidate guides for a gene outside Ito et al.'s benchmark dataset")
    parser.add_argument("gene", help="Gene symbol, e.g. BCL11A")
    parser.add_argument("--window", type=int, default=2000, help="How many bp downstream of the gene start to fetch/scan")
    parser.add_argument("--atac-signal", type=float, default=None, help="Real measured ATAC-seq signal for this cell type, if you have it")
    parser.add_argument("--cell-type", default=None, help="Label for the cell type the ATAC signal (if given) is from")
    parser.add_argument("--top", type=int, default=10)
    args = parser.parse_args()

    report = run(args.gene, args.window, args.atac_signal, args.cell_type, args.top)
    print(json.dumps(report, indent=2))
    if report["status"] != "OK":
        sys.exit(1)


if __name__ == "__main__":
    main()
