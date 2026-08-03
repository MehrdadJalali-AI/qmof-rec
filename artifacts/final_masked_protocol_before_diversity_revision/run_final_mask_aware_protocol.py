#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.recommendation.dynamic_weight_engine import dynamic_weight_engine
from app.recommendation.hybrid_ranker import hybrid_ranker
from app.recommendation.objective_utils import (
    ACTIVE_OBJECTIVES,
    EPSILON,
    WEIGHT_KEYS,
    masked_balance_score,
    masked_distance,
    masked_weighted_sum,
    normalize_weights,
)

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover - plotting is optional in minimal envs.
    plt = None


ARTIFACTS = ROOT / "artifacts"
FINAL = ARTIFACTS / "final_masked_protocol"
COMPARISON = ARTIFACTS / "protocol_comparison"
HISTORICAL = ARTIFACTS / "historical_protocol"


@dataclass
class MethodResult:
    method: str
    ranked: list[dict[str, Any]]
    runtime_ms: float
    history: list[float]


def finite_float(value: Any, default: float | None = None) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return number


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def archive_historical() -> None:
    HISTORICAL.mkdir(parents=True, exist_ok=True)
    files = [
        "manuscript/lea_evaluation/aggregate_metrics.csv",
        "manuscript/lea_evaluation/summary_metrics.csv",
        "manuscript/lea_evaluation/top_rankings.csv",
        "manuscript/lea_evaluation/lea_convergence.csv",
        "manuscript/reviewer_revision_artifacts/ablation_metrics.csv",
        "manuscript/reviewer_revision_artifacts/query_stratified_seed_results.csv",
        "manuscript/reviewer_revision_artifacts/candidate_pool_size_summary.csv",
        "manuscript/reviewer_revision_artifacts/lea_no_diversity_metric_identity.csv",
        "manuscript/reviewer_revision_artifacts/variance_decomposition.csv",
        "manuscript/reviewer_revision_artifacts/per_query_method_summary.csv",
        "manuscript/reviewer_revision_artifacts/descriptor_coverage_audit.csv",
        "manuscript/reviewer_revision_artifacts/all_vs_selected_objective_summary.csv",
        "manuscript/reviewer_revision_artifacts/method_difference_variance_summary.csv",
        "manuscript/reviewer_revision_artifacts/retrieval_serialization_sample.csv",
        "manuscript/reviewer_revision_artifacts/environment_snapshot.json",
        "manuscript/reviewer_revision_artifacts/input_summary_metrics_snapshot.csv",
        "manuscript/figures/figure_3_metric_comparison.png",
        "manuscript/figures/figure_4_runtime_log.png",
        "manuscript/figures/figure_5_lea_convergence.png",
        "manuscript/figures/figure_6_objective_radar.png",
    ]
    audit = []
    for rel in files:
        source = ROOT / rel
        if not source.exists():
            continue
        target = HISTORICAL / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
            target.chmod(0o444)
        audit.append(
            {
                "artifact": rel,
                "script": "historical saved artifact; original runner not present in final checkout",
                "configuration": "see manuscript/final_configuration.json and manuscript/protocol_audit.csv",
                "queries": "five manuscript query scenarios",
                "seeds": "seed 42 for primary single-run; 42-51 where repeated-seed artifact exists",
                "candidate_pool_size": "100 primary; 50/100/200 sensitivity where available",
                "top_k": 5,
                "mask_aware": "no; historical protocol preserved for comparison",
                "void_fraction_active": "historical CSV carries porosity_score=0.0 but final text excluded physical porosity claims",
                "contains_topk_ids": "yes" if "top_rankings" in rel else "no",
                "notes": "read-only copy under artifacts/historical_protocol",
            }
        )
    write_csv(
        COMPARISON / "historical_protocol_audit.csv",
        audit,
        [
            "artifact",
            "script",
            "configuration",
            "queries",
            "seeds",
            "candidate_pool_size",
            "top_k",
            "mask_aware",
            "void_fraction_active",
            "contains_topk_ids",
            "notes",
        ],
    )


def load_metadata(path: Path) -> list[dict[str, Any]]:
    with path.open() as handle:
        data = json.load(handle)
    clean = []
    for row in data:
        clean.append(
            {
                "qmof_id": row.get("qmof_id"),
                "formula": row.get("formula") or "",
                "band_gap": finite_float(row.get("band_gap")),
                "density": finite_float(row.get("density")),
                "void_fraction": finite_float(row.get("void_fraction")),
                "text": row.get("text") or "",
            }
        )
    return clean


def formula_counts(formula: str) -> Counter:
    import re

    counts: Counter = Counter()
    for element, count in re.findall(r"([A-Z][a-z]?)([0-9.]*)", formula or ""):
        counts[element] += float(count or 1.0)
    return counts


def semantic_proxy(row: dict[str, Any], query_id: str, query: str) -> float:
    text = f"{row.get('text','')} {row.get('formula','')}".lower()
    q_tokens = [tok for tok in query.lower().replace("-", " ").split() if len(tok) > 2]
    overlap = sum(1 for tok in q_tokens if tok in text) / max(1, len(q_tokens))
    counts = formula_counts(row.get("formula", ""))
    band = finite_float(row.get("band_gap"))
    density = finite_float(row.get("density"))
    score = 0.35 + 0.20 * overlap
    if query_id == "q1_co2_adsorption":
        score += 0.18 if counts.get("Co", 0) > 0 else 0.0
        score += 0.08 if density is not None and density < 1.8 else 0.0
        score += 0.04 if band is not None else 0.0
    elif query_id == "q2_photocatalysis":
        score += 0.22 if band is not None and 1.0 <= band <= 3.5 else 0.0
        score += 0.04 if any(counts.get(el, 0) for el in ("Ti", "Zn", "Cd", "Cu")) else 0.0
    elif query_id == "q3_lightweight_storage":
        score += 0.25 if density is not None and density < 1.0 else 0.0
        score += 0.10 if density is not None and density < 1.5 else 0.0
    elif query_id == "q4_balanced_discovery":
        score += 0.10 if band is not None else 0.0
        score += 0.10 if density is not None and density < 2.0 else 0.0
        score += 0.05 if len(counts) >= 4 else 0.0
    elif query_id == "q5_insulating_frameworks":
        score += 0.25 if band is not None and band >= 3.5 else 0.0
        score += 0.08 if density is not None and density < 2.0 else 0.0
    return round(max(0.0, min(1.0, score)), 6)


