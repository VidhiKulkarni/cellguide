#!/usr/bin/env python3
"""
Agent 4 — benchmarking / validation (CellGuide AI pipeline stage 4, see ../CLAUDE.md).

Deterministic (no LLM): scores each guide with Agent 3's metric
(../agent3_metric_construction/guide_scoring.py) and compares it against Ito et al. 2024's
measured indel%, including the T-cell-open vs K562-open gene panel check.

Ground-truth data gap (see ../papers/ito_2024/structured_extraction.md and MANIFEST.md):
the fetched full text only contains a *schema summary* of Supplementary Table S1 (205
gRNAs x 26 cols) and Table S2 (the 7-gene T-cell/K562 panel) — not the row-level values.
This script expects that data as a CSV; it refuses to fabricate numbers when it's missing.

Usage:
    # once the ground-truth CSV has been fetched and saved:
    uv run agent4_benchmarking/run.py --data path/to/table_s1.csv

    # to sanity-check the script itself before real data is available:
    uv run agent4_benchmarking/run.py --demo
"""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent3_metric_construction"))
from guide_scoring import GuideScoreInputs, GuideScoreWeights, score_guide  # noqa: E402

HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output"

REQUIRED_COLUMNS = ["gene", "spacer", "atac_signal", "chopchop_score", "deepspcas9_score", "indel_pct"]

DEMO_ROWS = [
    # Synthetic example rows — NOT real Ito et al. 2024 measurements. Only for exercising
    # the pipeline before the real Table S1 ground truth is fetched (see module docstring).
    {"gene": "GZMA", "cell_type": "T", "spacer": "GACCTGAAGCTGAGCGAGTG", "atac_signal": 0.42, "chopchop_score": 0.61, "deepspcas9_score": 71.2, "indel_pct": 88.0},
    {"gene": "GZMA", "cell_type": "K562", "spacer": "GACCTGAAGCTGAGCGAGTG", "atac_signal": 0.02, "chopchop_score": 0.61, "deepspcas9_score": 71.2, "indel_pct": 9.0},
    {"gene": "GATA1", "cell_type": "K562", "spacer": "TCCTGGAGAACCGCAAGGCC", "atac_signal": 0.55, "chopchop_score": 0.58, "deepspcas9_score": 64.0, "indel_pct": 81.0},
    {"gene": "GATA1", "cell_type": "T", "spacer": "TCCTGGAGAACCGCAAGGCC", "atac_signal": 0.03, "chopchop_score": 0.58, "deepspcas9_score": 64.0, "indel_pct": 7.0},
]


