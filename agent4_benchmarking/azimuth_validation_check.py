#!/usr/bin/env python3
"""
Agent 4 follow-up — validate the Azimuth (tier 2) scoring path specifically, in-context.

REPORT.md's headline number (sequence_efficacy rho=0.441, p=7e-11) comes entirely from
DeepSpCas9/CHOPCHOP (Ito et al.'s own precomputed tools) -- that number says nothing about
Azimuth, which is a DIFFERENT model used as the fallback for guides/genes that don't have
DeepSpCas9/CHOPCHOP scores (i.e. anything outside Ito's own 199-guide dataset -- see
guide_scoring.SOURCE_AZIMUTH's own docstring: "not independently re-validated in this
pipeline"). Conflating the two would be exactly the kind of unearned credibility this
project has been trying to avoid.

This script closes that gap using data we already have: Ito et al.'s 199 guides come with
real measured indel% AND a gene symbol + 20nt spacer, but no genomic coordinates or 30-mer
context. So for each guide:
  1. look up its gene's real coordinates (genome_lookup.lookup_gene)
  2. fetch the real genomic sequence spanning the gene (+/- 200bp padding)
  3. scan both strands for real NGG PAM sites (genome_lookup.find_candidate_guides)
  4. find the candidate whose spacer exactly matches Ito's reported spacer -- that candidate's
     context_30mer IS this guide's real genomic context, reconstructed from real sequence,
     not guessed or padded
  5. run Azimuth on that real context, and only THEN check it against the real indel%

Guides whose gene isn't found, whose sequence fetch fails, or whose spacer can't be matched
within the fetched window are excluded and reported by exact reason -- not silently dropped,
not guessed.

Usage:
    uv run agent4_benchmarking/azimuth_validation_check.py [--limit N]
"""

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "papers" / "ito_2024" / "table_s1_for_agent4.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

sys.path.insert(0, str(REPO_ROOT / "agent3_metric_construction"))
from genome_lookup import find_candidate_guides, fetch_sequence, lookup_gene  # noqa: E402
from guide_scoring import azimuth_available, azimuth_score_batch  # noqa: E402

PADDING = 200


