import pandas as pd
import json

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPORT_DIR = ROOT / "reports" / "rag_llm_evaluation"

CSV_FILE = REPORT_DIR / "rag_llm_eval_results.csv"


def load():

    return pd.read_csv(CSV_FILE)


def summary_statistics(
    df,
):

    stats = {
        "queries": int(len(df)),
        "avg_groundedness": round(
            df["groundedness_score"].mean(),
            3,
        ),
        "avg_metadata_consistency": round(
            df["metadata_consistency_score"].mean(),
            3,
        ),
        "avg_limitation_awareness": round(
            df["limitation_awareness_score"].mean(),
            3,
        ),
        "avg_explanation_quality": round(
            df["explanation_quality_score"].mean(),
            3,
        ),
        "hallucination_rate": round(
            100 * df["hallucination_detected"].mean(),
            2,
        ),
        "metadata_error_rate": round(
            100 * (df["metadata_error"] > 0).mean(),
            2,
        ),
    }

    return stats


def generate_table_a():

    table = """

| Dimension | Score Definition |

|---|---|

| Groundedness | Uses retrieved metadata and evidence |

| Metadata Consistency | Correct IDs, formulas, band gaps, density |

| Limitation Awareness | States missing descriptors and uncertainty |

| Explanation Quality | Explains ranking logic and suitability |

| Hallucination Risk | Unsupported claims detection |

"""

    with open(
        REPORT_DIR / "table_a_scoring_rubric.md",
        "w",
        encoding="utf8",
    ) as f:

        f.write(table)


def generate_table_b(
    df,
):

    grouped = (
        df.groupby("scenario")
        .agg(
            {
                "groundedness_score": "mean",
                "metadata_consistency_score": "mean",
                "limitation_awareness_score": "mean",
                "explanation_quality_score": "mean",
                "hallucination_detected": "mean",
            }
        )
        .reset_index()
    )

    grouped["hallucination_detected"] = grouped["hallucination_detected"] * 100

    grouped.to_markdown(
        REPORT_DIR / "table_b_summary_results.md",
        index=False,
    )


def generate_report(
    stats,
):

    report = f"""

# RAG / LLM Evaluation Report

## Evaluation Protocol

30 benchmark scientific queries were evaluated.

Retrieval:

top-k = 5

Evaluation dimensions:

groundedness

metadata consistency

limitation awareness

hallucination risk

explanation quality


## Summary Statistics

Queries:

{stats["queries"]}

Average Groundedness:

{stats["avg_groundedness"]}

Average Metadata Consistency:

{stats["avg_metadata_consistency"]}

Average Limitation Awareness:

{stats["avg_limitation_awareness"]}

Average Explanation Quality:

{stats["avg_explanation_quality"]}

Hallucination Rate:

{stats["hallucination_rate"]}%


## Main Limitations

Current evaluation does not evaluate:

experimental validation

physics-based simulation

adsorption benchmarks

CIF-derived graph neural networks

The assistant is evaluated only for explanation quality and metadata consistency.

"""

    with open(
        REPORT_DIR / "rag_llm_evaluation_report.md",
        "w",
        encoding="utf8",
    ) as f:

        f.write(report)


def main():

    df = load()

    stats = summary_statistics(df)

    with open(
        REPORT_DIR / "rag_llm_summary.json",
        "w",
    ) as f:

        json.dump(
            stats,
            f,
            indent=2,
        )

    generate_table_a()

    generate_table_b(df)

    generate_report(stats)

    print("Report generated.")


if __name__ == "__main__":

    main()
