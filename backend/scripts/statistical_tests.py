from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, wilcoxon


def _cohens_d_paired(a: np.ndarray, b: np.ndarray) -> float:
    diff = a - b
    std = np.std(diff, ddof=1)
    if std <= 0:
        return 0.0
    return float(np.mean(diff) / std)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ablation-metrics", type=Path, default=Path("reports/full_rerun/ablation/ablation_metrics.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports/full_rerun/statistics"))
    parser.add_argument("--metric", default="mean_relevance")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.ablation_metrics)
    rows = []
    pivot = df.pivot_table(index=["seed", "query_id"], columns="variant", values=args.metric, aggfunc="mean")
    comparisons = [
        ("LEA baseline", "WeightedSum"),
        ("LEA baseline", "MMR"),
        ("LEA baseline", "RandomRepeated"),
        ("LEA baseline", "SemanticOnly"),
    ]
    for first, second in comparisons:
        if first not in pivot.columns or second not in pivot.columns:
            rows.append({"test": "wilcoxon", "comparison": f"{first} vs {second}", "status": "not_executable", "reason": "missing variant"})
            continue
        paired = pivot[[first, second]].dropna()
        if len(paired) < 5:
            rows.append({"test": "wilcoxon", "comparison": f"{first} vs {second}", "status": "not_executable", "reason": "fewer than five paired observations"})
            continue
        stat, p_value = wilcoxon(paired[first].to_numpy(), paired[second].to_numpy(), zero_method="wilcox")
        rows.append(
            {
                "test": "wilcoxon_signed_rank",
                "comparison": f"{first} vs {second}",
                "metric": args.metric,
                "n_pairs": len(paired),
                "statistic": float(stat),
                "p_value": float(p_value),
                "mean_first": float(paired[first].mean()),
                "mean_second": float(paired[second].mean()),
                "paired_cohens_d": _cohens_d_paired(paired[first].to_numpy(), paired[second].to_numpy()),
                "status": "executed",
                "reason": "",
            }
        )

    friedman_variants = ["SemanticOnly", "WeightedSum", "MMR", "RandomRepeated", "LEA baseline"]
    available = [variant for variant in friedman_variants if variant in pivot.columns]
    if len(available) >= 3:
        paired = pivot[available].dropna()
        if len(paired) >= 5:
            stat, p_value = friedmanchisquare(*[paired[col].to_numpy() for col in available])
            rows.append(
                {
                    "test": "friedman",
                    "comparison": ";".join(available),
                    "metric": args.metric,
                    "n_pairs": len(paired),
                    "statistic": float(stat),
                    "p_value": float(p_value),
                    "status": "executed",
                    "reason": "",
                }
            )
    out = pd.DataFrame(rows)
    out.to_csv(args.out_dir / "statistical_tests.csv", index=False)
    with (args.out_dir / "statistical_summary.md").open("w", encoding="utf-8") as handle:
        handle.write("# Statistical Tests\n\n")
        handle.write(f"Input: `{args.ablation_metrics}`\n\n")
        handle.write(f"Metric: `{args.metric}`\n\n")
        handle.write(out.to_markdown(index=False))
        handle.write("\n")
    print(f"Wrote statistical outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
