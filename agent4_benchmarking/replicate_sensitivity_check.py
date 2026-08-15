#!/usr/bin/env python3
"""
Agent 4 addendum — ATAC replicate sensitivity check.

papers/ito_2024/table_s1_205_gRNAs.csv has TWO ATAC-seq replicate columns
(atac_seq_GSM6896554, atac_seq_GSM7256892) for the same 205 guides. The main benchmark
(run.py) uses only GSM6896554 without comment. This script runs the identical benchmark
against BOTH replicates and reports them side by side, because Agent 5's review
(agent5_confidence_assessment/output/CONFIDENCE_REPORT.md, finding 3) found the two
replicates disagree badly — 11/13 gate-passing guides under replicate 1 would FAIL the
ATAC>=0.1 gate under replicate 2 — meaning the accessibility gate's apparent value is
sensitive to an arbitrary choice of which sequencing run to use, not a stable signal.

Usage:
    uv run agent4_benchmarking/replicate_sensitivity_check.py
"""

import sys
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent3_metric_construction"))
from guide_scoring import GuideScoreInputs, GuideScoreWeights, passes_ito_thresholds, score_guide  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
FULL_TABLE = REPO_ROOT / "papers" / "ito_2024" / "table_s1_205_gRNAs.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

REPLICATES = {"GSM6896554 (used by run.py)": "atac_seq_GSM6896554", "GSM7256892": "atac_seq_GSM7256892"}


def build_dataset(full: pd.DataFrame, atac_col: str) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "gene": full["gene_name"],
            "spacer": full["target_sequence"],
            "atac_signal": full[atac_col],
            "chopchop_score": full["chop2014"],
            "deepspcas9_score": full["deepspcas9"],
            "indel_pct": full["indel_avg"],
        }
    ).replace("-", pd.NA)
    for col in ["atac_signal", "chopchop_score", "deepspcas9_score", "indel_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna()


def evaluate(df: pd.DataFrame) -> dict:
    weights = GuideScoreWeights()
    acc_scores, gate_passes = [], []
    for row in df.itertuples():
        result = score_guide(
            GuideScoreInputs(
                spacer=row.spacer, deepspcas9_score=row.deepspcas9_score,
                chopchop_score=row.chopchop_score, atac_signal=row.atac_signal, delivery="rnp",
            ),
            weights,
        )
        acc_scores.append(result.accessibility)
        gate_passes.append(passes_ito_thresholds(row.deepspcas9_score, row.chopchop_score, row.atac_signal))

    rho, pval = spearmanr(acc_scores, df["indel_pct"])
    actual = df["indel_pct"] > 50
    predicted = pd.Series(gate_passes, index=df.index)
    tp = int((predicted & actual).sum())
    fp = int((predicted & ~actual).sum())
    fn = int((~predicted & actual).sum())
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    return {"n": len(df), "accessibility_rho": rho, "accessibility_p": pval,
            "gate_precision": precision, "gate_recall": recall, "gate_tp": tp, "gate_fp": fp, "gate_fn": fn}


def main() -> None:
    full = pd.read_csv(FULL_TABLE)
    rows = []
    for label, col in REPLICATES.items():
        stats = evaluate(build_dataset(full, col))
        stats["replicate"] = label
        rows.append(stats)

    report = ["# Agent 4 — ATAC replicate sensitivity check", ""]
    report.append("| Replicate | n | accessibility ρ | p | gate precision | gate recall | TP | FP | FN |")
    report.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        report.append(
            f"| {r['replicate']} | {r['n']} | {r['accessibility_rho']:.3f} | {r['accessibility_p']:.3g} | "
            f"{r['gate_precision']:.3f} | {r['gate_recall']:.3f} | {r['gate_tp']} | {r['gate_fp']} | {r['gate_fn']} |"
        )
    report.append("")
    report.append(
        "If these numbers move a lot between replicates, the ATAC>=0.1 threshold is picking up "
        "sequencing-run-specific scale/noise, not a stable biological cutoff — treat any single-"
        "replicate accessibility result with that in mind."
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / "REPLICATE_SENSITIVITY_REPORT.md"
    out_path.write_text("\n".join(report) + "\n")
    print("\n".join(report))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
