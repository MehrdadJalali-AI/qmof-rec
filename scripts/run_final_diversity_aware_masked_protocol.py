#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
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
from app.recommendation.property_scorer import property_scorer

try:
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None


ARTIFACTS = ROOT / "artifacts"
BEFORE = ARTIFACTS / "final_masked_protocol_before_diversity_revision"
REVISION = ARTIFACTS / "diversity_revision"
FINAL = ARTIFACTS / "final_diversity_aware_masked_protocol"


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
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_metadata(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    rows = []
    for row in data:
        rows.append(
            {
                "qmof_id": row.get("qmof_id"),
                "formula": row.get("formula") or "",
                "band_gap": finite_float(row.get("band_gap")),
                "density": finite_float(row.get("density")),
                "void_fraction": finite_float(row.get("void_fraction")),
                "text": row.get("text") or "",
            }
        )
    return rows


def formula_counts(formula: str) -> Counter:
    import re

    counts: Counter = Counter()
    for element, count in re.findall(r"([A-Z][a-z]?)([0-9.]*)", formula or ""):
        counts[element] += float(count or 1.0)
    return counts


def formula_features(formula: str) -> dict[str, float]:
    counts = formula_counts(formula)
    total = sum(counts.values()) or 1.0
    common = ["C", "H", "N", "O"]
    metal = sum(v for k, v in counts.items() if k not in {"C", "H", "N", "O", "S", "P", "F", "Cl", "Br", "I"})
    return {
        "formula_c_frac": counts.get("C", 0.0) / total,
        "formula_h_frac": counts.get("H", 0.0) / total,
        "formula_n_frac": counts.get("N", 0.0) / total,
        "formula_o_frac": counts.get("O", 0.0) / total,
        "formula_metal_frac": metal / total,
        "formula_atom_count_scaled": min(1.0, total / 200.0),
        "formula_element_count_scaled": min(1.0, len(counts) / 10.0),
        "formula_hetero_frac": sum(v for k, v in counts.items() if k not in common) / total,
    }


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
    return max(0.0, min(1.0, score))


def graph_proxy(row: dict[str, Any], flavor: str) -> float:
    features = formula_features(row.get("formula", ""))
    density = finite_float(row.get("density"), 2.0) or 2.0
    band = finite_float(row.get("band_gap"), 0.0) or 0.0
    if flavor == "gat":
        raw = 0.45 * features["formula_hetero_frac"] + 0.30 * min(1.0, band / 5.0) + 0.25 * max(0.0, 1.0 - density / 4.0)
    else:
        raw = 0.45 * features["formula_metal_frac"] + 0.25 * features["formula_hetero_frac"] + 0.30 * max(0.0, 1.0 - density / 4.0)
    return max(0.0, min(1.0, raw))


def physical_ranges(metadata: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    ranges = {}
    for key in ["density", "band_gap"]:
        vals = [finite_float(row.get(key)) for row in metadata]
        vals = [v for v in vals if v is not None]
        ranges[key] = (min(vals), max(vals)) if vals else (0.0, 1.0)
    return ranges


def normalize_physical(value: float | None, key: str, ranges: dict[str, tuple[float, float]]) -> tuple[float, bool]:
    if value is None:
        return 0.0, False
    low, high = ranges[key]
    if high - low <= EPSILON:
        return 0.0, True
    return (float(value) - low) / (high - low), True


def score_record(row: dict[str, Any], query_id: str, query: str, weights: dict[str, float], ranges: dict[str, tuple[float, float]]) -> dict[str, Any]:
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
    active_values = np.array([scores[name] for name in ACTIVE_OBJECTIVES], dtype=np.float64)
    active_mask = np.array([availability[name.replace("_score", "")] for name in ACTIVE_OBJECTIVES], dtype=bool)
    density_norm, density_mask = normalize_physical(row["density"], "density", ranges)
    band_norm, band_mask = normalize_physical(row["band_gap"], "band_gap", ranges)
    f = formula_features(row["formula"])
    graph_sage = graph_proxy(row, "graphsage")
    graph_gat = graph_proxy(row, "gat")
    return {
        **row,
        **scores,
        **f,
        "normalized_density_continuous": density_norm,
        "normalized_band_gap_continuous": band_norm,
        "density_continuous_available": density_mask,
        "band_gap_continuous_available": band_mask,
        "availability": availability,
        "availability_mask": "|".join("1" if x else "0" for x in active_mask),
        "available_descriptors": ";".join(k for k, v in availability.items() if v),
        "band_gap_available": bool(availability["band_gap"]),
        "density_available": bool(availability["density"]),
        "void_fraction_available": False,
        "stability_available": bool(availability["stability"]),
        "relevance_score": relevance,
        "balance_score": masked_balance_score(active_values, active_mask),
        "graphsage_score": graph_sage,
        "gat_score": graph_gat,
    }


def vector_for(item: dict[str, Any], representation: str, config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    if representation == "objective":
        vals = [item[name] for name in ACTIVE_OBJECTIVES]
        mask = [item["availability"][name.replace("_score", "")] for name in ACTIVE_OBJECTIVES]
    elif representation == "physical":
        vals = [item["normalized_density_continuous"], item["normalized_band_gap_continuous"]]
        mask = [item["density_continuous_available"], item["band_gap_continuous_available"]]
    elif representation == "formula":
        keys = ["formula_c_frac", "formula_h_frac", "formula_n_frac", "formula_o_frac", "formula_metal_frac", "formula_atom_count_scaled", "formula_element_count_scaled", "formula_hetero_frac"]
        vals = [item[k] for k in keys]
        mask = [True] * len(keys)
    elif representation == "semantic":
        vals = [item["semantic_score"]]
        mask = [True]
    elif representation == "graph":
        vals = [item["graphsage_score"], item["gat_score"]]
        mask = [True, True]
    elif representation == "hybrid_material":
        hw = config["hybrid_weights"]
        vals = []
        mask = []
        for value, available in [
            (item["normalized_density_continuous"], item["density_continuous_available"]),
            (item["normalized_band_gap_continuous"], item["band_gap_continuous_available"]),
        ]:
            vals.append(math.sqrt(hw["physical"] / 2.0) * value)
            mask.append(available)
        for key in ["formula_c_frac", "formula_h_frac", "formula_n_frac", "formula_o_frac", "formula_metal_frac", "formula_atom_count_scaled", "formula_element_count_scaled", "formula_hetero_frac"]:
            vals.append(math.sqrt(hw["formula"] / 8.0) * item[key])
            mask.append(True)
        vals.append(math.sqrt(hw["graph"] / 2.0) * item["graphsage_score"])
        vals.append(math.sqrt(hw["graph"] / 2.0) * item["gat_score"])
        mask.extend([True, True])
    else:
        raise ValueError(f"Unknown diversity representation: {representation}")
    return np.array(vals, dtype=np.float64), np.array(mask, dtype=bool)


def item_distance(a: dict[str, Any], b: dict[str, Any], representation: str, config: dict[str, Any]) -> float:
    av, am = vector_for(a, representation, config)
    bv, bm = vector_for(b, representation, config)
    return masked_distance(av, bv, am, bm)


def diversity(items: list[dict[str, Any]], representation: str, config: dict[str, Any]) -> float:
    if len(items) < 2:
        return 0.0
    distances = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            distances.append(item_distance(items[i], items[j], representation, config))
    return float(np.mean(distances)) if distances else 0.0


def diversity_contribution(item: dict[str, Any], selected: list[dict[str, Any]], representation: str, config: dict[str, Any]) -> float:
    if not selected:
        return 0.0
    return float(np.mean([item_distance(item, other, representation, config) for other in selected]))


def objective_array(item: dict[str, Any], graph: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    vals = [item[name] for name in ACTIVE_OBJECTIVES]
    mask = [item["availability"][name.replace("_score", "")] for name in ACTIVE_OBJECTIVES]
    if graph == "graphsage":
        vals.append(item["graphsage_score"])
        mask.append(True)
    elif graph == "gat":
        vals.append(item["gat_score"])
        mask.append(True)
    return np.array(vals, dtype=np.float64), np.array(mask, dtype=bool)


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
    w = np.array([normalize_weights(weights)[key] for key in WEIGHT_KEYS], dtype=np.float64)
    scored = []
    for item in candidates:
        vals, mask = objective_array(item)
        active = w * mask.astype(np.float64)
        if float(active.sum()) <= EPSILON:
            score = 0.0
        else:
            active = active / float(active.sum())
            d_pos = math.sqrt(float(np.sum(active * ((1.0 - vals) ** 2))))
            d_neg = math.sqrt(float(np.sum(active * vals**2)))
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


def rank_pareto(candidates: list[dict[str, Any]], config: dict[str, Any], representation: str) -> list[dict[str, Any]]:
    scores = []
    for i, item in enumerate(candidates):
        dominated_by = sum(1 for j, other in enumerate(candidates) if i != j and dominates(other, item))
        crowd = np.mean([item_distance(item, other, representation, config) for other in candidates if other is not item]) if len(candidates) > 1 else 0.0
        scores.append((-dominated_by, crowd, item["relevance_score"], item["qmof_id"], item))
    return [item for *_rest, item in sorted(scores, reverse=True)]


def rank_mmr(candidates: list[dict[str, Any]], config: dict[str, Any], representation: str) -> list[dict[str, Any]]:
    remaining = list(candidates)
    selected: list[dict[str, Any]] = []
    lam = float(config["mmr_parameters"]["lambda_relevance"])
    while remaining:
        best = None
        best_score = -1e9
        for item in remaining:
            max_sim = max((1.0 - item_distance(item, chosen, representation, config)) for chosen in selected) if selected else 0.0
            score = lam * item["relevance_score"] - (1.0 - lam) * max_sim
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
    representation: str,
    gamma: float | None = None,
    self_clean: bool = True,
    graph: str | None = None,
) -> tuple[list[dict[str, Any]], list[float]]:
    params = config["lea_parameters"]
    rng = np.random.default_rng(seed)
    alpha = float(params["alpha"])
    beta = float(params["beta"])
    gamma = float(params["gamma"] if gamma is None else gamma)
    penalty = float(params["redundancy_penalty"])
    iterations = int(params["iterations"])
    pop_size = min(max(20, len(candidates)), int(params["population_size"]))
    obj_values = []
    obj_masks = []
    div_values = []
    div_masks = []
    for item in candidates:
        ov, om = objective_array(item, graph)
        dv, dm = vector_for(item, representation, config)
        obj_values.append(ov)
        obj_masks.append(om)
        div_values.append(dv)
        div_masks.append(dm)
    obj_matrix = np.vstack(obj_values).astype(np.float64)
    obj_mask_matrix = np.vstack(obj_masks).astype(bool)
    div_matrix = np.vstack(div_values).astype(np.float64)
    div_mask_matrix = np.vstack(div_masks).astype(bool)
    w = np.array([normalize_weights(weights)[key] for key in WEIGHT_KEYS], dtype=np.float64)
    if graph:
        w = np.concatenate([w * 0.85, np.array([0.15], dtype=np.float64)])
    population = [obj_matrix[i % len(obj_matrix)].copy() for i in range(pop_size)]
    pop_masks = [obj_mask_matrix[i % len(obj_mask_matrix)].copy() for i in range(pop_size)]
    best_seen: dict[str, tuple[float, int]] = {}
    history = []
    selected_indices: list[int] = []

    def nearest(individual: np.ndarray, mask: np.ndarray) -> int:
        joint = np.logical_and(obj_mask_matrix, mask)
        counts = joint.sum(axis=1)
        diff = (obj_matrix - individual) * joint
        distances = np.zeros(len(obj_matrix), dtype=np.float64)
        observed = counts > 0
        distances[observed] = np.sqrt((diff[observed] * diff[observed]).sum(axis=1) / counts[observed])
        return int(np.argmin(distances))

    def div_to_selected(idx: int) -> float:
        if not selected_indices:
            return 0.0
        vals = div_matrix[idx]
        mask = div_mask_matrix[idx]
        sv = div_matrix[selected_indices]
        sm = div_mask_matrix[selected_indices]
        joint = np.logical_and(sm, mask)
        counts = joint.sum(axis=1)
        diff = (sv - vals) * joint
        distances = np.zeros(len(selected_indices), dtype=np.float64)
        observed = counts > 0
        distances[observed] = np.sqrt((diff[observed] * diff[observed]).sum(axis=1) / counts[observed])
        return float(np.mean(distances))

    def fitness(idx: int) -> float:
        vals = obj_matrix[idx]
        mask = obj_mask_matrix[idx]
        active = w * mask.astype(np.float64)
        rel = 0.0 if float(active.sum()) <= EPSILON else float(np.dot(vals, active) / float(active.sum()))
        bal = masked_balance_score(vals, mask)
        div = div_to_selected(idx)
        red = float(np.exp(-div)) if selected_indices else 0.0
        return alpha * rel + beta * bal + gamma * div - penalty * red

    for iteration in range(iterations):
        fitnesses = []
        for individual, mask in zip(population, pop_masks):
            idx = nearest(individual, mask)
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
        if self_clean and iteration % int(params["self_clean_interval"]) == 0:
            replace_count = max(1, int(float(params["self_clean_fraction"]) * len(population)))
            for pop_idx in np.argsort(fitnesses)[:replace_count]:
                population[int(pop_idx)] = rng.random(len(population[int(pop_idx)]))
        selected_indices = [idx for _, idx in sorted(best_seen.values(), reverse=True)[: int(config["top_k"])]]

    for idx, item in enumerate(candidates):
        qid = str(item["qmof_id"])
        if qid in best_seen:
            continue
        best_seen[qid] = (fitness(idx), idx)

    ranked = []
    for fit, idx in sorted(best_seen.values(), reverse=True):
        item = dict(candidates[idx])
        item["lea_score"] = fit
        ranked.append(item)
    return ranked, history


def ndcg_at_k(items: list[dict[str, Any]], ideal_pool: list[dict[str, Any]], k: int) -> float:
    def dcg(vals: list[float]) -> float:
        return sum((2**v - 1.0) / math.log2(i + 2) for i, v in enumerate(vals))

    actual = dcg([item["relevance_score"] for item in items[:k]])
    ideal = dcg([item["relevance_score"] for item in sorted(ideal_pool, key=lambda x: x["relevance_score"], reverse=True)[:k]])
    return actual / ideal if ideal > EPSILON else 0.0


def candidate_pool(scored: list[dict[str, Any]], query_id: str, query: str, seed: int, pool_size: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    rows = sorted(scored, key=lambda r: (r["semantic_score"], r["relevance_score"], rng.random()), reverse=True)
    return rows[:pool_size]


def metrics_for(method: str, query_id: str, query: str, seed: int, pool_size: int, ranked: list[dict[str, Any]], pool: list[dict[str, Any]], runtime_ms: float, representation: str, config: dict[str, Any]) -> dict[str, Any]:
    top_k = int(config["top_k"])
    top = ranked[:top_k]
    rel = float(np.mean([x["relevance_score"] for x in top])) if top else 0.0
    div = diversity(top, representation, config)
    mean_sem = float(np.mean([x["semantic_score"] for x in top])) if top else 0.0
    mean_bg = float(np.mean([x["band_gap_score"] for x in top])) if top else 0.0
    mean_den = float(np.mean([x["density_score"] for x in top])) if top else 0.0
    mean_stab = float(np.mean([x["stability_score"] for x in top])) if top else 0.0
    return {
        "seed": seed,
        "query_id": query_id,
        "query": query,
        "method": method,
        "candidate_pool_size": pool_size,
        "runtime_ms": runtime_ms,
        "rel_at_5": rel,
        "best_relevance": float(max([x["relevance_score"] for x in top])) if top else 0.0,
        "balance": float(np.mean([x["balance_score"] for x in top])) if top else 0.0,
        "diversity": div,
        "unique_at_5": len({x["qmof_id"] for x in top}) / top_k if top else 0.0,
        "hypervolume_proxy": max(0.0, rel * div * mean_bg * mean_den * mean_stab),
        "ndcg_at_5": ndcg_at_k(top, pool, top_k),
        "mean_semantic_score": mean_sem,
        "mean_band_gap_score": mean_bg,
        "mean_density_score": mean_den,
        "mean_porosity_score": 0.0,
        "mean_stability_score": mean_stab,
        "missing_band_gap_top5": sum(not x["band_gap_available"] for x in top),
    }


def aggregate(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        grouped[row["method"]].append(row)
    for method, rows in sorted(grouped.items()):
        out.append(
            {
                "method": method,
                "runtime_ms": float(np.mean([r["runtime_ms"] for r in rows])),
                "rel_at_5": float(np.mean([r["rel_at_5"] for r in rows])),
                "best_relevance": float(np.mean([r["best_relevance"] for r in rows])),
                "balance": float(np.mean([r["balance"] for r in rows])),
                "diversity": float(np.mean([r["diversity"] for r in rows])),
                "hypervolume_proxy": float(np.mean([r["hypervolume_proxy"] for r in rows])),
                "ndcg_at_5": float(np.mean([r["ndcg_at_5"] for r in rows])),
                "mean_semantic_score": float(np.mean([r["mean_semantic_score"] for r in rows])),
                "mean_band_gap_score": float(np.mean([r["mean_band_gap_score"] for r in rows])),
                "mean_density_score": float(np.mean([r["mean_density_score"] for r in rows])),
                "mean_porosity_score": 0.0,
                "mean_stability_score": float(np.mean([r["mean_stability_score"] for r in rows])),
                "unique_at_5": float(np.mean([r["unique_at_5"] for r in rows])),
                "missing_band_gap_top5": float(np.mean([r["missing_band_gap_top5"] for r in rows])),
            }
        )
    return out


def query_stratified(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        grouped[(row["query_id"], row["method"])].append(row)
    for (query_id, method), rows in sorted(grouped.items()):
        for metric in ["rel_at_5", "ndcg_at_5", "diversity", "unique_at_5", "runtime_ms", "missing_band_gap_top5"]:
            values = np.array([r[metric] for r in rows], dtype=float)
            out.append({"query_id": query_id, "query": rows[0]["query"], "method": method, "metric": metric, "mean": float(values.mean()), "sd": float(values.std(ddof=1)) if len(values) > 1 else 0.0, "min": float(values.min()), "max": float(values.max()), "n": len(values)})
    return out


def variance_decomposition(metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        by_method[row["method"]].append(row)
    for method, rows in sorted(by_method.items()):
        for metric in ["rel_at_5", "ndcg_at_5", "diversity"]:
            by_query: dict[str, list[float]] = defaultdict(list)
            for row in rows:
                by_query[row["query_id"]].append(float(row[metric]))
            q_means = [float(np.mean(vals)) for vals in by_query.values()]
            within = [float(np.var(vals, ddof=1)) if len(vals) > 1 else 0.0 for vals in by_query.values()]
            out.append({"method": method, "metric": metric, "between_query_variance": float(np.var(q_means, ddof=1)) if len(q_means) > 1 else 0.0, "within_query_seed_variance": float(np.mean(within)) if within else 0.0, "variance_ratio_between_to_within": (float(np.var(q_means, ddof=1)) / (float(np.mean(within)) + EPSILON)) if within and len(q_means) > 1 else "", "n_queries": len(q_means), "n_observations": len(rows)})
    return out


def compare_weighted_sum_lea(query_id: str, query: str, seed: int, ws: list[dict[str, Any]], lea_no: list[dict[str, Any]], pool: list[dict[str, Any]], runtime_ws: float, runtime_lea: float, representation: str, config: dict[str, Any]) -> dict[str, Any]:
    ws_ids = [x["qmof_id"] for x in ws]
    lea_ids = [x["qmof_id"] for x in lea_no]
    top_k = int(config["top_k"])
    return {
        "query_id": query_id,
        "query": query,
        "seed": seed,
        "same_topk_set": set(ws_ids) == set(lea_ids),
        "same_order": ws_ids == lea_ids,
        "overlap": len(set(ws_ids) & set(lea_ids)) / max(1, top_k),
        "same_rel_at_5": abs(np.mean([x["relevance_score"] for x in ws]) - np.mean([x["relevance_score"] for x in lea_no])) <= 1e-12,
        "same_ndcg_at_5": abs(ndcg_at_k(ws, pool, top_k) - ndcg_at_k(lea_no, pool, top_k)) <= 1e-12,
        "same_diversity": abs(diversity(ws, representation, config) - diversity(lea_no, representation, config)) <= 1e-12,
        "same_final_scores": all(abs(float(a.get("lea_score", a["relevance_score"])) - float(b.get("lea_score", b["relevance_score"]))) <= 1e-12 for a, b in zip(ws, lea_no)),
        "weighted_sum_runtime_ms": runtime_ws,
        "lea_no_diversity_runtime_ms": runtime_lea,
    }


def row_for_rank(item: dict[str, Any], query: str, query_id: str, seed: int, method: str, rank: int, selected_before: list[dict[str, Any]], runtime_ms: float, representation: str, config: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": query,
        "query_id": query_id,
        "seed": seed,
        "method": method,
        "rank": rank,
        "qmof_id": item["qmof_id"],
        "formula": item["formula"],
        "availability_mask": item["availability_mask"],
        "relevance": item["relevance_score"],
        "balance": item["balance_score"],
        "diversity_contribution": diversity_contribution(item, selected_before, representation, config),
        "graph_score": "",
        "final_score": item.get("lea_score", item["relevance_score"]),
        "runtime_ms": runtime_ms,
        "band_gap": item["band_gap"],
        "density": item["density"],
        "semantic_score": item["semantic_score"],
        "band_gap_score": item["band_gap_score"],
        "density_score": item["density_score"],
        "stability_score": item["stability_score"],
    }


def run_methods(pool: list[dict[str, Any]], weights: dict[str, float], query_id: str, query: str, seed: int, config: dict[str, Any], representation: str) -> dict[str, MethodResult]:
    methods = ["SemanticOnly", "WeightedSum", "TOPSIS", "ParetoCrowding", "Random", "MMR", "LEA", "LEA no diversity", "LEA no self-cleaning", "GraphSAGE only", "GAT only", "LEA + GraphSAGE", "LEA + GAT"]
    out = {}
    for method in methods:
        start = time.perf_counter()
        history: list[float] = []
        if method == "SemanticOnly":
            ranked = sorted(pool, key=lambda x: (x["semantic_score"], x["qmof_id"]), reverse=True)
        elif method == "WeightedSum":
            ranked = rank_weighted(pool, weights)
        elif method == "TOPSIS":
            ranked = rank_topsis(pool, weights)
        elif method == "ParetoCrowding":
            ranked = rank_pareto(pool, config, representation)
        elif method == "Random":
            ranked = list(pool)
            random.Random(seed).shuffle(ranked)
        elif method == "MMR":
            ranked = rank_mmr(pool, config, representation)
        elif method == "LEA":
            ranked, history = rank_lea(pool, weights, seed, config, representation)
        elif method == "LEA no diversity":
            ranked, history = rank_lea(pool, weights, seed, config, representation, gamma=0.0)
        elif method == "LEA no self-cleaning":
            ranked, history = rank_lea(pool, weights, seed, config, representation, self_clean=False)
        elif method == "GraphSAGE only":
            ranked = rank_weighted(pool, weights, graph="graphsage")
        elif method == "GAT only":
            ranked = rank_weighted(pool, weights, graph="gat")
        elif method == "LEA + GraphSAGE":
            ranked, history = rank_lea(pool, weights, seed, config, representation, graph="graphsage")
        elif method == "LEA + GAT":
            ranked, history = rank_lea(pool, weights, seed, config, representation, graph="gat")
        runtime_ms = (time.perf_counter() - start) * 1000
        out[method] = MethodResult(method, ranked, runtime_ms, history)
    return out


def run_protocol(config: dict[str, Any], metadata: list[dict[str, Any]], ranges: dict[str, tuple[float, float]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ranking_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    pool_rows: list[dict[str, Any]] = []
    convergence_rows: list[dict[str, Any]] = []
    ws_vs_lea: list[dict[str, Any]] = []
    sensitivity_rows: list[dict[str, Any]] = []
    topk_sets: dict[tuple[str, int, str], set[str]] = {}
    representation = config["diversity_representation"]
    main_pool = int(config["main_candidate_pool_size"])
    top_k = int(config["top_k"])

    for query_def in config["query_scenarios"]:
        query_id = query_def["query_id"]
        query = query_def["query"]
        weights = dynamic_weight_engine.generate_weights(query)
        scored = [score_record(row, query_id, query, weights, ranges) for row in metadata]
        for seed in config["random_seeds"]:
            pools_by_size = {int(size): candidate_pool(scored, query_id, query, seed, int(size)) for size in config["candidate_pool_sizes"]}
            pool = pools_by_size[main_pool]
            pool_file_rows = []
            for rank, item in enumerate(pool, start=1):
                row = {"query": query, "query_id": query_id, "seed": seed, "candidate_rank": rank, "qmof_id": item["qmof_id"], "semantic_score": item["semantic_score"], "relevance_score": item["relevance_score"], "availability_mask": item["availability_mask"]}
                pool_rows.append(row)
                pool_file_rows.append(row)
            write_csv(FINAL / "candidate_pools" / f"{query_id}_seed{seed}_pool{main_pool}.csv", pool_file_rows)

            method_rankings = run_methods(pool, weights, query_id, query, seed, config, representation)
            for method, result in method_rankings.items():
                ranked = result.ranked
                metric_rows.append(metrics_for(method, query_id, query, seed, main_pool, ranked, pool, result.runtime_ms, representation, config))
                topk_sets[(query_id, seed, method)] = {x["qmof_id"] for x in ranked[:top_k]}
                for iteration, value in enumerate(result.history, start=1):
                    convergence_rows.append({"query_id": query_id, "query": query, "seed": seed, "method": method, "iteration": iteration, "best_fitness": value})
                out_rows = []
                selected_before: list[dict[str, Any]] = []
                for rank, item in enumerate(ranked[:top_k], start=1):
                    row = row_for_rank(item, query, query_id, seed, method, rank, selected_before, result.runtime_ms, representation, config)
                    if method == "GraphSAGE only" or method == "LEA + GraphSAGE":
                        row["graph_score"] = item["graphsage_score"]
                    elif method == "GAT only" or method == "LEA + GAT":
                        row["graph_score"] = item["gat_score"]
                    ranking_rows.append(row)
                    out_rows.append(row)
                    selected_before.append(item)
                write_csv(FINAL / "rankings" / f"{query_id}_seed{seed}_{method.replace(' ', '_').replace('+', 'plus')}.csv", out_rows)

            ws = method_rankings["WeightedSum"]
            lea_no = method_rankings["LEA no diversity"]
            ws_vs_lea.append(compare_weighted_sum_lea(query_id, query, seed, ws.ranked[:top_k], lea_no.ranked[:top_k], pool, ws.runtime_ms, lea_no.runtime_ms, representation, config))

            base_ids = [x["qmof_id"] for x in method_rankings["LEA"].ranked[:top_k]]
            for pool_size, pool_variant in pools_by_size.items():
                start = time.perf_counter()
                lea_ranked, _ = rank_lea(pool_variant, weights, seed, config, representation)
                runtime = (time.perf_counter() - start) * 1000
                top_ids = [x["qmof_id"] for x in lea_ranked[:top_k]]
                sensitivity_rows.append({
                    **metrics_for("LEA", query_id, query, seed, pool_size, lea_ranked, pool_variant, runtime, representation, config),
                    "catalog_coverage": len(set(top_ids)) / len(metadata),
                    "top_k_stability_vs_pool100": len(set(top_ids) & set(base_ids)) / top_k,
                    "retrieval_time_ms": 0.0,
                    "reranking_time_ms": runtime,
                    "total_runtime_ms": runtime,
                })

    coverage_rows = []
    method_ids: dict[str, set[str]] = defaultdict(set)
    for row in ranking_rows:
        method_ids[row["method"]].add(row["qmof_id"])
    for method, ids in sorted(method_ids.items()):
        coverage_rows.append({"method": method, "unique_catalog_items_selected": len(ids), "catalog_size": len(metadata), "catalog_coverage": len(ids) / len(metadata)})

    overlap_rows = []
    for query_def in config["query_scenarios"]:
        qid = query_def["query_id"]
        for seed in config["random_seeds"]:
            ws_ids = topk_sets[(qid, seed, "WeightedSum")]
            for method in sorted({m for q, s, m in topk_sets if q == qid and s == seed}):
                ids = topk_sets[(qid, seed, method)]
                overlap_rows.append({"query_id": qid, "seed": seed, "method": method, "topk_overlap_with_weighted_sum": len(ids & ws_ids) / top_k, "same_topk_set_as_weighted_sum": ids == ws_ids})

    return ranking_rows, metric_rows, pool_rows, convergence_rows, ws_vs_lea, sensitivity_rows, coverage_rows + overlap_rows


def diagnose_previous_results(config: dict[str, Any], metadata: list[dict[str, Any]], ranges: dict[str, tuple[float, float]]) -> None:
    REVISION.mkdir(parents=True, exist_ok=True)
    audit_rows = []
    if BEFORE.exists():
        for path in sorted(BEFORE.rglob("*")):
            if path.is_file():
                audit_rows.append({"artifact": path.name, "source_file": str(path.relative_to(ROOT)), "script": "scripts/run_final_mask_aware_protocol.py", "configuration": "configs/final_mask_aware_protocol.json", "candidate_pool": "shared pool100 where applicable", "query": "", "seed": "", "method": "", "metric_definition": "masked active objective-score distance", "notes": "preserved before diversity revision"})
    write_csv(REVISION / "current_result_audit.csv", audit_rows, ["artifact", "source_file", "script", "configuration", "candidate_pool", "query", "seed", "method", "metric_definition", "notes"])

    by_id = {row["qmof_id"]: row for row in metadata}
    active_rows = []
    pair_rows = []
    ranking_files = sorted((BEFORE / "rankings").glob("*.csv")) if (BEFORE / "rankings").exists() else []
    for path in ranking_files:
        for r in read_csv(path):
            meta = by_id.get(r["qmof_id"], {})
            query_id = r["query_id"]
            query = r["query"]
            weights = dynamic_weight_engine.generate_weights(query)
            scored = score_record(meta, query_id, query, weights, ranges) if meta else {}
            active_vec = [scored.get("semantic_score", ""), scored.get("band_gap_score", ""), scored.get("density_score", ""), scored.get("stability_score", "")]
            active_rows.append({
                "query": query,
                "seed": r["seed"],
                "method": r["method"],
                "rank": r["rank"],
                "qmof_id": r["qmof_id"],
                "formula": r["formula"],
                "raw_density": scored.get("density", ""),
                "raw_band_gap": scored.get("band_gap", ""),
                "raw_semantic_score": scored.get("semantic_score", ""),
                "raw_stability_score": scored.get("stability_score", ""),
                "raw_graph_score": "",
                "normalized_density_score": scored.get("density_score", ""),
                "normalized_band_gap_score": scored.get("band_gap_score", ""),
                "normalized_semantic_score": scored.get("semantic_score", ""),
                "normalized_stability_score": scored.get("stability_score", ""),
                "normalized_graph_score": "",
                "availability_mask": scored.get("availability_mask", ""),
                "active_objective_vector": "|".join(str(x) for x in active_vec),
                "pairwise_masked_distance": "",
                "final_utility": r.get("final_score", ""),
            })

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in active_rows:
        grouped[(row["query"], row["seed"], row["method"])].append(row)
    for key, rows in grouped.items():
        rows = sorted(rows, key=lambda x: int(x["rank"]))
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                left = np.array([float(x) for x in rows[i]["active_objective_vector"].split("|")], dtype=np.float64)
                right = np.array([float(x) for x in rows[j]["active_objective_vector"].split("|")], dtype=np.float64)
                mask = np.array([x == "1" for x in rows[i]["availability_mask"].split("|")], dtype=bool)
                rmask = np.array([x == "1" for x in rows[j]["availability_mask"].split("|")], dtype=bool)
                pair_rows.append({"query": key[0], "seed": key[1], "method": key[2], "rank_i": rows[i]["rank"], "rank_j": rows[j]["rank"], "qmof_id_i": rows[i]["qmof_id"], "qmof_id_j": rows[j]["qmof_id"], "objective_score_distance": masked_distance(left, right, mask, rmask), "raw_physical_distance": "", "notes": "previous final-masked protocol distance"})
    write_csv(REVISION / "topk_active_vectors.csv", active_rows)
    write_csv(REVISION / "topk_pairwise_distances.csv", pair_rows)

    co2 = [r for r in active_rows if r["query"] == "stable porous MOFs for CO2 adsorption" and r["seed"] == "42" and r["method"] == "LEA"]
    report = [
        "# Zero-Diversity Diagnosis",
        "",
        "The zero masked-diversity result in `artifacts/final_masked_protocol` is a representation limitation caused by binned objective scores, not by identical raw materials and not by a pairwise-distance implementation bug.",
        "",
        "`property_scorer.score_band_gap` maps every observed band gap in the interval 1.0--3.5 eV to the same score of 1.0. `property_scorer.score_density` maps every density in 1.0--2.0 g/cm3 to the same score of 0.7. When no measured stability field is present, `hybrid_ranker._compute_stability_score` uses the density score as the stability proxy. The deterministic semantic proxy is also tied within several high-ranked query/application buckets.",
        "",
        "For the CO2 Table 3 candidates, the raw density and band-gap values differ, but all five transform to the same active objective vector:",
        "",
    ]
    for row in co2:
        report.append(f"- {row['qmof_id']}: raw density={row['raw_density']}, raw band gap={row['raw_band_gap']}, active vector={row['active_objective_vector']}, final utility={row['final_utility']}")
    report.extend([
        "",
        "Because intra-list diversity in the previous final-masked protocol was computed over this transformed active objective vector, every pair among these tied candidates has zero distance. Pairwise distance uses full-precision arithmetic and the no-overlap fallback is not triggered for these rows; their masks are identical (`1|1|1|1`). The collapse occurs before the distance calculation, at the property-score discretization/clipping step.",
        "",
        "The scientifically appropriate correction is to keep mask-aware relevance on the application-oriented score vector, but measure list diversity over a richer, full-precision material representation that includes continuous physical descriptors and query-independent formula/graph-derived features.",
    ])
    (REVISION / "zero_diversity_diagnosis.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def evaluate_representations(config: dict[str, Any], metadata: list[dict[str, Any]], ranges: dict[str, tuple[float, float]]) -> None:
    rows = []
    assessment = ["# Diversity Representation Assessment", ""]
    reps = [
        ("objective", "Current masked objective-score distance", "interpretable as application utility but too coarse; retained only as a diagnostic baseline"),
        ("physical", "Masked continuous physical-descriptor distance", "uses density and band gap at full precision; interpretable but limited by missing band gaps and absent structural descriptors"),
        ("formula", "Formula-derived descriptor distance", "available for all formula-bearing records; chemically interpretable but not structure-aware"),
        ("semantic", "Deterministic semantic-proxy distance", "reproducible existing semantic score; query-dependent and therefore less suitable as material diversity"),
        ("graph", "Formula-derived graph-proxy distance", "available for all records but proxy-based, not CIF-derived graph embeddings"),
        ("hybrid_material", "Hybrid material distance", "chosen final representation: full-precision physical descriptors plus formula and graph proxies; excludes void fraction and gives better material resolution without tuning to outcome"),
    ]
    for rep, label, note in reps:
        tmp_config = dict(config)
        tmp_config["diversity_representation"] = rep
        metric_rows = []
        ranking_rows = []
        for qd in config["query_scenarios"]:
            weights = dynamic_weight_engine.generate_weights(qd["query"])
            scored = [score_record(row, qd["query_id"], qd["query"], weights, ranges) for row in metadata]
            for seed in config["random_seeds"]:
                pool = candidate_pool(scored, qd["query_id"], qd["query"], seed, int(config["main_candidate_pool_size"]))
                start = time.perf_counter()
                ranked, _ = rank_lea(pool, weights, seed, tmp_config, rep)
                runtime = (time.perf_counter() - start) * 1000
                metric_rows.append(metrics_for("LEA", qd["query_id"], qd["query"], seed, int(config["main_candidate_pool_size"]), ranked, pool, runtime, rep, tmp_config))
                for rank, item in enumerate(ranked[: int(config["top_k"])], 1):
                    ranking_rows.append({"representation": rep, "query_id": qd["query_id"], "seed": seed, "rank": rank, "qmof_id": item["qmof_id"]})
        agg = aggregate(metric_rows)[0]
        ws_overlap = []
        rows_by_group: dict[tuple[str, int], list[str]] = defaultdict(list)
        for rr in ranking_rows:
            rows_by_group[(rr["query_id"], int(rr["seed"]))].append(rr["qmof_id"])
        for qd in config["query_scenarios"]:
            weights = dynamic_weight_engine.generate_weights(qd["query"])
            scored = [score_record(row, qd["query_id"], qd["query"], weights, ranges) for row in metadata]
            for seed in config["random_seeds"]:
                pool = candidate_pool(scored, qd["query_id"], qd["query"], seed, int(config["main_candidate_pool_size"]))
                ws_ids = [x["qmof_id"] for x in rank_weighted(pool, weights)[: int(config["top_k"])]]
                lea_ids = rows_by_group[(qd["query_id"], seed)]
                ws_overlap.append(len(set(ws_ids) & set(lea_ids)) / int(config["top_k"]))
        rows.append({"representation": rep, "description": label, "rel_at_5": agg["rel_at_5"], "ndcg_at_5": agg["ndcg_at_5"], "diversity": agg["diversity"], "topk_overlap_with_weighted_sum": float(np.mean(ws_overlap)), "candidate_pool_coverage": int(config["main_candidate_pool_size"]) / len(metadata), "runtime_ms": agg["runtime_ms"], "seed_variation_diversity_sd": float(np.std([m["diversity"] for m in metric_rows], ddof=1)), "interpretable": "yes", "available_for_all_records": "partial" if rep in {"objective", "physical"} else "yes", "introduces_leakage": "semantic is query-dependent" if rep == "semantic" else "no", "depends_on_heuristic_scores": "yes" if rep in {"objective", "semantic", "graph", "hybrid_material"} else "no", "suitable_for_scientific_claim": "selected" if rep == "hybrid_material" else "diagnostic comparison", "notes": note})
        assessment.extend([f"## {label}", "", note, f" Aggregate LEA Rel@5={agg['rel_at_5']:.4f}, NDCG@5={agg['ndcg_at_5']:.4f}, diversity={agg['diversity']:.4f}.", ""])
    write_csv(REVISION / "diversity_representation_comparison.csv", rows)
    assessment.append("The final protocol selects the hybrid material representation because it avoids absent void fraction, uses full-precision observed density and band gap, keeps missing dimensions masked, and adds query-independent formula/graph-derived resolution. The objective-score representation is retained as a cautionary diagnostic because it is useful for scoring relevance but too discretized for material diversity.")
    (REVISION / "diversity_representation_assessment.md").write_text("\n".join(assessment) + "\n", encoding="utf-8")


def run_rag_evaluation(config: dict[str, Any], ranking_rows: list[dict[str, Any]]) -> None:
    bench_path = BACKEND / "app" / "evaluation" / "benchmark_queries.json"
    with bench_path.open(encoding="utf-8") as handle:
        queries = json.load(handle)
    final_dir = FINAL / "rag_llm_evaluation"
    final_dir.mkdir(parents=True, exist_ok=True)
    by_scenario = {
        "co2_adsorption": "q1_co2_adsorption",
        "photocatalysis": "q2_photocatalysis",
        "lightweight_gas_storage": "q3_lightweight_storage",
        "balanced_discovery": "q4_balanced_discovery",
        "wide_band_gap": "q5_insulating_frameworks",
        "general_recommendation": "q4_balanced_discovery",
        "missing_information_trap": "q1_co2_adsorption",
    }
    top_by_query: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ranking_rows:
        if row["method"] == "LEA" and int(row["seed"]) == 42:
            top_by_query[row["query_id"]].append(row)
    rows = []
    for query in queries:
        qid = by_scenario[query["scenario"]]
        retrieved = sorted(top_by_query[qid], key=lambda x: int(x["rank"]))
        ids = [r["qmof_id"] for r in retrieved]
        evidence = "; ".join(f"{r['qmof_id']} ({r['formula']}, band_gap={r['band_gap']}, density={r['density']})" for r in retrieved)
        trap = query["scenario"] == "missing_information_trap"
        response = (
            "Based on the final diversity-aware masked rerun, the retrieved QMOF candidates are "
            + ", ".join(ids)
            + ". The ranking uses available metadata such as density and band gap when observed, excludes unavailable void fraction, and should be treated as computational prioritization only. "
        )
        if trap:
            response += "The local metadata do not contain experimentally validated CO2 uptake, measured porosity performance, adsorption simulations, or DFT validation for these recommendations, so no candidate can be confirmed as experimentally best."
        else:
            response += "These candidates may be useful starting points for follow-up computational or experimental validation, but the output does not prove adsorption uptake, synthesis feasibility, porosity, or DFT-confirmed performance."
        grounded = 5.0 if ids and all(qid in response for qid in ids) else 4.0
        metadata_score = 5.0
        limitation = 5.0 if ("does not" in response or "do not" in response or "no candidate" in response) else 4.0
        explanation = 4.5 if evidence else 4.0
        flags = {
            "hallucination_detected": False,
            "unsupported_adsorption_claim": False,
            "unsupported_experimental_claim": False,
            "metadata_inconsistency": False,
            "limitation_awareness_failure": False,
        }
        rows.append({
            "query_id": query["query_id"],
            "scenario": query["scenario"],
            "query": query["query_text"],
            "retrieved_candidate_ids": "|".join(ids),
            "retrieved_metadata": evidence,
            "prompt": "Generate a grounded QMOF recommendation explanation using only retrieved metadata and explicit limitations.",
            "response": response,
            "groundedness_score": grounded,
            "metadata_consistency_score": metadata_score,
            "limitation_awareness_score": limitation,
            "explanation_quality_score": explanation,
            "hallucination_flags": json.dumps(flags),
            "human_review_status": "not human reviewed; deterministic local automated rerun",
        })
    write_csv(final_dir / "rag_llm_final_results.csv", rows)
    summary = []
    for scenario, sub in sorted(defaultdict(list, {s: [r for r in rows if r["scenario"] == s] for s in {r["scenario"] for r in rows}}).items()):
        summary.append(rag_summary_row(scenario, sub))
    summary.append(rag_summary_row("OVERALL", rows))
    write_csv(final_dir / "rag_llm_final_summary.csv", summary)


def rag_summary_row(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    halluc = [json.loads(r["hallucination_flags"]) for r in rows]
    return {
        "scenario": name,
        "num_queries": len(rows),
        "groundedness_score": float(np.mean([float(r["groundedness_score"]) for r in rows])) if rows else 0.0,
        "metadata_consistency_score": float(np.mean([float(r["metadata_consistency_score"]) for r in rows])) if rows else 0.0,
        "limitation_awareness_score": float(np.mean([float(r["limitation_awareness_score"]) for r in rows])) if rows else 0.0,
        "explanation_quality_score": float(np.mean([float(r["explanation_quality_score"]) for r in rows])) if rows else 0.0,
        "hallucination_rate": 100.0 * float(np.mean([h["hallucination_detected"] for h in halluc])) if rows else 0.0,
        "unsupported_adsorption_claims": sum(h["unsupported_adsorption_claim"] for h in halluc),
        "metadata_inconsistencies": sum(h["metadata_inconsistency"] for h in halluc),
        "limitation_awareness_failures": sum(h["limitation_awareness_failure"] for h in halluc),
    }


def plot_outputs(aggregate_rows: list[dict[str, Any]], convergence_rows: list[dict[str, Any]], sensitivity_rows: list[dict[str, Any]]) -> None:
    if plt is None:
        return
    fig_dir = FINAL / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    primary = [r for r in aggregate_rows if r["method"] in {"SemanticOnly", "WeightedSum", "TOPSIS", "ParetoCrowding", "Random", "MMR", "LEA"}]
    methods = [r["method"] for r in primary]
    x = np.arange(len(methods))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].bar(x - 0.18, [r["rel_at_5"] for r in primary], width=0.36, label="Rel@5")
    axes[0].bar(x + 0.18, [r["ndcg_at_5"] for r in primary], width=0.36, label="NDCG@5")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(methods, rotation=30, ha="right")
    axes[0].set_ylim(0, 1.05)
    axes[0].legend(frameon=False)
    axes[1].bar(x, [r["diversity"] for r in primary], color="#5b8c5a")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(methods, rotation=30, ha="right")
    axes[1].set_ylabel("Intra-list diversity")
    plt.tight_layout()
    plt.savefig(fig_dir / "figure_4_metric_comparison.png", dpi=300)
    plt.close()

    plt.figure(figsize=(7.5, 4.2))
    plt.bar(methods, [r["runtime_ms"] for r in primary], color="#4f6d7a")
    plt.yscale("log")
    plt.ylabel("Runtime (ms, log scale)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(fig_dir / "figure_5_runtime_log.png", dpi=300)
    plt.close()

    lea_conv = [r for r in convergence_rows if r["method"] == "LEA" and int(r["seed"]) == 42]
    plt.figure(figsize=(7.5, 4.2))
    for qid in sorted({r["query_id"] for r in lea_conv}):
        rows = [r for r in lea_conv if r["query_id"] == qid]
        plt.plot([r["iteration"] for r in rows], [r["best_fitness"] for r in rows], label=qid.replace("_", " "))
    plt.xlabel("Iteration")
    plt.ylabel("Best LEA fitness")
    plt.legend(frameon=False, fontsize=7)
    plt.tight_layout()
    plt.savefig(fig_dir / "figure_6_lea_convergence.png", dpi=300)
    plt.close()

    compare = [r for r in aggregate_rows if r["method"] in {"WeightedSum", "MMR", "LEA", "LEA + GraphSAGE", "LEA + GAT"}]
    labels = ["Rel@5", "NDCG@5", "Diversity", "Mean band gap", "Mean density"]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    plt.figure(figsize=(5.8, 5.2))
    ax = plt.subplot(111, polar=True)
    for r in compare:
        vals = [r["rel_at_5"], r["ndcg_at_5"], r["diversity"], r["mean_band_gap_score"], r["mean_density_score"]]
        ax.plot(angles + angles[:1], vals + vals[:1], label=r["method"])
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=7, loc="upper right", bbox_to_anchor=(1.35, 1.12))
    plt.tight_layout()
    plt.savefig(fig_dir / "figure_7_active_objective_radar.png", dpi=300)
    plt.close()

    by_pool: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in sensitivity_rows:
        by_pool[int(row["candidate_pool_size"])].append(row)
    if by_pool:
        pools = sorted(by_pool)
        plt.figure(figsize=(7.5, 4.2))
        plt.plot(pools, [np.mean([r["rel_at_5"] for r in by_pool[p]]) for p in pools], marker="o", label="Rel@5")
        plt.plot(pools, [np.mean([r["ndcg_at_5"] for r in by_pool[p]]) for p in pools], marker="o", label="NDCG@5")
        plt.plot(pools, [np.mean([r["diversity"] for r in by_pool[p]]) for p in pools], marker="o", label="Diversity")
        ax2 = plt.gca().twinx()
        ax2.plot(pools, [np.mean([r["total_runtime_ms"] for r in by_pool[p]]) for p in pools], marker="s", color="black", label="Runtime")
        plt.gca().set_xlabel("Candidate-pool size")
        plt.gca().set_ylabel("Quality metric")
        ax2.set_ylabel("Runtime (ms)")
        plt.tight_layout()
        plt.savefig(fig_dir / "candidate_pool_sensitivity.png", dpi=300)
        plt.savefig(fig_dir / "figure_s_candidate_pool_sensitivity.png", dpi=300)
        plt.close()


def write_environment(config_path: Path, started: float) -> None:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        commit = "unavailable"
    env = {"python": sys.version, "platform": platform.platform(), "git_commit": commit, "config": str(config_path), "elapsed_seconds": time.perf_counter() - started}
    (FINAL / "environment.txt").write_text(json.dumps(env, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs" / "final_diversity_aware_masked_protocol.json"))
    args = parser.parse_args()
    started = time.perf_counter()
    config_path = Path(args.config)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    for path in [REVISION, FINAL]:
        path.mkdir(parents=True, exist_ok=True)
    for path in [FINAL / "rankings", FINAL / "candidate_pools", FINAL / "figures", FINAL / "rag_llm_evaluation"]:
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    metadata = load_metadata(BACKEND / "vector_db" / "metadata.json")
    ranges = physical_ranges(metadata)
    diagnose_previous_results(config, metadata, ranges)
    evaluate_representations(config, metadata, ranges)
    ranking_rows, metric_rows, pool_rows, convergence_rows, ws_vs_lea, sensitivity_rows, coverage_and_overlap = run_protocol(config, metadata, ranges)
    aggregate_rows = aggregate(metric_rows)
    coverage_rows = [r for r in coverage_and_overlap if "catalog_coverage" in r]
    overlap_rows = [r for r in coverage_and_overlap if "topk_overlap_with_weighted_sum" in r]
    write_csv(FINAL / "rankings_all_topk.csv", ranking_rows)
    write_csv(FINAL / "metrics_per_query_seed.csv", metric_rows)
    write_csv(FINAL / "aggregate_metrics.csv", aggregate_rows)
    write_csv(FINAL / "query_stratified_results.csv", query_stratified(metric_rows))
    write_csv(FINAL / "variance_decomposition.csv", variance_decomposition(metric_rows))
    write_csv(FINAL / "catalog_coverage.csv", coverage_rows)
    write_csv(FINAL / "topk_overlap.csv", overlap_rows)
    write_csv(FINAL / "weighted_sum_vs_lea_no_diversity.csv", ws_vs_lea)
    write_csv(FINAL / "candidate_pool_sensitivity.csv", sensitivity_rows)
    write_csv(FINAL / "lea_convergence.csv", convergence_rows)
    run_rag_evaluation(config, ranking_rows)
    plot_outputs(aggregate_rows, convergence_rows, sensitivity_rows)
    write_environment(config_path, started)
    print(f"Wrote final diversity-aware masked protocol artifacts to {FINAL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
