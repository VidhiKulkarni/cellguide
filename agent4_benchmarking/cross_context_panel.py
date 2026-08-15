#!/usr/bin/env python3
"""
Agent 4 addendum — T-cell vs K562 cross-context panel check (Ito et al. 2024
Supplementary Table S2, the 11-gene "T-cell-open" vs "K562-open" panel behind
the plan's "same guide, different context" winning demo).

Unlike run.py's Table S1 benchmark, Table S2 has no per-guide indel% ground
truth in the supplement (the paper reports indel% for this panel only as a
figure, Fig. 2H-K, not as numbers) and no DeepSpCas9/CHOPCHOP columns —
so this script does NOT fabricate indel_pct/chopchop_score/deepspcas9_score
for it. It only computes what the real data supports: sequence_efficacy
(identical for a guide regardless of cell context, by construction) and the
accessibility term in each context, and checks whether accessibility alone
correctly flips direction the way the paper reports.

Usage:
    uv run agent4_benchmarking/cross_context_panel.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent3_metric_construction"))
from guide_scoring import sequence_efficacy, accessibility_score  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "papers" / "ito_2024" / "table_s2_tcell_vs_k562_panel.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    with open(DATA_PATH, newline="") as f:
        rows = list(csv.DictReader(f))

    out_rows = []
    for row in rows:
        spacer = row["target_sequence"]
        seq_eff = sequence_efficacy(spacer)  # no DeepSpCas9/CHOPCHOP for this table -> GC/motif fallback
        acc_t = accessibility_score(float(row["atac_score_tcell"]))
        acc_k = accessibility_score(float(row["atac_score_k562"]))
        is_tcell_open_gene = row["category"].startswith("T cell")
        direction_matches_paper = (acc_t > acc_k) if is_tcell_open_gene else (acc_k > acc_t)
        out_rows.append({
            "gene_name": row["gene_name"],
            "category": row["category"],
            "sequence_efficacy_fixed": round(seq_eff, 3),
            "accessibility_tcell": round(acc_t, 3),
            "accessibility_k562": round(acc_k, 3),
            "direction_matches_paper": direction_matches_paper,
        })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = OUTPUT_DIR / "cross_context_panel_results.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    n_correct = sum(r["direction_matches_paper"] for r in out_rows)
    report = [
        "# Agent 4 — cross-context panel check (Ito et al. 2024 Table S2)",
        "",
        f"n = {len(out_rows)} genes (6 T-cell-open, 5 K562-open — matches the plan's §3.3 10-gene panel + EOMES)",
        "",
        "No per-guide indel% ground truth is available for this panel (the paper reports it only as "
        "Figure 2H-K, not as numbers) — this check validates only what real data supports: whether the "
        "accessibility term alone, computed from real ATAC-seq scores, correctly flips direction between "
        "T cells and K562 for each gene's designated 'open' context, while sequence_efficacy stays fixed "
        "for the same guide across contexts (by construction, since sequence doesn't change).",
        "",
        f"**Result: accessibility correctly predicts the paper's reported open-chromatin context for "
        f"{n_correct}/{len(out_rows)} genes.**",
        "",
        "| Gene | Category | seq_efficacy (fixed) | accessibility (T cell) | accessibility (K562) | matches paper? |",
        "|---|---|---|---|---|---|",
    ]
    for r in out_rows:
        report.append(
            f"| {r['gene_name']} | {r['category']} | {r['sequence_efficacy_fixed']} | "
            f"{r['accessibility_tcell']} | {r['accessibility_k562']} | {r['direction_matches_paper']} |"
        )
    report.append("")
    report.append(f"Results CSV: `{out_csv.name}`")

    report_path = OUTPUT_DIR / "CROSS_CONTEXT_REPORT.md"
    report_path.write_text("\n".join(report) + "\n")
    print("\n".join(report))
    print(f"\nWrote {out_csv}, {report_path}")


if __name__ == "__main__":
    main()
