import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.append(str(ROOT))

import pandas as pd
from tqdm import tqdm

from app.rag.retriever import retrieve_materials

from app.evaluation.metadata_checker import (
    metadata_checker,
)

from app.evaluation.hallucination_checker import (
    hallucination_checker,
)

from app.evaluation.scoring_rubric import (
    scoring_rubric,
)

from app.services.chat_service import (
    chat_service,
)

##################################################
# PATHS
##################################################

BENCHMARK_FILE = ROOT / "app" / "evaluation" / "benchmark_queries.json"

OUTPUT_DIR = ROOT / "reports" / "rag_llm_evaluation"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CSV_OUTPUT = OUTPUT_DIR / "rag_llm_eval_results.csv"


##################################################
# LOAD BENCHMARK QUERIES
##################################################


def load_queries():

    with open(
        BENCHMARK_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


##################################################
# EXTRACT RETRIEVED IDS
##################################################


def extract_retrieved_ids(
    retrieved,
):

    ids = []

    for item in retrieved:

        doc = item.get(
            "document",
            {},
        )

        qmof_id = doc.get("qmof_id")

        if qmof_id:

            ids.append(str(qmof_id))

    return ids


##################################################
# SUMMARIZE TOP RETRIEVED EVIDENCE
##################################################


def summarize_retrieved_evidence(
    retrieved,
    max_items=5,
):
    """
    Produce a compact, human-readable summary of the top retrieved
    documents (qmof_id, formula, band gap, density) for the CSV's
    `top_retrieved_evidence` column, per Mehrdad's spec.
    """

    summaries = []

    for item in retrieved[:max_items]:

        doc = item.get("document", {})

        qmof_id = doc.get("qmof_id", "unknown")
        formula = doc.get("formula", "n/a")
        band_gap = doc.get("band_gap", "n/a")
        density = doc.get("density", "n/a")

        summaries.append(
            f"{qmof_id} ({formula}, band_gap={band_gap}, density={density})"
        )

    return "; ".join(summaries)


##################################################
# SINGLE QUERY EVALUATION
##################################################


def run_single_query(
    query_object,
):

    query_text = query_object["query_text"]

    scenario = query_object["scenario"]

    ##################################################
    # RETRIEVAL
    ##################################################

    retrieved = retrieve_materials(
        query=query_text,
        top_k=5,
    )

    retrieved_ids = extract_retrieved_ids(retrieved)

    top_retrieved_evidence = summarize_retrieved_evidence(retrieved)

    ##################################################
    # CHAT / RAG ANSWER
    ##################################################

    llm_response = chat_service.ask(query_text)

    llm_answer = str(
        llm_response.get(
            "answer",
            "",
        )
    )

    ##################################################
    # METADATA CHECK
    ##################################################

    # Use the RAG-retrieved documents (the actual context the LLM saw via
    # chat_service.ask()), not the recommendation pipeline's separate
    # candidate list - these are two different retrieval/ranking paths and
    # checking against the wrong one produces false "metadata error" flags
    # even when the LLM's answer is fully grounded and correct.
    retrieved_documents = [
        item.get("document", {}) for item in retrieved if item.get("document")
    ]

    metadata_result = metadata_checker.check_metadata_consistency(
        generated_answer=llm_answer,
        retrieved_materials=retrieved_documents,
    )

    ##################################################
    # HALLUCINATION CHECK
    ##################################################

    hallucination_result = hallucination_checker.detect(llm_answer)

    ##################################################
    # SCORING
    ##################################################

    groundedness = scoring_rubric.groundedness_score(
        retrieved_qmof_ids=retrieved_ids,
        mentioned_qmof_ids=metadata_result["mentioned_qmof_ids"],
    )

    metadata_score = scoring_rubric.metadata_consistency_score(
        metadata_result["metadata_errors"]
    )

    limitation_score = scoring_rubric.limitation_awareness_score(
        metadata_checker.missing_descriptor_warning(llm_answer),
        hallucination_result["unsupported_adsorption_claim"],
    )

    explanation_score = scoring_rubric.explanation_quality_score(
        explanation_length=len(llm_answer),
        explanation_mentions_properties=len(metadata_result["metadata_fields_used"])
        > 0,
        explanation_mentions_uncertainty=metadata_checker.missing_descriptor_warning(
            llm_answer
        ),
    )

    ##################################################
    # OUTPUT ROW
    ##################################################

    return {
        "query_id": query_object["query_id"],
        "scenario": scenario,
        "query_text": query_text,
        "retrieved_qmof_ids": retrieved_ids,
        "top_retrieved_evidence": top_retrieved_evidence,
        "generated_answer": llm_answer,
        "mentioned_qmof_ids": metadata_result["mentioned_qmof_ids"],
        "metadata_fields_used": metadata_result["metadata_fields_used"],
        "groundedness_score": groundedness,
        "metadata_consistency_score": metadata_score,
        "limitation_awareness_score": limitation_score,
        "explanation_quality_score": explanation_score,
        **hallucination_result,
        "metadata_errors_count": metadata_result["metadata_errors"],
        "metadata_error": metadata_result["metadata_errors"] > 0,
        "missing_descriptor_warning": metadata_checker.missing_descriptor_warning(
            llm_answer
        ),
        "human_notes": "",
    }


def build_summary(df):
    """
    Builds the manuscript-ready Table B: per-scenario and overall summary
    of the RAG/LLM evaluation results.
    """

    def scenario_row(name, sub_df):
        n = len(sub_df)

        return {
            "scenario": name,
            "num_queries": n,
            "avg_retrieval_count": round(
                sub_df["retrieved_qmof_ids"].apply(len).mean(), 2
            ),
            "avg_groundedness": round(sub_df["groundedness_score"].mean(), 2),
            "avg_metadata_consistency": round(
                sub_df["metadata_consistency_score"].mean(), 2
            ),
            "avg_limitation_awareness": round(
                sub_df["limitation_awareness_score"].mean(), 2
            ),
            "avg_explanation_quality": round(
                sub_df["explanation_quality_score"].mean(), 2
            ),
            "hallucination_rate": round(
                sub_df["hallucination_detected"].mean() * 100, 1
            ),
            "metadata_error_rate": round(sub_df["metadata_error"].mean() * 100, 1),
            "missing_descriptor_warning_rate": round(
                sub_df["missing_descriptor_warning"].mean() * 100, 1
            ),
        }

    rows = []

    for scenario, sub_df in df.groupby("scenario"):
        rows.append(scenario_row(scenario, sub_df))

    rows.append(scenario_row("OVERALL", df))

    return rows


##################################################
# MAIN
##################################################


def main():

    queries = load_queries()

    rows = []

    for query in tqdm(queries):

        result = run_single_query(query)

        rows.append(result)

    df = pd.DataFrame(rows)

    df.to_csv(
        CSV_OUTPUT,
        index=False,
    )

    print(
        "\nSaved:",
        CSV_OUTPUT,
    )

    summary_table = build_summary(df)

    summary_path = OUTPUT_DIR / "rag_llm_summary.json"

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_table, f, indent=2)

    print("Saved:", summary_path)


if __name__ == "__main__":

    main()