from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/qmof-matplotlib")

import numpy as np
import pandas as pd

from app.evaluation.baselines import (
    OBJECTIVE_COLUMNS,
    objective_matrix,
    query_weight_vector,
    rank_semantic_only,
    rank_weighted_sum,
    rank_random,
)
from app.evaluation.metrics import evaluate_ranking
from app.evaluation.query_suite import QUERY_SUITE
from app.recommendation.lea_optimizer import LotusEffectOptimizer
from scripts.evaluate_lea_recommender import build_candidate_pool, load_materials


def _rank_mmr(
    candidates: List[Dict],
    weights: Dict[str, float],
    top_k: int,
    lambda_relevance: float = 0.75,
) -> List[Dict]:
    matrix = objective_matrix(candidates)
    weight_vector = query_weight_vector(weights)
    relevance = matrix @ weight_vector
    selected: List[int] = []
    remaining = set(range(len(candidates)))

    while remaining and len(selected) < top_k:
        best_idx = None
        best_score = -np.inf
        for idx in remaining:
            if selected:
                similarities = [
                    1.0 / (1.0 + float(np.linalg.norm(matrix[idx] - matrix[j])))
                    for j in selected
                ]
                redundancy = max(similarities)
            else:
                redundancy = 0.0
            score = lambda_relevance * float(relevance[idx]) - (1.0 - lambda_relevance) * redundancy
            if score > best_score:
                best_score = score
                best_idx = idx
        selected.append(int(best_idx))
        remaining.remove(int(best_idx))

    ranked = []
    for rank, idx in enumerate(selected, start=1):
        item = dict(candidates[idx])
        item["rank"] = rank
        item["method"] = "MMR"
        item["baseline_score"] = round(float(relevance[idx]), 6)
        ranked.append(item)
    return ranked


@dataclass
class LEAConfig:
    label: str
    population_size: int = 30
    iterations: int = 60
    balance_weight: float = 0.12
    diversity_weight: float = 0.08
    self_cleaning: bool = True
    candidate_pool_size: int = 100


class ConfigurableLEA(LotusEffectOptimizer):
    def __init__(self, config: LEAConfig, top_k: int, seed: int):
        super().__init__(
            population_size=config.population_size,
            max_iterations=config.iterations,
            top_k=top_k,
            seed=seed,
        )
        self.config = config

    def _fitness(self, individual, candidate_matrix, objective_weights, selected_vectors):
        candidate_idx = self._nearest_candidate(individual, candidate_matrix)
        objectives = candidate_matrix[candidate_idx]
        weighted_score = float(np.dot(objectives, objective_weights))
        balance_score = float(np.min(objectives))
        diversity_score = 0.0
        if selected_vectors:
            diversity_score = float(
                np.mean([np.linalg.norm(objectives - selected) for selected in selected_vectors])
            )
        fitness = (
            weighted_score
            + self.config.balance_weight * balance_score
            + self.config.diversity_weight * diversity_score
        )
        return fitness, candidate_idx

    def _self_cleaning(self, population, fitnesses):
        if self.config.self_cleaning:
            super()._self_cleaning(population, fitnesses)


def _extra_metrics(ranked: List[Dict], pool: List[Dict]) -> Dict[str, float]:
    matrix = objective_matrix(ranked)
    pool_matrix = objective_matrix(pool)
    if len(ranked) == 0:
        return {"coverage": 0.0, "novelty": 0.0}
    unique_ids = {str(item.get("qmof_id", idx)) for idx, item in enumerate(ranked)}
    coverage = len(unique_ids) / len(ranked)
    centroid = np.mean(pool_matrix, axis=0)
    novelty = float(np.mean(np.linalg.norm(matrix - centroid, axis=1)))
    return {"coverage": coverage, "novelty": novelty}


def _run_variant(
    variant: Dict,
    pool: List[Dict],
    weights: Dict[str, float],
    top_k: int,
    seed: int,
) -> Tuple[List[Dict], float, List[float]]:
    started = time.perf_counter()
    history: List[float] = []
    kind = variant["kind"]

    if kind == "semantic":
        ranked = rank_semantic_only(pool, top_k)
    elif kind == "weighted":
        ranked = rank_weighted_sum(pool, weights, top_k)
    elif kind == "random":
        ranked = rank_random(pool, top_k, seed)
    elif kind == "mmr":
        ranked = _rank_mmr(pool, weights, top_k)
    elif kind == "lea":
        optimizer = ConfigurableLEA(variant["config"], top_k=top_k, seed=seed)
        ranked = optimizer.rank(pool, weights, top_k=top_k)
        history = optimizer.fitness_history
        for item in ranked:
            item["method"] = variant["label"]
            item["rank"] = item.get("lea_rank", item.get("rank"))
    else:
        raise ValueError(f"Unknown variant kind: {kind}")

    runtime_ms = (time.perf_counter() - started) * 1000.0
    return ranked, runtime_ms, history


