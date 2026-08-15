#!/usr/bin/env python3
"""
Agent 4 correction — test Ito et al.'s ACTUAL accessibility claim.

Agent 5's review (agent5_confidence_assessment/output/CONFIDENCE_REPORT.md, finding B) caught
a real methodological error in the original REPORT.md: it tested the MARGINAL correlation
between ATAC and indel% across all guides (rho=0.084, n.s.) and concluded accessibility "has
not demonstrated predictive value." But Ito et al. never claimed a marginal effect. Their
actual claim (fulltext L64): "the ATAC-seq score alone did not show a significant correlation
with the efficiency of indel generation. However, high ATAC-seq scores were significantly
associated with efficient indel formation among gRNAs with above-median scores in CHOPCHOP
(Doench 2014) or DeepSpCas9." That's a CONDITIONAL/interaction claim, tested here properly by
subsetting to above-median sequence-score guides before checking the ATAC correlation.

Usage:
    uv run agent4_benchmarking/interaction_effect_check.py
"""

import sys
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "papers" / "ito_2024" / "table_s1_for_agent4.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    df = pd.read_csv(DATA_PATH)

    median_chop = df["chopchop_score"].median()
    median_deep = df["deepspcas9_score"].median()
    above_median = (df["chopchop_score"] >= median_chop) | (df["deepspcas9_score"] >= median_deep)

    marginal_rho, marginal_p = spearmanr(df["atac_signal"], df["indel_pct"])
    above = df[above_median]
    above_rho, above_p = spearmanr(above["atac_signal"], above["indel_pct"])
    below = df[~above_median]
    below_rho, below_p = spearmanr(below["atac_signal"], below["indel_pct"])

    report = [
        "# Agent 4 — testing Ito et al.'s actual (conditional) accessibility claim",
        "",
        f"n = {len(df)}; median CHOPCHOP (chop2014) = {median_chop:.3f}, median DeepSpCas9 = {median_deep:.2f}",
        "",
        "| Test | n | Spearman ρ | p-value |",
        "|---|---|---|---|",
        f"| Marginal (all guides) — what REPORT.md originally tested | {len(df)} | {marginal_rho:.3f} | {marginal_p:.3g} |",
        f"| **Conditional: above-median CHOPCHOP or DeepSpCas9 — Ito's actual claim** | {len(above)} | **{above_rho:.3f}** | **{above_p:.3g}** |",
        f"| Below-median CHOPCHOP and DeepSpCas9 (should not show the effect, per Ito) | {len(below)} | {below_rho:.3f} | {below_p:.3g} |",
        "",
    ]

    if above_p < 0.05 and above_rho > 0:
        report.append(
            f"**This reproduces Ito et al.'s claim.** Tested correctly (conditional on sequence "
            f"score, not marginal), accessibility DOES have a real, statistically significant "
            f"positive association with editing efficiency (ρ={above_rho:.3f}, p={above_p:.3g}). "
            "The original REPORT.md's marginal test was the wrong statistic for this claim — "
            "the earlier 'accessibility has no value' conclusion does not hold; it was never "
            "properly tested. `recommended_score` (sequence-only) is still a reasonable default "
            "ranking value on its own, but the honest conclusion is 'accessibility adds "
            "conditional information not yet folded into a score,' not 'accessibility failed.'"
        )
    else:
        report.append(
            "This does NOT clearly reproduce Ito et al.'s claim on this data — treat the "
            "'accessibility has not demonstrated value' conclusion as still standing pending "
            "further checks."
        )

    if below_p < 0.05:
        report.append(
            f"\n**Caveat worth flagging, not overselling**: the below-median subset (n={len(below)}) "
            f"shows its own significant correlation (ρ={below_rho:.3f}, p={below_p:.3g}), which Ito's "
            "paper doesn't predict or address — worth treating as an open question rather than "
            "further evidence either way, since it wasn't a pre-registered hypothesis and the "
            "subset is smaller."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "INTERACTION_EFFECT_CHECK.md"
    out_path.write_text("\n".join(report) + "\n")
    print("\n".join(report))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
