#!/usr/bin/env python3
"""
Agent 4 addendum — two follow-up checks on real data:

1. Does our own from-scratch sequence-motif heuristic (GC content + poly-T penalty,
   agent3_metric_construction.guide_scoring.sequence_motif_score) carry any real signal on
   its own? The main benchmark (run.py) never actually exercises this heuristic against real
   outcomes — every one of the 199 real guides has a DeepSpCas9/CHOPCHOP score available, so
   sequence_efficacy() always takes the "preferred external tool" branch and the motif
   fallback is untested. This forces the motif-only path and correlates it directly against
   real indel%.

2. Does averaging the two ATAC-seq replicates (papers/ito_2024/table_s1_205_gRNAs.csv has
   both GSM6896554 and GSM7256892 for every guide) produce a more stable/predictive
   accessibility signal than using either replicate alone? See
   agent4_benchmarking/replicate_sensitivity_check.py for how badly the two disagree
   individually.

Usage:
    uv run agent4_benchmarking/motif_and_accessibility_checks.py
"""

import sys
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent3_metric_construction"))
from guide_scoring import GuideScoreInputs, accessibility_score, passes_ito_thresholds, sequence_motif_score, score_guide, GuideScoreWeights  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
FULL_TABLE = REPO_ROOT / "papers" / "ito_2024" / "table_s1_205_gRNAs.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def load_clean() -> pd.DataFrame:
    full = pd.read_csv(FULL_TABLE)
    df = pd.DataFrame(
        {
            "gene": full["gene_name"],
            "spacer": full["target_sequence"],
            "atac_1": full["atac_seq_GSM6896554"],
            "atac_2": full["atac_seq_GSM7256892"],
            "chopchop_score": full["chop2014"],
            "deepspcas9_score": full["deepspcas9"],
            "indel_pct": full["indel_avg"],
        }
    ).replace("-", pd.NA)
    for col in ["atac_1", "atac_2", "chopchop_score", "deepspcas9_score", "indel_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna()


def check_motif_only(df: pd.DataFrame) -> str:
    """sequence_motif_score() forced on every guide, ignoring DeepSpCas9/CHOPCHOP even
    though they're available, to see if the from-scratch heuristic has any signal at all."""
    scores = [sequence_motif_score(s, delivery="rnp") for s in df["spacer"]]
    rho, pval = spearmanr(scores, df["indel_pct"])
    lines = [
        "## Does our own motif heuristic (GC + poly-T) predict real indel%?\n",
        f"Forced sequence_motif_score() (ignoring DeepSpCas9/CHOPCHOP) on all {len(df)} real "
        f"guides: Spearman ρ={rho:.3f}, p={pval:.3g} vs. sequence_efficacy's ρ=0.441 when "
        "using DeepSpCas9/CHOPCHOP as designed.",
    ]
    if pval < 0.05 and rho > 0.1:
        lines.append("Real, if weak, signal — the heuristic is doing more than nothing.")
    else:
        lines.append(
            "No meaningful signal on its own. The two external tools (DeepSpCas9, CHOPCHOP) "
            "are carrying essentially all of sequence_efficacy's real predictive power; our "
            "own GC/poly-T heuristic is a reasonable-looking fallback for when no external "
            "score is available, not a validated predictor in its own right."
        )
    return "\n".join(lines)


def check_averaged_atac(df: pd.DataFrame) -> str:
    """Average the two ATAC replicates and see if the noise partially cancels out, compared
    to either replicate alone (see replicate_sensitivity_check.py for the individual
    numbers: rho=0.084/p=0.239 for GSM6896554, rho=0.019/p=0.792 for GSM7256892)."""
    df = df.copy()
    df["atac_avg"] = df[["atac_1", "atac_2"]].mean(axis=1)

    weights = GuideScoreWeights()
    acc_scores, gate_passes = [], []
    for row in df.itertuples():
        acc_scores.append(accessibility_score(row.atac_avg, delivery="rnp"))
        gate_passes.append(passes_ito_thresholds(row.deepspcas9_score, row.chopchop_score, row.atac_avg))

    rho, pval = spearmanr(acc_scores, df["indel_pct"])
    actual = df["indel_pct"] > 50
    predicted = pd.Series(gate_passes, index=df.index)
    tp = int((predicted & actual).sum()); fp = int((predicted & ~actual).sum()); fn = int((~predicted & actual).sum())
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")

    lines = [
        "## Does averaging both ATAC replicates give a more stable accessibility signal?\n",
        "| Signal | accessibility ρ | p | gate precision | gate recall |",
        "|---|---|---|---|---|",
        "| GSM6896554 alone | 0.084 | 0.239 | 0.862 | 0.287 |",
        "| GSM7256892 alone | 0.019 | 0.792 | 1.000 | 0.138 |",
        f"| **Average of both** | **{rho:.3f}** | **{pval:.3g}** | **{precision:.3f}** | **{recall:.3f}** |",
        "",
    ]
    if pval < 0.05:
        lines.append(
            "Averaging recovers a statistically real (if still weak) accessibility signal — "
            "the individual replicates' disagreement was partly independent noise that partially "
            "cancels when combined. Worth using the average as the default `atac_signal` input "
            "instead of a single replicate."
        )
    else:
        lines.append(
            "Still not a statistically significant signal even averaged — the two replicates' "
            "disagreement is not just independent noise that cancels out; accessibility's "
            "predictive value for this benchmark remains unsupported."
        )
    return "\n".join(lines)


def main() -> None:
    df = load_clean()
    report = [
        "# Agent 4 — motif-heuristic and ATAC-averaging follow-up checks",
        "",
        f"n = {len(df)} real Ito et al. 2024 guides",
        "",
        check_motif_only(df),
        "",
        check_averaged_atac(df),
    ]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "MOTIF_AND_ACCESSIBILITY_CHECKS.md"
    out_path.write_text("\n".join(report) + "\n")
    print("\n".join(report))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