def graph_proxy(row: dict[str, Any], flavor: str) -> float:
    counts = formula_counts(row.get("formula", ""))
    total = sum(counts.values()) or 1.0
    hetero = sum(v for k, v in counts.items() if k not in {"C", "H"}) / total
    metal = sum(v for k, v in counts.items() if k not in {"C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I"}) / total
    density = finite_float(row.get("density"), 2.0) or 2.0
    band = finite_float(row.get("band_gap"), 0.0) or 0.0
    if flavor == "gat":
        raw = 0.45 * hetero + 0.30 * min(1.0, band / 5.0) + 0.25 * max(0.0, 1.0 - density / 4.0)
    else:
        raw = 0.45 * metal + 0.25 * hetero + 0.30 * max(0.0, 1.0 - density / 4.0)
    return round(max(0.0, min(1.0, raw)), 6)


def score_record(row: dict[str, Any], query_id: str, query: str, weights: dict[str, float]) -> dict[str, Any]:
    semantic = semantic_proxy(row, query_id, query)
    scored = hybrid_ranker.compute_score(row, weights, semantic)
    availability = scored["availability"]
    scores = {
        "semantic_score": semantic,
        "band_gap_score": scored["band_gap_score"],
        "density_score": scored["density_score"],
        "stability_score": scored["stability_score"],
    }
    relevance = masked_weighted_sum(scores, weights, availability)
    active_values = np.array([scores[name] for name in ACTIVE_OBJECTIVES], dtype=np.float32)
    active_mask = np.array([availability[name.replace("_score", "")] for name in ACTIVE_OBJECTIVES], dtype=bool)
    return {
        **row,
        **scores,
        "availability": availability,
        "availability_mask": "|".join("1" if x else "0" for x in active_mask),
        "available_descriptors": ";".join(k for k, v in availability.items() if v),
        "band_gap_available": bool(availability["band_gap"]),
        "density_available": bool(availability["density"]),
        "void_fraction_available": False,
        "stability_available": bool(availability["stability"]),
        "relevance_score": relevance,
        "balance_score": masked_balance_score(active_values, active_mask),
        "graphsage_score": graph_proxy(row, "graphsage"),
        "gat_score": graph_proxy(row, "gat"),
    }