def _variants() -> List[Dict]:
    variants: List[Dict] = [
        {"label": "SemanticOnly", "kind": "semantic", "candidate_pool_size": 100},
        {"label": "WeightedSum", "kind": "weighted", "candidate_pool_size": 100},
        {"label": "MMR", "kind": "mmr", "candidate_pool_size": 100},
        {"label": "RandomRepeated", "kind": "random", "candidate_pool_size": 100},
    ]
    configs = [
        LEAConfig("LEA baseline"),
        LEAConfig("LEA no diversity", diversity_weight=0.0),
        LEAConfig("LEA no balance", balance_weight=0.0),
        LEAConfig("LEA no self-cleaning", self_cleaning=False),
        LEAConfig("LEA pop20", population_size=20),
        LEAConfig("LEA pop50", population_size=50),
        LEAConfig("LEA pop100", population_size=100),
        LEAConfig("LEA iter20", iterations=20),
        LEAConfig("LEA iter40", iterations=40),
        LEAConfig("LEA iter100", iterations=100),
        LEAConfig("LEA pool50", candidate_pool_size=50),
        LEAConfig("LEA pool200", candidate_pool_size=200),
    ]
    for config in configs:
        variants.append(
            {
                "label": config.label,
                "kind": "lea",
                "config": config,
                "candidate_pool_size": config.candidate_pool_size,
            }
        )
    return variants


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, default=Path("backend/vector_db/metadata.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("reports/full_rerun/ablation"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--seed-start", type=int, default=42)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    materials = load_materials(args.metadata)
    metric_rows = []
    runtime_rows = []
    command = "PYTHONPATH=backend python3 backend/scripts/evaluate_lea_ablation.py " + " ".join(
        [
            f"--metadata {args.metadata}",
            f"--out-dir {args.out_dir}",
            f"--top-k {args.top_k}",
            f"--seeds {args.seeds}",
            f"--seed-start {args.seed_start}",
        ]
    )

    for seed_offset in range(args.seeds):
        seed = args.seed_start + seed_offset
        for query_index, query in enumerate(QUERY_SUITE):
            pools: Dict[int, List[Dict]] = {}
            for variant in _variants():
                pool_size = int(variant["candidate_pool_size"])
                if pool_size not in pools:
                    pools[pool_size] = build_candidate_pool(materials, query, pool_size)
                pool = pools[pool_size]
                ranked, runtime_ms, _ = _run_variant(
                    variant=variant,
                    pool=pool,
                    weights=query["weights"],
                    top_k=args.top_k,
                    seed=seed + query_index,
                )
                metrics = evaluate_ranking(ranked, pool, query["weights"], args.top_k)
                metrics.update(_extra_metrics(ranked, pool))
                row = {
                    "seed": seed,
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "variant": variant["label"],
                    "candidate_pool_size": pool_size,
                    "runtime_ms": runtime_ms,
                    **metrics,
                }
                metric_rows.append(row)
                runtime_rows.append(
                    {
                        "seed": seed,
                        "query_id": query["query_id"],
                        "variant": variant["label"],
                        "runtime_ms": runtime_ms,
                    }
                )

    metrics_df = pd.DataFrame(metric_rows)
    runtime_df = pd.DataFrame(runtime_rows)
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
            coverage_std=("coverage", "std"),
            novelty_mean=("novelty", "mean"),
            novelty_std=("novelty", "std"),
            hypervolume_proxy_mean=("hypervolume_proxy", "mean"),
            hypervolume_proxy_std=("hypervolume_proxy", "std"),
            runtime_ms_mean=("runtime_ms", "mean"),
            runtime_ms_std=("runtime_ms", "std"),
            runs=("runtime_ms", "count"),
        )
        .reset_index()
    )

    metrics_df.to_csv(args.out_dir / "ablation_metrics.csv", index=False)
    summary.to_csv(args.out_dir / "ablation_summary.csv", index=False)
    runtime_df.to_csv(args.out_dir / "ablation_runtime.csv", index=False)
    with (args.out_dir / "run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "command": command,
                "seeds": list(range(args.seed_start, args.seed_start + args.seeds)),
                "top_k": args.top_k,
                "query_count": len(QUERY_SUITE),
                "notes": [
                    "MMR is implemented directly from objective vectors.",
                    "NSGA-II was not included because no evolutionary NSGA-II implementation exists in the repository; ParetoCrowding remains the deterministic Pareto-style comparator.",
                    "Coverage is the fraction of unique QMOF identifiers in the top-K list.",
                    "Novelty is the mean Euclidean distance of selected objective vectors from the candidate-pool centroid.",
                ],
            },
            handle,
            indent=2,
        )
    print(f"Wrote ablation outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
