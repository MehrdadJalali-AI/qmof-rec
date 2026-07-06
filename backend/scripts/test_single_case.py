"""
Quick single-case tester for the RAG/LLM evaluation checkers.

Usage examples:

    # Test the checkers against a hand-written answer (no API calls):
    python -m scripts.test_single_case --mock

    # Run ONE benchmark query end-to-end (real retrieval + real LLM call):
    python -m scripts.test_single_case --query-id Q001

    # List available query IDs:
    python -m scripts.test_single_case --list
"""

import sys
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.evaluation.metadata_checker import metadata_checker
from app.evaluation.hallucination_checker import hallucination_checker
from app.evaluation.scoring_rubric import scoring_rubric


BENCHMARK_FILE = ROOT / "app" / "evaluation" / "benchmark_queries.json"


def load_queries():
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_checkers(answer: str, retrieved_materials: list, retrieved_ids: list):
    metadata_result = metadata_checker.check_metadata_consistency(
        generated_answer=answer,
        retrieved_materials=retrieved_materials,
    )

    hallucination_result = hallucination_checker.detect(answer)

    groundedness = scoring_rubric.groundedness_score(
        retrieved_qmof_ids=retrieved_ids,
        mentioned_qmof_ids=metadata_result["mentioned_qmof_ids"],
    )

    metadata_score = scoring_rubric.metadata_consistency_score(
        metadata_result["metadata_errors"]
    )

    limitation_score = scoring_rubric.limitation_awareness_score(
        metadata_checker.missing_descriptor_warning(answer),
        hallucination_result["unsupported_adsorption_claim"],
    )

    explanation_score = scoring_rubric.explanation_quality_score(
        explanation_length=len(answer),
        explanation_mentions_properties=len(metadata_result["metadata_fields_used"]) > 0,
        explanation_mentions_uncertainty=metadata_checker.missing_descriptor_warning(answer),
    )

    print("\n--- METADATA CHECK ---")
    print(json.dumps(metadata_result, indent=2))

    print("\n--- HALLUCINATION CHECK ---")
    print(json.dumps(hallucination_result, indent=2))

    print("\n--- SCORES ---")
    print(f"groundedness_score:        {groundedness}")
    print(f"metadata_consistency_score: {metadata_score}")
    print(f"limitation_awareness_score: {limitation_score}")
    print(f"explanation_quality_score:  {explanation_score}")


def run_mock_case():
    """
    Hand-written example - no API calls. Useful for quickly checking
    checker/regex logic after edits.
    """

    retrieved_materials = [
        {
            "qmof_id": "qmof-8a95c27",
            "formula": "Ba2CuC6H14O16",
            "band_gap": 1.23,
            "density": 2.76,
        },
        {
            "qmof_id": "qmof-019ba28",
            "formula": "Zn4O(BDC)3",
            "band_gap": 3.4,
            "density": 1.1,
        },
    ]

    retrieved_ids = [m["qmof_id"] for m in retrieved_materials]

    # A "good" answer: references retrieved IDs, flags missing data, no
    # adsorption/validation claims.
    good_answer = (
        "Based on the retrieved candidates, qmof-8a95c27 (Ba2CuC6H14O16, "
        "band gap 1.23 eV, density 2.76 g/cm3) and qmof-019ba28 "
        "(Zn4O(BDC)3, band gap 3.4 eV) are reasonable candidates for "
        "further screening. Note that void fraction and CO2 uptake data "
        "are not available in the current metadata, so porosity-related "
        "performance cannot be assessed directly. These are computational "
        "screening candidates and would require further validation."
    )

    # A "bad" answer: invents an adsorption number, claims validation, and
    # introduces a non-retrieved MOF.
    bad_answer = (
        "UiO-66 is an excellent choice, with a measured CO2 uptake of "
        "120 cm3/g and experimentally validated stability. qmof-8a95c27 "
        "also shows the highest porosity among known MOFs."
    )

    print("=" * 60)
    print("GOOD ANSWER")
    print("=" * 60)
    print(good_answer)
    run_checkers(good_answer, retrieved_materials, retrieved_ids)

    print("\n" + "=" * 60)
    print("BAD ANSWER")
    print("=" * 60)
    print(bad_answer)
    run_checkers(bad_answer, retrieved_materials, retrieved_ids)


def run_single_query(query_id: str):
    """
    Real end-to-end test for ONE benchmark query: real retrieval + real
    recommendation pipeline + real LLM call. Requires OPENAI_API_KEY.
    """

    from app.rag.retriever import retrieve_materials
    from app.recommendation.recommendation_pipeline import recommendation_pipeline
    from app.services.chat_service import chat_service

    queries = load_queries()
    query_object = next((q for q in queries if q["query_id"] == query_id), None)

    if query_object is None:
        print(f"Query ID '{query_id}' not found. Use --list to see available IDs.")
        return

    query_text = query_object["query_text"]
    print(f"Scenario: {query_object['scenario']}")
    print(f"Query:    {query_text}\n")

    retrieved = retrieve_materials(query=query_text, top_k=5)
    retrieved_ids = [
        item.get("document", {}).get("qmof_id")
        for item in retrieved
        if item.get("document", {}).get("qmof_id")
    ]
    print(f"Retrieved IDs: {retrieved_ids}\n")

    recommendation_result = recommendation_pipeline.recommend(query=query_text, top_k=5)
    retrieved_materials_list = recommendation_result.get("recommendations", [])

    llm_response = chat_service.ask(query_text)
    answer = str(llm_response.get("answer", ""))

    print("--- LLM ANSWER ---")
    print(answer)

    run_checkers(answer, retrieved_materials_list, retrieved_ids)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="Run hand-written good/bad examples (no API calls)")
    parser.add_argument("--query-id", type=str, help="Run one benchmark query end-to-end (e.g. Q001)")
    parser.add_argument("--list", action="store_true", help="List available query IDs and scenarios")
    args = parser.parse_args()

    if args.list:
        for q in load_queries():
            print(f"{q['query_id']:6} {q['scenario']:25} {q['query_text']}")
        return

    if args.mock:
        run_mock_case()
        return

    if args.query_id:
        run_single_query(args.query_id)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