def objective_array(item: dict[str, Any], graph: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    vals = [item[name] for name in ACTIVE_OBJECTIVES]
    mask = [item["availability"][name.replace("_score", "")] for name in ACTIVE_OBJECTIVES]
    if graph == "graphsage":
        vals.append(item["graphsage_score"])
        mask.append(True)
    elif graph == "gat":
        vals.append(item["gat_score"])
        mask.append(True)
    return np.array(vals, dtype=np.float32), np.array(mask, dtype=bool)


def distance_items(a: dict[str, Any], b: dict[str, Any], graph: str | None = None) -> float:
    av, am = objective_array(a, graph)
    bv, bm = objective_array(b, graph)
    return masked_distance(av, bv, am, bm)


def rank_weighted(candidates: list[dict[str, Any]], weights: dict[str, float], graph: str | None = None) -> list[dict[str, Any]]:
    graph_weight = 0.15 if graph else 0.0
    rows = []
    for item in candidates:
        score = item["relevance_score"]
        if graph == "graphsage":
            score = (1 - graph_weight) * score + graph_weight * item["graphsage_score"]
        elif graph == "gat":
            score = (1 - graph_weight) * score + graph_weight * item["gat_score"]
        rows.append((score, item["semantic_score"], item["qmof_id"], item))
    return [item for *_rest, item in sorted(rows, reverse=True)]


def rank_topsis(candidates: list[dict[str, Any]], weights: dict[str, float]) -> list[dict[str, Any]]:
    w = np.array([normalize_weights(weights)[key] for key in WEIGHT_KEYS], dtype=np.float32)
    scored = []
    for item in candidates:
        vals, mask = objective_array(item)
        active = w * mask.astype(np.float32)
        if float(active.sum()) <= EPSILON:
            score = 0.0
        else:
            active = active / float(active.sum())
            ideal = np.ones_like(vals)
            anti = np.zeros_like(vals)
            d_pos = math.sqrt(float(np.sum(active * ((ideal - vals) ** 2))))
            d_neg = math.sqrt(float(np.sum(active * ((vals - anti) ** 2))))
            score = d_neg / (d_pos + d_neg + EPSILON)
        scored.append((score, item["semantic_score"], item["qmof_id"], item))
    return [item for *_rest, item in sorted(scored, reverse=True)]


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    av, am = objective_array(a)
    bv, bm = objective_array(b)
    joint = np.logical_and(am, bm)
    if not np.any(joint):
        return False
    return bool(np.all(av[joint] >= bv[joint]) and np.any(av[joint] > bv[joint]))


def rank_pareto(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scores = []
    for i, item in enumerate(candidates):
        dominated_by = sum(1 for j, other in enumerate(candidates) if i != j and dominates(other, item))
        crowd = np.mean([distance_items(item, other) for other in candidates if other is not item]) if len(candidates) > 1 else 0.0
        scores.append((-dominated_by, crowd, item["relevance_score"], item["qmof_id"], item))
    return [item for *_rest, item in sorted(scores, reverse=True)]


def rank_mmr(candidates: list[dict[str, Any]], lambda_rel: float = 0.7) -> list[dict[str, Any]]:
    remaining = list(candidates)
    selected: list[dict[str, Any]] = []
    while remaining:
        best = None
        best_score = -1e9
        for item in remaining:
            max_sim = 0.0
            if selected:
                max_sim = max(1.0 - distance_items(item, chosen) for chosen in selected)
            score = lambda_rel * item["relevance_score"] - (1.0 - lambda_rel) * max_sim
            if score > best_score:
                best_score = score
                best = item
        selected.append(best)
        remaining.remove(best)
    return selected


def rank_lea(
    candidates: list[dict[str, Any]],
    weights: dict[str, float],
    seed: int,
    config: dict[str, Any],
    gamma: float | None = None,
    self_clean: bool = True,
    graph: str | None = None,
) -> tuple[list[dict[str, Any]], list[float]]:
    rng = np.random.default_rng(seed)
    alpha = float(config["lea_alpha"])
    beta = float(config["lea_beta"])
    gamma = float(config["lea_gamma"] if gamma is None else gamma)
    penalty = float(config["redundancy_penalty"])
    iterations = int(config["lea_iterations"])
    pop_size = min(max(20, len(candidates)), int(config["lea_population_size"]))
    values = []
    masks = []
    for item in candidates:
        v, m = objective_array(item, graph)
        values.append(v)
        masks.append(m)
    matrix = np.vstack(values).astype(np.float32)
    mask_matrix = np.vstack(masks).astype(bool)
    w = np.array([normalize_weights(weights)[key] for key in WEIGHT_KEYS], dtype=np.float32)
    if graph:
        w = np.concatenate([w * 0.85, np.array([0.15], dtype=np.float32)])
    population = [matrix[i % len(matrix)].copy() for i in range(pop_size)]
    pop_masks = [mask_matrix[i % len(mask_matrix)].copy() for i in range(pop_size)]
    best_seen: dict[str, tuple[float, int]] = {}
    history = []
    selected_vectors: list[np.ndarray] = []
    selected_masks: list[np.ndarray] = []

    def nearest(individual: np.ndarray, mask: np.ndarray) -> int:
        joint = np.logical_and(mask_matrix, mask)
        counts = joint.sum(axis=1)
        diff = (matrix - individual) * joint
        distances = np.zeros(len(matrix), dtype=np.float32)
        observed = counts > 0
        distances[observed] = np.sqrt((diff[observed] * diff[observed]).sum(axis=1) / counts[observed])
        return int(np.argmin(distances))

    def fitness(idx: int) -> float:
        vals = matrix[idx]
        mask = mask_matrix[idx]
        active = w * mask.astype(np.float32)
        rel = 0.0 if float(active.sum()) <= EPSILON else float(np.dot(vals, active) / float(active.sum()))
        bal = masked_balance_score(vals, mask)
        div = 0.0
        red = 0.0
        if selected_vectors:
            sv = np.vstack(selected_vectors)
            sm = np.vstack(selected_masks)
            joint = np.logical_and(sm, mask)
            counts = joint.sum(axis=1)
            diff = (sv - vals) * joint
            distances = np.zeros(len(sv), dtype=np.float32)
            observed = counts > 0
            distances[observed] = np.sqrt((diff[observed] * diff[observed]).sum(axis=1) / counts[observed])
            div = float(np.mean(distances))
            red = float(np.exp(-div))
        return alpha * rel + beta * bal + gamma * div - penalty * red

    for iteration in range(iterations):
        fitnesses = []
        for p, pm in zip(population, pop_masks):
            idx = nearest(p, pm)
            fit = fitness(idx)
            fitnesses.append(fit)
            qid = str(candidates[idx]["qmof_id"])
            if qid not in best_seen or fit > best_seen[qid][0]:
                best_seen[qid] = (fit, idx)
        history.append(float(max(fitnesses)))
        best_vector = population[int(np.argmax(fitnesses))]
        progress = iteration / max(1, iterations)
        noise_scale = 0.20 * (1.0 - progress)
        population = [np.clip(p + rng.normal(0, noise_scale, size=len(p)) + progress * (best_vector - p), 0, 1) for p in population]
        if self_clean and iteration % int(config["self_clean_interval"]) == 0:
            replace_count = max(1, int(float(config["self_clean_fraction"]) * len(population)))
            for idx in np.argsort(fitnesses)[:replace_count]:
                population[int(idx)] = rng.random(len(population[int(idx)]))
        ordered = sorted(best_seen.values(), reverse=True)[: int(config["top_k"])]
        selected_vectors = [matrix[idx] for _, idx in ordered]
        selected_masks = [mask_matrix[idx] for _, idx in ordered]

    for idx, item in enumerate(candidates):
        qid = str(item["qmof_id"])
        if qid in best_seen:
            continue
        vals = matrix[idx]
        mask = mask_matrix[idx]
        active = w * mask.astype(np.float32)
        rel = 0.0 if float(active.sum()) <= EPSILON else float(np.dot(vals, active) / float(active.sum()))
        bal = masked_balance_score(vals, mask)
        div = 0.0
        if selected_vectors:
            sv = np.vstack(selected_vectors)
            sm = np.vstack(selected_masks)
            joint = np.logical_and(sm, mask)
            counts = joint.sum(axis=1)
            diff = (sv - vals) * joint
            distances = np.zeros(len(sv), dtype=np.float32)
            observed = counts > 0
            distances[observed] = np.sqrt((diff[observed] * diff[observed]).sum(axis=1) / counts[observed])
            div = float(np.mean(distances))
        best_seen[qid] = (alpha * rel + beta * bal + gamma * div, idx)

    ordered = sorted(best_seen.values(), reverse=True)
    ranked = []
    for fit, idx in ordered:
        item = dict(candidates[idx])
        item["lea_score"] = fit
        ranked.append(item)
    return ranked, history


def diversity(items: list[dict[str, Any]], graph: str | None = None) -> float:
    if len(items) < 2:
        return 0.0
    distances = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            distances.append(distance_items(items[i], items[j], graph))
    return float(np.mean(distances)) if distances else 0.0


def ndcg_at_k(items: list[dict[str, Any]], ideal_pool: list[dict[str, Any]], k: int) -> float:
    def dcg(vals: list[float]) -> float:
        return sum((2**v - 1.0) / math.log2(i + 2) for i, v in enumerate(vals))

    actual = dcg([item["relevance_score"] for item in items[:k]])
    ideal = dcg([item["relevance_score"] for item in sorted(ideal_pool, key=lambda x: x["relevance_score"], reverse=True)[:k]])
    return actual / ideal if ideal > EPSILON else 0.0


def metrics_for(method: str, query_id: str, query: str, seed: int, pool_size: int, ranked: list[dict[str, Any]], pool: list[dict[str, Any]], runtime_ms: float, graph: str | None = None) -> dict[str, Any]:
    top = ranked[:5]
    rel = float(np.mean([x["relevance_score"] for x in top])) if top else 0.0
    best = float(max([x["relevance_score"] for x in top])) if top else 0.0
    div = diversity(top, graph)
    mean_sem = float(np.mean([x["semantic_score"] for x in top])) if top else 0.0
    mean_bg = float(np.mean([x["band_gap_score"] for x in top])) if top else 0.0
    mean_den = float(np.mean([x["density_score"] for x in top])) if top else 0.0
    mean_stab = float(np.mean([x["stability_score"] for x in top])) if top else 0.0
    balance = float(np.mean([x["balance_score"] for x in top])) if top else 0.0
    return {
        "seed": seed,
        "query_id": query_id,
        "query": query,
        "method": method,
        "candidate_pool_size": pool_size,
        "runtime_ms": runtime_ms,
        "rel_at_5": rel,
        "best_relevance": best,
        "balance": balance,
        "diversity": div,
        "hypervolume_proxy": max(0.0, rel * div * mean_bg * mean_den * mean_stab),
        "ndcg_at_5": ndcg_at_k(top, pool, 5),
        "mean_semantic_score": mean_sem,
        "mean_band_gap_score": mean_bg,
        "mean_density_score": mean_den,
        "mean_porosity_score": 0.0,
        "mean_stability_score": mean_stab,
        "coverage": len({x["qmof_id"] for x in top}) / 5.0 if top else 0.0,
        "missing_band_gap_top5": sum(not x["band_gap_available"] for x in top),
    }


def candidate_pool(scored: list[dict[str, Any]], query_id: str, query: str, seed: int, pool_size: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows = sorted(
        scored,
        key=lambda r: (r["semantic_score"], r["relevance_score"], rng.random()),
        reverse=True,
    )
    return rows[:pool_size]


def run_protocol(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    metadata = load_metadata(BACKEND / "vector_db" / "metadata.json")
    methods_main = ["SemanticOnly", "WeightedSum", "TOPSIS", "ParetoCrowding", "Random", "MMR", "LEA"]
    methods_extra = ["LEA no diversity", "LEA no self-cleaning", "GraphSAGE only", "GAT only", "LEA + GraphSAGE", "LEA + GAT"]
    ranking_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    pool_rows: list[dict[str, Any]] = []
    convergence_rows: list[dict[str, Any]] = []
    sensitivity_rows: list[dict[str, Any]] = []
    main_pool = int(config["main_candidate_pool_size"])
    top_k = int(config["top_k"])

    for query_def in config["query_scenarios"]:
        query_id = query_def["query_id"]
        query = query_def["query"]
        weights = dynamic_weight_engine.generate_weights(query)
        scored = [score_record(row, query_id, query, weights) for row in metadata]
        for seed in config["random_seeds"]:
            pools_by_size = {size: candidate_pool(scored, query_id, query, seed, int(size)) for size in config["candidate_pool_sizes"]}
            pool = pools_by_size[main_pool]
            pool_file_rows = []
            for rank, item in enumerate(pool, start=1):
                row = {
                    "query": query,
                    "query_id": query_id,
                    "seed": seed,
                    "candidate_rank": rank,
                    "qmof_id": item["qmof_id"],
                    "semantic_score": item["semantic_score"],
                    "available_descriptors": item["available_descriptors"],
                    "availability_mask": item["availability_mask"],
                }
                pool_rows.append(row)
                pool_file_rows.append(row)
            write_csv(FINAL / "candidate_pools" / f"{query_id}_seed{seed}_pool{main_pool}.csv", pool_file_rows)

            method_rankings: dict[str, MethodResult] = {}
            for method in methods_main + methods_extra:
                start = time.perf_counter()
                history: list[float] = []
                graph = None
                if method == "SemanticOnly":
                    ranked = sorted(pool, key=lambda x: (x["semantic_score"], x["qmof_id"]), reverse=True)
                elif method == "WeightedSum":
                    ranked = rank_weighted(pool, weights)
                elif method == "TOPSIS":
                    ranked = rank_topsis(pool, weights)
                elif method == "ParetoCrowding":
                    ranked = rank_pareto(pool)
                elif method == "Random":
                    ranked = list(pool)
                    random.Random(seed).shuffle(ranked)
                elif method == "MMR":
                    ranked = rank_mmr(pool)
                elif method == "LEA":
                    ranked, history = rank_lea(pool, weights, seed, config)
                elif method == "LEA no diversity":
                    ranked, history = rank_lea(pool, weights, seed, config, gamma=0.0)
                elif method == "LEA no self-cleaning":
                    ranked, history = rank_lea(pool, weights, seed, config, self_clean=False)
                elif method == "GraphSAGE only":
                    graph = "graphsage"
                    ranked = rank_weighted(pool, weights, graph=graph)
                elif method == "GAT only":
                    graph = "gat"
                    ranked = rank_weighted(pool, weights, graph=graph)
                elif method == "LEA + GraphSAGE":
                    graph = "graphsage"
                    ranked, history = rank_lea(pool, weights, seed, config, graph=graph)
                elif method == "LEA + GAT":
                    graph = "gat"
                    ranked, history = rank_lea(pool, weights, seed, config, graph=graph)
                else:
                    ranked = []
                runtime_ms = (time.perf_counter() - start) * 1000
                method_rankings[method] = MethodResult(method, ranked, runtime_ms, history)
                metric_rows.append(metrics_for(method, query_id, query, seed, main_pool, ranked, pool, runtime_ms, graph=graph))
                for iteration, value in enumerate(history, start=1):
                    convergence_rows.append({"query_id": query_id, "query": query, "seed": seed, "method": method, "iteration": iteration, "best_fitness": value})
                out_rows = []
                for rank, item in enumerate(ranked[:top_k], start=1):
                    row = {
                        "query": query,
                        "query_id": query_id,
                        "seed": seed,
                        "method": method,
                        "rank": rank,
                        "qmof_id": item["qmof_id"],
                        "formula": item["formula"],
                        "semantic_score": item["semantic_score"],
                        "band_gap": item["band_gap"],
                        "band_gap_available": item["band_gap_available"],
                        "density": item["density"],
                        "density_available": item["density_available"],
                        "stability_score": item["stability_score"],
                        "graph_score": item["graphsage_score"] if graph == "graphsage" else item["gat_score"] if graph == "gat" else "",
                        "availability_mask": item["availability_mask"],
                        "relevance_score": item["relevance_score"],
                        "balance_score": item["balance_score"],
                        "diversity_contribution": diversity(ranked[:rank], graph) if rank > 1 else 0.0,
                        "final_score": item.get("lea_score", item["relevance_score"]),
                        "runtime_ms": runtime_ms,
                    }
                    ranking_rows.append(row)
                    out_rows.append(row)
                write_csv(FINAL / "rankings" / f"{query_id}_seed{seed}_{method.replace(' ', '_').replace('+', 'plus')}.csv", out_rows)

            ws = method_rankings["WeightedSum"].ranked[:top_k]
            lea_no = method_rankings["LEA no diversity"].ranked[:top_k]
            sensitivity_rows.append(weighted_sum_vs_lea_no_diversity(query_id, query, seed, ws, lea_no))

            for pool_size, pool_variant in pools_by_size.items():
                start = time.perf_counter()
                lea_ranked, _ = rank_lea(pool_variant, weights, seed, config)
                runtime = (time.perf_counter() - start) * 1000
                sensitivity_rows.append({
                    "record_type": "candidate_pool_sensitivity",
                    **metrics_for("LEA", query_id, query, seed, int(pool_size), lea_ranked, pool_variant, runtime),
                    "unique_top_k_candidates": len({x["qmof_id"] for x in lea_ranked[:top_k]}),
                    "candidate_coverage": len({x["qmof_id"] for x in pool_variant}) / len(metadata),
                    "top_k_stability": "",
                    "retrieval_time_ms": 0.0,
                    "reranking_time_ms": runtime,
                    "total_runtime_ms": runtime,
                })
    return ranking_rows, metric_rows, pool_rows, convergence_rows, sensitivity_rows


def weighted_sum_vs_lea_no_diversity(query_id: str, query: str, seed: int, ws: list[dict[str, Any]], lea_no: list[dict[str, Any]]) -> dict[str, Any]:
    ws_ids = [x["qmof_id"] for x in ws]
    lea_ids = [x["qmof_id"] for x in lea_no]
    overlap = len(set(ws_ids) & set(lea_ids)) / max(1, len(ws_ids))
    return {
        "record_type": "weighted_sum_vs_lea_no_diversity",
        "query": query,
        "query_id": query_id,
        "seed": seed,
        "same_topk_set": set(ws_ids) == set(lea_ids),
        "same_order": ws_ids == lea_ids,
        "topk_overlap": overlap,
        "same_rel": abs(np.mean([x["relevance_score"] for x in ws]) - np.mean([x["relevance_score"] for x in lea_no])) <= 1e-12,
        "same_ndcg": "",
        "same_diversity": abs(diversity(ws) - diversity(lea_no)) <= 1e-12,
        "same_scores": "",
        "notes": "list-level comparison from final mask-aware rerun",
    }


def aggregate(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        grouped[row["method"]].append(row)
    out = []
    for method, rows in sorted(grouped.items()):
        out.append(
            {
                "method": method,
                "runtime_ms": np.mean([r["runtime_ms"] for r in rows]),
                "rel_at_5": np.mean([r["rel_at_5"] for r in rows]),
                "best_relevance": np.mean([r["best_relevance"] for r in rows]),
                "balance": np.mean([r["balance"] for r in rows]),
                "diversity": np.mean([r["diversity"] for r in rows]),
                "hypervolume_proxy": np.mean([r["hypervolume_proxy"] for r in rows]),
                "ndcg_at_5": np.mean([r["ndcg_at_5"] for r in rows]),
                "mean_semantic_score": np.mean([r["mean_semantic_score"] for r in rows]),
                "mean_band_gap_score": np.mean([r["mean_band_gap_score"] for r in rows]),
                "mean_density_score": np.mean([r["mean_density_score"] for r in rows]),
                "mean_porosity_score": 0.0,
                "mean_stability_score": np.mean([r["mean_stability_score"] for r in rows]),
                "coverage": np.mean([r["coverage"] for r in rows]),
                "missing_band_gap_top5": np.mean([r["missing_band_gap_top5"] for r in rows]),
            }
        )
    return out


def query_stratified(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        grouped[(row["query_id"], row["method"])].append(row)
    out = []
    for (query_id, method), rows in sorted(grouped.items()):
        for metric in ["rel_at_5", "ndcg_at_5", "diversity", "runtime_ms"]:
            values = np.array([r[metric] for r in rows], dtype=float)
            out.append(
                {
                    "query_id": query_id,
                    "query": rows[0]["query"],
                    "method": method,
                    "metric": metric,
                    "mean": float(values.mean()),
                    "sd": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "n": len(values),
                }
            )
    return out


def variance_decomposition(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        by_method[row["method"]].append(row)
    for method, rows in sorted(by_method.items()):
        q_means = []
        within = []
        by_query: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            by_query[r["query_id"]].append(r["rel_at_5"])
        for vals in by_query.values():
            arr = np.array(vals)
            q_means.append(float(arr.mean()))
            within.append(float(arr.var(ddof=1)) if len(arr) > 1 else 0.0)
        out.append(
            {
                "method": method,
                "metric": "rel_at_5",
                "between_query_variance": float(np.var(q_means, ddof=1)) if len(q_means) > 1 else 0.0,
                "within_query_seed_variance": float(np.mean(within)) if within else 0.0,
                "variance_ratio_between_to_within": (float(np.var(q_means, ddof=1)) / (float(np.mean(within)) + EPSILON)) if within and len(q_means) > 1 else "",
                "n_queries": len(q_means),
                "n_observations": len(rows),
            }
        )
    return out


def comparisons(metric_rows: list[dict[str, Any]], ranking_rows: list[dict[str, Any]]) -> None:
    historical = read_csv(ROOT / "manuscript" / "lea_evaluation" / "aggregate_metrics.csv")
    final_agg = {r["method"]: r for r in aggregate([r for r in metric_rows if r["method"] in {"SemanticOnly", "WeightedSum", "TOPSIS", "ParetoCrowding", "Random", "MMR", "LEA"}])}
    old_by_method = {r["method"]: r for r in historical}
    rows = []
    for method, final in final_agg.items():
        old = old_by_method.get(method, {})
        rows.append(
            {
                "method": method,
                "historical_rel_at_5": old.get("mean_relevance", ""),
                "final_rel_at_5": final["rel_at_5"],
                "rel_difference": float(final["rel_at_5"]) - float(old["mean_relevance"]) if old.get("mean_relevance") else "",
                "historical_ndcg_at_5": old.get("ndcg_at_k", ""),
                "final_ndcg_at_5": final["ndcg_at_5"],
                "ndcg_difference": float(final["ndcg_at_5"]) - float(old["ndcg_at_k"]) if old.get("ndcg_at_k") else "",
                "historical_diversity": old.get("diversity", ""),
                "final_masked_diversity": final["diversity"],
                "diversity_difference": float(final["diversity"]) - float(old["diversity"]) if old.get("diversity") else "",
                "historical_runtime_ms": old.get("runtime_ms", ""),
                "final_runtime_ms": final["runtime_ms"],
                "runtime_difference_ms": float(final["runtime_ms"]) - float(old["runtime_ms"]) if old.get("runtime_ms") else "",
                "number_selected_missing_band_gap": final["missing_band_gap_top5"],
            }
        )
    write_csv(COMPARISON / "historical_vs_masked_metrics.csv", rows)

    old_top = read_csv(ROOT / "manuscript" / "lea_evaluation" / "top_rankings.csv")
    old_lookup = defaultdict(list)
    for r in old_top:
        old_lookup[(r.get("query_id"), r.get("method"))].append(r.get("qmof_id"))
    new_lookup = defaultdict(list)
    for r in ranking_rows:
        if int(r["seed"]) == 42 and r["method"] in {"SemanticOnly", "WeightedSum", "TOPSIS", "ParetoCrowding", "Random", "MMR", "LEA"}:
            new_lookup[(r["query_id"], r["method"])].append(r["qmof_id"])
    top_rows = []
    for key, new_ids in sorted(new_lookup.items()):
        old_ids = old_lookup.get(key, [])
        top_rows.append(
            {
                "query_id": key[0],
                "method": key[1],
                "historical_topk_ids": "|".join(old_ids),
                "final_topk_ids": "|".join(new_ids),
                "topk_overlap": len(set(old_ids) & set(new_ids)) / max(1, len(new_ids)),
                "positions_changed": sum(1 for i, qid in enumerate(new_ids) if i >= len(old_ids) or old_ids[i] != qid),
                "top_rank_changed": (old_ids[0] != new_ids[0]) if old_ids else "",
            }
        )
    write_csv(COMPARISON / "historical_vs_masked_topk.csv", top_rows)
    write_csv(FINAL / "topk_overlap_analysis.csv", top_rows)

    lea = final_agg.get("LEA", {})
    ws = final_agg.get("WeightedSum", {})
    with (COMPARISON / "protocol_change_report.md").open("w") as handle:
        handle.write("# Protocol Change Report\n\n")
        handle.write("The final mask-aware protocol was rerun from local QMOF vector metadata. Void fraction is unavailable for all records and is excluded from numerical ranking.\n\n")
        if lea and ws:
            handle.write(f"Final LEA Rel@5 = {lea['rel_at_5']:.4f}, NDCG@5 = {lea['ndcg_at_5']:.4f}, diversity = {lea['diversity']:.4f}.\n")
            handle.write(f"Final WeightedSum Rel@5 = {ws['rel_at_5']:.4f}, NDCG@5 = {ws['ndcg_at_5']:.4f}, diversity = {ws['diversity']:.4f}.\n\n")
            if lea["diversity"] > ws["diversity"] and lea["rel_at_5"] <= ws["rel_at_5"]:
                handle.write("Main conclusion: LEA retains a relevance-diversity trade-off advantage, while WeightedSum remains strongest or tied on the relevance-aligned objective.\n")
            else:
                handle.write("Main conclusion: the ranking trade-off should be interpreted from the final aggregate table; the historical conclusion is not automatically preserved.\n")


def write_audits() -> None:
    rows = [
        ("candidate generation", "scripts/run_final_mask_aware_protocol.py", "candidate_pool", "deterministic semantic proxy over metadata; identical pool reused across methods", True, True, "", "live FAISS retrieval audited separately"),
        ("live retrieval", "backend/scripts/build_vector_index.py; backend/app/rag/vector_store.py", "build_vector_database/retrieve", "SentenceTransformer metadata text embeddings in FAISS L2 index; unavailable fields serialized as unavailable/None", True, False, "", "offline rerun uses deterministic proxy for reproducibility"),
        ("availability masks", "backend/app/recommendation/hybrid_ranker.py", "HybridRanker.compute_score", "band_gap/density/stability availability recorded; void_fraction warning only", True, True, "backend/tests/test_missing_data_masks.py", ""),
        ("weighted relevance", "backend/app/recommendation/objective_utils.py", "masked_weighted_sum", "weights renormalized over observed dimensions", True, True, "backend/tests/test_missing_data_masks.py", ""),
        ("balance", "backend/app/recommendation/objective_utils.py", "masked_balance_score", "observed-objective evenness only", True, True, "backend/tests/test_missing_data_masks.py", ""),
        ("masked pairwise distance", "backend/app/recommendation/objective_utils.py", "masked_distance", "Euclidean RMS over jointly observed dimensions; no-overlap fallback 0.0", True, True, "backend/tests/test_missing_data_masks.py", ""),
        ("masked cosine similarity", "backend/app/recommendation/objective_utils.py", "masked_cosine", "cosine over jointly observed dimensions; no-overlap fallback 0.0", True, False, "backend/tests/test_missing_data_masks.py", ""),
        ("WeightedSum", "scripts/run_final_mask_aware_protocol.py", "rank_weighted", "sort by masked weighted relevance", True, True, "", ""),
        ("TOPSIS", "scripts/run_final_mask_aware_protocol.py", "rank_topsis", "masked closeness to active ideal", True, True, "", ""),
        ("ParetoCrowding", "scripts/run_final_mask_aware_protocol.py", "rank_pareto", "joint-observed dominance plus masked crowding", True, True, "", ""),
        ("SemanticOnly", "scripts/run_final_mask_aware_protocol.py", "semantic rank branch", "sort by deterministic semantic proxy", True, True, "", ""),
        ("Random", "scripts/run_final_mask_aware_protocol.py", "random branch", "seeded shuffle of shared candidate pool", True, True, "", ""),
        ("MMR", "scripts/run_final_mask_aware_protocol.py", "rank_mmr", "masked relevance with masked-distance redundancy", True, True, "", ""),
        ("LEA baseline", "scripts/run_final_mask_aware_protocol.py; backend/app/recommendation/lea_optimizer.py", "rank_lea/LotusEffectOptimizer", "LEA-style mutation, masked remapping, relevance, balance, and diversity", True, True, "backend/tests/test_missing_data_masks.py", ""),
        ("GraphSAGE-only ranking", "scripts/run_final_mask_aware_protocol.py", "graph_proxy/rank_weighted", "formula-derived metadata graph proxy; no full-record trained embeddings found", True, True, "", "not CIF-derived atomistic graph learning"),
        ("GAT-only ranking", "scripts/run_final_mask_aware_protocol.py", "graph_proxy/rank_weighted", "formula-derived metadata graph proxy; GAT file is future-extension stub", True, True, "", "not CIF-derived atomistic graph learning"),
        ("ranking metrics", "scripts/run_final_mask_aware_protocol.py", "metrics_for", "Rel@5, NDCG@5, masked diversity, coverage, runtime, hypervolume proxy", True, True, "", ""),
        ("query-level statistics", "scripts/run_final_mask_aware_protocol.py", "query_stratified/variance_decomposition", "query-stratified means and query-block variance reporting", True, True, "", ""),
        ("RAG/LLM evaluation", "backend/scripts/evaluate_rag_llm_quality.py", "evaluate", "not rerun by final ranking script; historical result requires separate revalidation if final top-K changes feed RAG", True, False, "", "recorded honestly in final audit"),
    ]
    write_csv(
        COMPARISON / "final_implementation_audit.csv",
        [
            {
                "component": r[0],
                "source_file": r[1],
                "function_or_class": r[2],
                "current_behavior": r[3],
                "mask_aware": r[4],
                "used_in_final_rerun": r[5],
                "test_file": r[6],
                "notes": r[7],
            }
            for r in rows
        ],
    )


def write_environment(config_path: Path, started: float) -> None:
    packages = {}
    for mod in ["numpy", "matplotlib"]:
        try:
            module = __import__(mod)
            packages[mod] = getattr(module, "__version__", "unknown")
        except Exception as exc:
            packages[mod] = f"unavailable: {exc}"
    try:
        git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        git_commit = "unavailable"
    elapsed = time.perf_counter() - started
    env = {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "git_commit": git_commit,
        "config": str(config_path),
        "elapsed_seconds": elapsed,
        "packages": packages,
    }
    (FINAL / "environment.txt").write_text(json.dumps(env, indent=2))
    (FINAL / "clean_clone_validation.txt").write_text(
        "Clean-clone validation was not executed by this local rerun. "
        "The final protocol script, focused tests, manuscript compile commands, "
        "and environment snapshot are recorded for a separate clean-clone check.\n"
    )


def plot_outputs(aggregate_rows: list[dict[str, Any]], convergence_rows: list[dict[str, Any]], sensitivity_rows: list[dict[str, Any]]) -> None:
    if plt is None:
        return
    fig_dir = FINAL / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    primary = [r for r in aggregate_rows if r["method"] in {"SemanticOnly", "WeightedSum", "TOPSIS", "ParetoCrowding", "Random", "MMR", "LEA"}]
    methods = [r["method"] for r in primary]
    x = np.arange(len(methods))
    plt.figure(figsize=(8, 4.8))
    plt.bar(x - 0.2, [r["rel_at_5"] for r in primary], width=0.2, label="Rel@5")
    plt.bar(x, [r["ndcg_at_5"] for r in primary], width=0.2, label="NDCG@5")
    plt.bar(x + 0.2, [r["diversity"] for r in primary], width=0.2, label="Diversity")
    plt.xticks(x, methods, rotation=30, ha="right")
    plt.ylim(0, 1.05)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(fig_dir / "figure_4_metric_comparison.png", dpi=300)
    plt.close()

    plt.figure(figsize=(7.2, 4.2))
    plt.bar(methods, [r["runtime_ms"] for r in primary])
    plt.yscale("log")
    plt.ylabel("Runtime (ms, log scale)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(fig_dir / "figure_5_runtime_log.png", dpi=300)
    plt.close()

    lea_conv = [r for r in convergence_rows if r["method"] == "LEA" and int(r["seed"]) == 42]
    plt.figure(figsize=(7.2, 4.2))
    for qid in sorted({r["query_id"] for r in lea_conv}):
        rows = [r for r in lea_conv if r["query_id"] == qid]
        plt.plot([r["iteration"] for r in rows], [r["best_fitness"] for r in rows], label=qid.replace("_", " "))
    plt.xlabel("Iteration")
    plt.ylabel("Best LEA fitness")
    plt.legend(frameon=False, fontsize=7)
    plt.tight_layout()
    plt.savefig(fig_dir / "figure_6_lea_convergence.png", dpi=300)
    plt.close()

    lea = next((r for r in primary if r["method"] == "LEA"), None)
    if lea:
        labels = ["Semantic", "Band gap", "Density", "Stability", "Diversity"]
        vals = [lea["mean_semantic_score"], lea["mean_band_gap_score"], lea["mean_density_score"], lea["mean_stability_score"], lea["diversity"]]
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        vals += vals[:1]
        angles += angles[:1]
        fig = plt.figure(figsize=(5.2, 5.2))
        ax = fig.add_subplot(111, polar=True)
        ax.plot(angles, vals)
        ax.fill(angles, vals, alpha=0.18)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 1)
        plt.tight_layout()
        plt.savefig(fig_dir / "figure_7_active_objective_radar.png", dpi=300)
        plt.close()

    sens = [r for r in sensitivity_rows if r.get("record_type") == "candidate_pool_sensitivity"]
    if sens:
        by_pool = defaultdict(list)
        for r in sens:
            by_pool[int(r["candidate_pool_size"])].append(r)
        pools = sorted(by_pool)
        plt.figure(figsize=(7.2, 4.2))
        plt.plot(pools, [np.mean([r["rel_at_5"] for r in by_pool[p]]) for p in pools], marker="o", label="Rel@5")
        plt.plot(pools, [np.mean([r["ndcg_at_5"] for r in by_pool[p]]) for p in pools], marker="o", label="NDCG@5")
        plt.plot(pools, [np.mean([r["diversity"] for r in by_pool[p]]) for p in pools], marker="o", label="Diversity")
        ax2 = plt.gca().twinx()
        ax2.plot(pools, [np.mean([r["total_runtime_ms"] for r in by_pool[p]]) for p in pools], marker="s", color="black", label="Runtime")
        plt.gca().set_xlabel("Candidate-pool size")
        plt.gca().set_ylabel("Quality metric")
        ax2.set_ylabel("Runtime (ms)")
        plt.tight_layout()
        plt.savefig(fig_dir / "figure_s_candidate_pool_sensitivity.png", dpi=300)
        plt.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs" / "final_mask_aware_protocol.json"))
    args = parser.parse_args()
    started = time.perf_counter()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text())
    for path in [FINAL, COMPARISON, HISTORICAL, FINAL / "rankings", FINAL / "candidate_pools"]:
        path.mkdir(parents=True, exist_ok=True)
    for path in [FINAL / "rankings", FINAL / "candidate_pools", FINAL / "figures"]:
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    archive_historical()
    write_audits()
    ranking_rows, metric_rows, pool_rows, convergence_rows, mixed_rows = run_protocol(config)
    ws_vs_lea = [r for r in mixed_rows if r.get("record_type") == "weighted_sum_vs_lea_no_diversity"]
    sensitivity = [r for r in mixed_rows if r.get("record_type") == "candidate_pool_sensitivity"]
    aggregate_rows = aggregate(metric_rows)
    write_csv(FINAL / "rankings_all_topk.csv", ranking_rows)
    write_csv(FINAL / "metrics_per_query_seed.csv", metric_rows)
    write_csv(FINAL / "aggregate_metrics.csv", aggregate_rows)
    write_csv(FINAL / "query_stratified_results.csv", query_stratified(metric_rows))
    write_csv(FINAL / "variance_decomposition.csv", variance_decomposition(metric_rows))
    write_csv(FINAL / "weighted_sum_vs_lea_no_diversity.csv", ws_vs_lea)
    write_csv(FINAL / "candidate_pool_sensitivity.csv", sensitivity)
    write_csv(FINAL / "lea_convergence.csv", convergence_rows)
    comparisons(metric_rows, ranking_rows)
    plot_outputs(aggregate_rows, convergence_rows, sensitivity)
    write_environment(config_path, started)
    print(f"Wrote final mask-aware protocol artifacts to {FINAL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
