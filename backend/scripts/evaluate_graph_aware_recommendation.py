from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Dict, List

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/qmof-matplotlib")

import numpy as np
import pandas as pd

from app.evaluation.baselines import (
    OBJECTIVE_COLUMNS,
    objective_matrix,
    query_weight_vector,
    rank_semantic_only,
    rank_weighted_sum,
)
from app.evaluation.metrics import evaluate_ranking
from app.evaluation.query_suite import QUERY_SUITE
from app.recommendation.lea_optimizer import LotusEffectOptimizer
from scripts.evaluate_lea_recommender import build_candidate_pool, load_materials


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _attach_graph_scores(pool: List[Dict], id_to_idx: Dict[str, int], embeddings: np.ndarray, weights: Dict[str, float]) -> List[Dict]:
    base = rank_weighted_sum(pool, weights, top_k=min(10, len(pool)))
    base_indices = [id_to_idx[str(item.get("qmof_id"))] for item in base if str(item.get("qmof_id")) in id_to_idx]
    if not base_indices:
        query_embedding = np.mean(embeddings, axis=0)
    else:
        query_embedding = np.mean(embeddings[base_indices], axis=0)
    scored = []
    sims = []
    for item in pool:
        idx = id_to_idx[str(item.get("qmof_id"))]
        sim = _cosine(embeddings[idx], query_embedding)
        sims.append(sim)
        copied = dict(item)
        copied["_raw_graph_similarity"] = sim
        scored.append(copied)
    sims_arr = np.asarray(sims, dtype=np.float32)
    low, high = float(np.min(sims_arr)), float(np.max(sims_arr))
    for item in scored:
        if high > low:
            item["graph_score"] = (item["_raw_graph_similarity"] - low) / (high - low)
        else:
            item["graph_score"] = 0.0
    return scored


def _rank_graph_only(pool: List[Dict], top_k: int, method: str) -> List[Dict]:
    scores = np.asarray([float(item.get("graph_score", 0.0)) for item in pool], dtype=np.float32)
    order = np.argsort(scores)[::-1][:top_k]
    ranked = []
    for rank, idx in enumerate(order, start=1):
        item = dict(pool[int(idx)])
        item["rank"] = rank
        item["method"] = method
        item["baseline_score"] = round(float(scores[int(idx)]), 6)
        ranked.append(item)
    return ranked


def _rank_lea_graph(pool: List[Dict], weights: Dict[str, float], top_k: int, seed: int, graph_weight: float = 0.15) -> List[Dict]:
    original_by_id = {str(item.get("qmof_id")): item for item in pool}
    adjusted = []
    for item in pool:
        copied = dict(item)
        copied["semantic_score"] = (
            (1.0 - graph_weight) * float(copied.get("semantic_score", 0.0))
            + graph_weight * float(copied.get("graph_score", 0.0))
        )
        adjusted.append(copied)
    optimizer = LotusEffectOptimizer(population_size=30, max_iterations=60, top_k=top_k, seed=seed)
    ranked = optimizer.rank(adjusted, weights, top_k=top_k)
    seen = set()
    clean_ranked = []
    for item in ranked:
        qmof_id = str(item.get("qmof_id"))
        if qmof_id in seen or qmof_id not in original_by_id:
            continue
        seen.add(qmof_id)
        restored = dict(original_by_id[qmof_id])
        restored["graph_score"] = float(item.get("graph_score", restored.get("graph_score", 0.0)))
        clean_ranked.append(restored)
    if len(clean_ranked) < top_k:
        fallback = rank_weighted_sum(adjusted, weights, top_k=len(adjusted))
        for item in fallback:
            qmof_id = str(item.get("qmof_id"))
            if qmof_id in seen or qmof_id not in original_by_id:
                continue
            seen.add(qmof_id)
            restored = dict(original_by_id[qmof_id])
            restored["graph_score"] = float(item.get("graph_score", restored.get("graph_score", 0.0)))
            clean_ranked.append(restored)
            if len(clean_ranked) >= top_k:
                break
    for rank, item in enumerate(clean_ranked[:top_k], start=1):
        item["rank"] = rank
    return clean_ranked[:top_k]


