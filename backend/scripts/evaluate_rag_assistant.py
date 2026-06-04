from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import pandas as pd

from app.evaluation.query_suite import QUERY_SUITE


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("reports/full_rerun/rag_llm"))
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    retrieval_rows = []
    examples = ["# RAG / LLM Assistant Evaluation\n"]
    retrieval_status = "not_started"
    retrieval_error = ""

    try:
        from app.rag.retriever import retrieve_materials
        from app.rag.vector_store import vector_store

        vector_store.load()
        for query in QUERY_SUITE:
            started = time.perf_counter()
            results = retrieve_materials(query["query"], top_k=args.top_k)
            runtime_ms = (time.perf_counter() - started) * 1000.0
            retrieved_ids = []
            density_available = 0
            band_gap_available = 0
            void_available = 0
            keyword_hits = 0
            for item in results:
                doc = item.get("document", {})
                retrieved_ids.append(str(doc.get("qmof_id", "")))
                density_available += doc.get("density") not in [None, "", "nan"]
                band_gap_available += doc.get("band_gap") not in [None, "", "nan"]
                void_available += doc.get("void_fraction") not in [None, "", "nan"]
                text = (str(doc.get("text", "")) + " " + str(doc.get("formula", ""))).lower()
                keyword_hits += sum(1 for kw in query.get("keywords", []) if kw.lower() in text)
            retrieval_rows.append(
                {
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "retrieved_count": len(results),
                    "runtime_ms": runtime_ms,
                    "density_available_at_k": density_available,
                    "band_gap_available_at_k": band_gap_available,
                    "void_fraction_available_at_k": void_available,
                    "keyword_hit_count_at_k": keyword_hits,
                    "retrieved_qmof_ids": ";".join(retrieved_ids),
                }
            )
            examples.append(f"## {query['query_id']}\n")
            examples.append(f"Query: {query['query']}\n")
            examples.append(f"Retrieved QMOFs: {', '.join(retrieved_ids)}\n")
        retrieval_status = "executed"
    except Exception as exc:
        retrieval_status = "not_executable"
        retrieval_error = repr(exc)
        examples.append(f"RAG retrieval was not executable in this environment: `{retrieval_error}`\n")

    pd.DataFrame(retrieval_rows).to_csv(args.out_dir / "rag_retrieval_metrics.csv", index=False)

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        llm_rows = [
            {
                "status": "not_executed",
                "reason": "The script does not call external LLM APIs during reproducibility reruns to avoid non-deterministic and potentially billable outputs.",
                "groundedness": "",
                "citation_fidelity": "",
                "metadata_consistency": "",
            }
        ]
        examples.append("\nLLM answer generation was intentionally not executed despite OPENAI_API_KEY being present; no LLM-quality claims are reported.\n")
    else:
        llm_rows = [
            {
                "status": "not_executable",
                "reason": "OPENAI_API_KEY is not set; repository LLM client depends on OpenAI chat completions.",
                "groundedness": "",
                "citation_fidelity": "",
                "metadata_consistency": "",
            }
        ]
        examples.append("\nLLM answer-quality evaluation was not executable because OPENAI_API_KEY is not set.\n")
    pd.DataFrame(llm_rows).to_csv(args.out_dir / "llm_assistant_eval.csv", index=False)
    with (args.out_dir / "example_outputs.md").open("w", encoding="utf-8") as handle:
        handle.write("\n".join(examples))
    with (args.out_dir / "rag_llm_status.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "retrieval_status": retrieval_status,
                "retrieval_error": retrieval_error,
                "llm_status": llm_rows[0]["status"],
                "llm_reason": llm_rows[0]["reason"],
            },
            handle,
            indent=2,
        )
    print(f"Wrote RAG/LLM outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