def load_ground_truth(data_path: Path | None, demo: bool) -> pd.DataFrame:
    if demo:
        print("[demo mode] using synthetic example rows — NOT real Ito et al. 2024 data\n")
        return pd.DataFrame(DEMO_ROWS)

    if data_path is None or not data_path.exists():
        sys.exit(
            "No ground-truth data found.\n\n"
            f"Expected a CSV with columns {REQUIRED_COLUMNS} (+ optional 'cell_type').\n"
            "Ito et al. 2024's Supplementary Table S1 (205 gRNAs) and Table S2 (the T-cell-open "
            "vs K562-open panel) have only been fetched as a *schema summary* so far — see "
            "papers/ito_2024/structured_extraction.md. Fetch the row-level data (e.g. re-run "
            "agent1_literature_search for the NAR supplementary Excel file and export it to CSV) "
            "before running this benchmark for real.\n\n"
            "Run with --demo to sanity-check this script against synthetic data instead."
        )
    df = pd.read_csv(data_path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        sys.exit(f"{data_path} is missing required columns: {missing}")
    return df


def run_benchmark(df: pd.DataFrame, weights: GuideScoreWeights) -> pd.DataFrame:
    results = []
    for row in df.itertuples():
        result = score_guide(
            GuideScoreInputs(
                spacer=row.spacer,
                deepspcas9_score=row.deepspcas9_score,
                chopchop_score=row.chopchop_score,
                atac_signal=row.atac_signal,
                delivery="rnp",  # Ito et al. 2024 used Cas9 RNP electroporation, not a vector
            ),
            weights,
        )
        results.append(
            {
                "gene": row.gene,
                "cell_type": getattr(row, "cell_type", None),
                "spacer": row.spacer,
                "indel_pct": row.indel_pct,
                "combined_score": result.combined,
                "recommended_score": result.recommended_score,
                "sequence_efficacy": result.sequence_efficacy,
                "accessibility": result.accessibility,
                "passes_ito_rule": result.passes_ito_rule,
                "deepspcas9_score": row.deepspcas9_score,
                "chopchop_score": row.chopchop_score,
                "atac_signal": row.atac_signal,
            }
        )
    return pd.DataFrame(results)


def _prf(predicted: pd.Series, actual: pd.Series) -> tuple[float, float, float, int, int, int]:
    tp = int((predicted & actual).sum())
    fp = int((predicted & ~actual).sum())
    fn = int((~predicted & actual).sum())
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else float("nan")
    return precision, recall, f1, tp, fp, fn


def baseline_comparison(results: pd.DataFrame, weights: GuideScoreWeights) -> str:
    """Compare combined_score against its own components in isolation, and check the Ito et
    al. AND-gate rule (including its marginal contribution over sequence gates alone — Agent
    5 finding: the accessibility gate *reduces* F1 relative to sequence gates alone). Two
    components only (sequence_efficacy, accessibility) — specificity was removed from the
    scoring library entirely (agent3_metric_construction/guide_scoring.py module docstring),
    not just left unevaluated, since no real off-target data source was ever wired in."""
    lines = [
        "### Baseline comparison (component-only vs combined)\n",
        f"`combined_score = {weights.w_seq}*sequence_efficacy + {weights.w_atac}*accessibility` "
        "(renormalized when accessibility is unavailable for a guide).\n",
        "| Component | Spearman ρ vs indel% | p-value |",
        "|---|---|---|",
    ]
    for col in ["sequence_efficacy", "accessibility", "combined_score", "recommended_score"]:
        rho, pval = spearmanr(results[col], results["indel_pct"])
        lines.append(f"| `{col}` | {rho:.3f} | {pval:.3g} |")

    if "passes_ito_rule" in results.columns:
        actual = results["indel_pct"] > 50
        seq_gate = (results["deepspcas9_score"] >= 60) & (results["chopchop_score"] >= 0.3)
        full_rule = results["passes_ito_rule"]

        lines.append("")
        lines.append("### Does the accessibility gate earn its keep? (>50%-indel classifier)\n")
        lines.append("| Rule | Precision | Recall | F1 | TP | FP | FN |")
        lines.append("|---|---|---|---|---|---|---|")
        for label, pred in [("Sequence gates only (no ATAC)", seq_gate), ("Full Ito rule (+ ATAC≥0.1)", full_rule)]:
            p, r, f1, tp, fp, fn = _prf(pred, actual)
            lines.append(f"| {label} | {p:.3f} | {r:.3f} | {f1:.3f} | {tp} | {fp} | {fn} |")
        seq_f1 = _prf(seq_gate, actual)[2]
        full_f1 = _prf(full_rule, actual)[2]
        seq_p = _prf(seq_gate, actual)[0]
        full_p = _prf(full_rule, actual)[0]
        lines.append(
            f"\nF1 {'drops' if full_f1 < seq_f1 else 'improves'} when the ATAC≥0.1 gate is added "
            f"({seq_f1:.3f} -> {full_f1:.3f}), but **F1 is the wrong metric to judge this rule by** "
            "— SPEC.md itself documents this as intended to be \"a high-precision, low-recall "
            "filter, not a general ranker,\" and *any* added AND-condition mechanically reduces "
            "recall regardless of whether the added condition is useful, so F1 will almost always "
            f"fall here. What the gate is actually designed to do is raise precision, and it does: "
            f"{seq_p:.3f} -> {full_p:.3f}. See `interaction_effect_check.py` for the statistically "
            "correct test of Ito et al.'s actual accessibility claim (a conditional effect, not "
            f"reflected in this precision/recall table) — evaluable on "
            f"{int(full_rule.notna().sum())}/{len(results)} guides here."
        )
    return "\n".join(lines)


def cross_context_check(results: pd.DataFrame) -> str:
    """Reproduce Ito et al.'s specific finding: T-cell-open genes score high in T cells and
    low in K562, and vice versa for K562-open genes — check if it holds for combined_score."""
    if "cell_type" not in results.columns or results["cell_type"].isna().all():
        return "No cell_type column — skipping T-cell-open vs K562-open panel check."

    lines = ["### T-cell-open vs K562-open panel check\n"]
    for gene, group in results.groupby("gene"):
        by_ct = group.set_index("cell_type")["combined_score"]
        lines.append(f"- **{gene}**: " + ", ".join(f"{ct}={score:.3f}" for ct, score in by_ct.items()))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent 4 — benchmarking / validation")
    parser.add_argument("--data", type=Path, default=None, help="CSV of ground-truth guide data")
    parser.add_argument("--demo", action="store_true", help="Use synthetic demo data instead of real ground truth")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_ground_truth(args.data, args.demo)
    weights = GuideScoreWeights()
    results = run_benchmark(df, weights)

    results_path = OUTPUT_DIR / ("demo_results.csv" if args.demo else "results.csv")
    results.to_csv(results_path, index=False)

    rho, pval = spearmanr(results["combined_score"], results["indel_pct"])

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(results["combined_score"], results["indel_pct"], alpha=0.7)
    ax.set_xlabel("CellGuide combined score")
    ax.set_ylabel("Measured indel %")
    ax.set_title(f"Spearman ρ = {rho:.3f} (p = {pval:.3g})")
    fig_path = OUTPUT_DIR / ("demo_correlation.png" if args.demo else "correlation.png")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=150)

    report = [
        "# Agent 4 — benchmark report" + (" (DEMO — synthetic data, not real Ito et al. 2024 numbers)" if args.demo else ""),
        "",
        f"- n = {len(results)} guides",
        f"- weights: w_seq={weights.w_seq}, w_atac={weights.w_atac}",
        f"- Spearman correlation (combined_score vs indel %): ρ = {rho:.3f}, p = {pval:.3g}",
        f"- results table: `{results_path.name}`",
        f"- scatter figure: `{fig_path.name}`",
        "",
        baseline_comparison(results, weights),
        "",
        cross_context_check(results),
    ]
    report_path = OUTPUT_DIR / ("DEMO_REPORT.md" if args.demo else "REPORT.md")
    report_path.write_text("\n".join(report) + "\n")

    print("\n".join(report))
    print(f"\nWrote {results_path}, {fig_path}, {report_path}")


if __name__ == "__main__":
    main()