def _extra_metrics(ranked: List[Dict], pool: List[Dict]) -> Dict[str, float]:
    matrix = objective_matrix(ranked)
    pool_matrix = objective_matrix(pool)
    coverage = len({str(item.get("qmof_id", i)) for i, item in enumerate(ranked)}) / max(1, len(ranked))
    novelty = float(np.mean(np.linalg.norm(matrix - np.mean(pool_matrix, axis=0), axis=1))) if len(ranked) else 0.0
    return {"coverage": coverage, "novelty": novelty}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, default=Path("backend/vector_db/metadata.json"))
    parser.add_argument("--gnn-dir", type=Path, default=Path("reports/full_rerun/gnn"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports/full_rerun/graph_recommendation"))
    parser.add_argument("--candidate-pool-size", type=int, default=100)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    materials = load_materials(args.metadata)
    id_to_idx = {str(item.get("qmof_id")): idx for idx, item in enumerate(materials)}
    embedding_paths = {
        "GraphSAGE": args.gnn_dir / "graphsage_band_gap_embeddings.npy",
        "GAT": args.gnn_dir / "gat_band_gap_embeddings.npy",
    }
    available_embeddings = {
        name: np.load(path)
        for name, path in embedding_paths.items()
        if path.exists()
    }
    skipped = []
    for name, path in embedding_paths.items():
        if name not in available_embeddings:
            skipped.append(f"{name} graph-aware variants skipped because `{path}` was not found.")

    rows = []
    for seed in args.seeds:
        for query_index, query in enumerate(QUERY_SUITE):
            pool = build_candidate_pool(materials, query, args.candidate_pool_size)
            base_variants = [
                ("SemanticOnly", rank_semantic_only(pool, args.top_k)),
                ("WeightedSum", rank_weighted_sum(pool, query["weights"], args.top_k)),
            ]
            lea_started = time.perf_counter()
            lea_ranked = LotusEffectOptimizer(seed=seed + query_index).rank(pool, query["weights"], top_k=args.top_k)
            lea_runtime = (time.perf_counter() - lea_started) * 1000.0
            for item in lea_ranked:
                item["rank"] = item.get("lea_rank", item.get("rank"))
            for label, ranked in base_variants:
                started = time.perf_counter()
                runtime_ms = (time.perf_counter() - started) * 1000.0
                metrics = evaluate_ranking(ranked, pool, query["weights"], args.top_k)
                metrics.update(_extra_metrics(ranked, pool))
                rows.append({"seed": seed, "query_id": query["query_id"], "variant": label, "runtime_ms": runtime_ms, **metrics})
            metrics = evaluate_ranking(lea_ranked, pool, query["weights"], args.top_k)
            metrics.update(_extra_metrics(lea_ranked, pool))
            rows.append({"seed": seed, "query_id": query["query_id"], "variant": "LEA", "runtime_ms": lea_runtime, **metrics})

            for model_name, embeddings in available_embeddings.items():
                graph_pool = _attach_graph_scores(pool, id_to_idx, embeddings, query["weights"])
                started = time.perf_counter()
                graph_ranked = _rank_graph_only(graph_pool, args.top_k, f"{model_name}-only")
                runtime_ms = (time.perf_counter() - started) * 1000.0
                metrics = evaluate_ranking(graph_ranked, graph_pool, query["weights"], args.top_k)
                metrics.update(_extra_metrics(graph_ranked, graph_pool))
                rows.append({"seed": seed, "query_id": query["query_id"], "variant": f"{model_name}-only", "runtime_ms": runtime_ms, **metrics})

                started = time.perf_counter()
                lea_graph_ranked = _rank_lea_graph(graph_pool, query["weights"], args.top_k, seed + query_index)
                runtime_ms = (time.perf_counter() - started) * 1000.0
                metrics = evaluate_ranking(lea_graph_ranked, graph_pool, query["weights"], args.top_k)
                metrics.update(_extra_metrics(lea_graph_ranked, graph_pool))
                rows.append({"seed": seed, "query_id": query["query_id"], "variant": f"LEA + {model_name}", "runtime_ms": runtime_ms, **metrics})

    metrics_df = pd.DataFrame(rows)
    summary = (
        metrics_df.groupby("variant")
        .agg(
            rel_at_k_mean=("mean_relevance", "mean"),
            rel_at_k_std=("mean_relevance", "std"),
            ndcg_at_k_mean=("ndcg_at_k", "mean"),
            ndcg_at_k_std=("ndcg_at_k", "std"),
            diversity_mean=("diversity", "mean"),
            diversity_std=("diversity", "std"),
            coverage_mean=("coverage", "mean"),
            novelty_mean=("novelty", "mean"),
            runtime_ms_mean=("runtime_ms", "mean"),
            runtime_ms_std=("runtime_ms", "std"),
            runs=("runtime_ms", "count"),
        )
        .reset_index()
    )
    metrics_df.to_csv(args.out_dir / "graph_recommendation_metrics.csv", index=False)
    summary.to_csv(args.out_dir / "graph_recommendation_summary.csv", index=False)
    with (args.out_dir / "graph_recommendation_notes.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "embedding_sources": {name: str(path) for name, path in embedding_paths.items()},
                "skipped": skipped,
                "graph_objective_note": "Graph-aware LEA blends normalized graph similarity into semantic_score with graph_weight=0.15.",
            },
            handle,
            indent=2,
        )
    print(f"Wrote graph-aware recommendation outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