def reconstruct_contexts(df: pd.DataFrame) -> tuple[dict[tuple, str], dict[str, str]]:
    """Returns (spacer_context_by_row_key, failure_reason_by_gene) -- one Ensembl round-trip
    per unique gene, not per guide, since several guides share a gene."""
    contexts: dict[tuple, str] = {}
    gene_failures: dict[str, str] = {}

    genes = sorted(df["gene"].unique())
    for n, gene in enumerate(genes, 1):
        print(f"  [{n}/{len(genes)}] {gene}...", end=" ", flush=True)
        info = lookup_gene(gene)
        if info is None:
            gene_failures[gene] = "GENE_NOT_FOUND (Ensembl lookup failed)"
            print("gene not found")
            continue

        region_start = max(1, info.start - PADDING)
        region_end = info.end + PADDING
        seq = fetch_sequence(info.chromosome, region_start, region_end)
        if seq is None:
            gene_failures[gene] = f"SEQUENCE_FETCH_FAILED ({info.chromosome}:{region_start}-{region_end})"
            print("sequence fetch failed")
            continue

        candidates = find_candidate_guides(seq, chromosome=info.chromosome, region_start=region_start, assembly=info.assembly)
        by_spacer = {}
        for c in candidates:
            by_spacer.setdefault(c.spacer.upper(), c.context_30mer)

        matched = 0
        for spacer in df.loc[df["gene"] == gene, "spacer"]:
            ctx = by_spacer.get(spacer.upper())
            if ctx is not None:
                contexts[(gene, spacer)] = ctx
                matched += 1
        print(f"{matched}/{(df['gene'] == gene).sum()} spacers matched ({len(candidates)} candidates in window)")
        time.sleep(0.1)  # be polite to Ensembl's REST API across ~100+ sequential lookups

    return contexts, gene_failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Azimuth (tier 2) in-context against Ito et al.'s real indel% data")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N guides (for a quick smoke test)")
    args = parser.parse_args()

    df = pd.read_csv(DATA_PATH)
    if args.limit:
        df = df.head(args.limit)

    if not azimuth_available():
        print("Azimuth conda env not set up on this machine (~/miniforge3/envs/azimuth missing) -- cannot run this check.")
        sys.exit(1)

    print(f"Reconstructing real genomic 30-mer context for {len(df)} guides across {df['gene'].nunique()} genes...")
    contexts, gene_failures = reconstruct_contexts(df)

    df["context_30mer"] = df.apply(lambda r: contexts.get((r["gene"], r["spacer"])), axis=1)
    scored = df[df["context_30mer"].notna()].copy()
    unscored = df[df["context_30mer"].isna()].copy()

    print(f"\nReconstructed real context for {len(scored)}/{len(df)} guides. Running Azimuth (batched)...")
    scored["azimuth_score"] = azimuth_score_batch(list(scored["context_30mer"]))
    failed_azimuth = scored[scored["azimuth_score"].isna()]
    scored = scored.dropna(subset=["azimuth_score"])

    rho, p = (float("nan"), float("nan"))
    if len(scored) >= 3:
        rho, p = spearmanr(scored["azimuth_score"], scored["indel_pct"])

    # Also compute what DeepSpCas9/CHOPCHOP get on this SAME subset, so the comparison is
    # apples-to-apples (not the full-199-guide number from REPORT.md).
    seq_eff_same_subset = (scored["deepspcas9_score"] / 100.0 + scored["chopchop_score"]) / 2
    rho_seq, p_seq = spearmanr(seq_eff_same_subset, scored["indel_pct"]) if len(scored) >= 3 else (float("nan"), float("nan"))

    lines = [
        "# Agent 4 — Azimuth (tier 2) in-context validation",
        "",
        "REPORT.md's rho=0.441 validates DeepSpCas9/CHOPCHOP (tier 1), not Azimuth (tier 2) --",
        "these are different models. This check reconstructs each Ito et al. guide's real",
        "genomic 30-mer context (gene lookup -> real sequence -> real PAM scan -> spacer match,",
        "no fabrication/padding) and runs Azimuth on it directly, to get an honest in-context",
        "number for the path that actually gets used to score genes outside Ito's dataset.",
        "",
        f"- Guides in Ito et al.'s table: {len(df)} (across {df['gene'].nunique()} genes)",
        f"- Genes with a failed Ensembl lookup or sequence fetch: {len(gene_failures)}",
        f"- Guides with real context successfully reconstructed: {len(df) - len(unscored)}/{len(df)}",
        f"- Guides Azimuth itself failed to score (bad context, subprocess error): {len(failed_azimuth)}",
        f"- **Final n scored by Azimuth and compared to real indel%: {len(scored)}**",
        "",
        "| Score | n | Spearman ρ vs real indel% | p-value |",
        "|---|---|---|---|",
        f"| **Azimuth (tier 2, this check)** | {len(scored)} | **{rho:.3f}** | **{p:.3g}** |",
        f"| DeepSpCas9/CHOPCHOP (tier 1), same {len(scored)}-guide subset | {len(scored)} | {rho_seq:.3f} | {p_seq:.3g} |",
        f"| DeepSpCas9/CHOPCHOP (tier 1), full REPORT.md number for reference | 199 | 0.441 | 7.01e-11 |",
        "",
    ]

    if gene_failures:
        lines.append(f"### Genes excluded ({len(gene_failures)})")
        lines.append("")
        for gene, reason in gene_failures.items():
            lines.append(f"- **{gene}**: {reason}")
        lines.append("")

    unmatched_but_gene_ok = unscored[~unscored["gene"].isin(gene_failures)]
    if len(unmatched_but_gene_ok):
        lines.append(f"### Guides excluded — gene found, but spacer not matched to any real PAM site in the fetched window ({len(unmatched_but_gene_ok)})")
        lines.append("")
        lines.append("Possible reasons: guide targets a splice site or region outside the padded gene span, ")
        lines.append("assembly/annotation mismatch, or Ito et al. used a different reference build.")
        lines.append("")
        for _, r in unmatched_but_gene_ok.iterrows():
            lines.append(f"- {r['gene']} / `{r['spacer']}`")
        lines.append("")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "AZIMUTH_VALIDATION_CHECK.md"
    out_path.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
