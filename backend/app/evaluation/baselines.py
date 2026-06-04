from __future__ import annotations

from typing import Dict, List

import numpy as np


OBJECTIVE_COLUMNS = [
    "semantic_score",
    "band_gap_score",
    "density_score",
    "porosity_score",
    "stability_score",
]


def objective_matrix(
    candidates: List[Dict],
) -> np.ndarray:
    return np.array(
        [
            [
                float(candidate.get(column, 0.0) or 0.0)
                for column in OBJECTIVE_COLUMNS
            ]
            for candidate in candidates
        ],
        dtype=np.float32,
    )


def query_weight_vector(
    weights: Dict[str, float],
) -> np.ndarray:
    vector = np.array(
        [
            weights.get("semantic", 0.0),
            weights.get("band_gap", 0.0),
            weights.get("density", 0.0),
            weights.get("porosity", 0.0),
            weights.get("stability", 0.0),
        ],
        dtype=np.float32,
    )

    total = vector.sum()

    if total <= 0:
        return np.ones_like(vector) / len(vector)

    return vector / total


def attach_rank_metadata(
    candidates: List[Dict],
    ordered_indices: np.ndarray,
    method: str,
    score_name: str,
    scores: np.ndarray,
    top_k: int,
) -> List[Dict]:
    ranked = []

    for rank, idx in enumerate(
        ordered_indices[:top_k],
        start=1,
    ):
        candidate = dict(candidates[int(idx)])
        candidate["rank"] = rank
        candidate["method"] = method
        candidate[score_name] = round(
            float(scores[int(idx)]),
            6,
        )
        ranked.append(candidate)

    return ranked


def rank_semantic_only(
    candidates: List[Dict],
    top_k: int,
) -> List[Dict]:
    scores = np.array(
        [
            float(candidate.get("semantic_score", 0.0) or 0.0)
            for candidate in candidates
        ],
        dtype=np.float32,
    )
    order = np.argsort(scores)[::-1]

    return attach_rank_metadata(
        candidates,
        order,
        "SemanticOnly",
        "baseline_score",
        scores,
        top_k,
    )


def rank_weighted_sum(
    candidates: List[Dict],
    weights: Dict[str, float],
    top_k: int,
) -> List[Dict]:
    matrix = objective_matrix(candidates)
    weight_vector = query_weight_vector(weights)
    scores = matrix @ weight_vector
    order = np.argsort(scores)[::-1]

    return attach_rank_metadata(
        candidates,
        order,
        "WeightedSum",
        "baseline_score",
        scores,
        top_k,
    )


def rank_topsis(
    candidates: List[Dict],
    weights: Dict[str, float],
    top_k: int,
) -> List[Dict]:
    matrix = objective_matrix(candidates)
    weight_vector = query_weight_vector(weights)

    ideal = np.ones(matrix.shape[1], dtype=np.float32)
    anti_ideal = np.zeros(matrix.shape[1], dtype=np.float32)

    d_ideal = np.sqrt(
        np.sum(
            weight_vector * (matrix - ideal) ** 2,
            axis=1,
        )
    )
    d_anti = np.sqrt(
        np.sum(
            weight_vector * (matrix - anti_ideal) ** 2,
            axis=1,
        )
    )

    scores = d_anti / (d_ideal + d_anti + 1e-12)
    order = np.argsort(scores)[::-1]

    return attach_rank_metadata(
        candidates,
        order,
        "TOPSIS",
        "baseline_score",
        scores,
        top_k,
    )


def dominates(
    first: np.ndarray,
    second: np.ndarray,
) -> bool:
    return bool(
        np.all(first >= second)
        and np.any(first > second)
    )


def pareto_fronts(
    matrix: np.ndarray,
) -> List[List[int]]:
    remaining = set(range(len(matrix)))
    fronts = []

    while remaining:
        front = []

        for idx in remaining:
            if not any(
                dominates(matrix[other], matrix[idx])
                for other in remaining
                if other != idx
            ):
                front.append(idx)

        fronts.append(front)
        remaining -= set(front)

    return fronts


def crowding_scores(
    matrix: np.ndarray,
    front: List[int],
) -> Dict[int, float]:
    if len(front) <= 2:
        return {
            idx: float("inf")
            for idx in front
        }

    scores = {
        idx: 0.0
        for idx in front
    }
    front_matrix = matrix[front]

    for objective_idx in range(matrix.shape[1]):
        values = front_matrix[:, objective_idx]
        order = np.argsort(values)
        low = float(values[order[0]])
        high = float(values[order[-1]])

        scores[front[order[0]]] = float("inf")
        scores[front[order[-1]]] = float("inf")

        if high == low:
            continue

        for pos in range(1, len(order) - 1):
            prev_value = float(values[order[pos - 1]])
            next_value = float(values[order[pos + 1]])
            scores[front[order[pos]]] += (
                next_value - prev_value
            ) / (high - low)

    return scores


def rank_pareto_crowding(
    candidates: List[Dict],
    weights: Dict[str, float],
    top_k: int,
) -> List[Dict]:
    matrix = objective_matrix(candidates)
    weight_vector = query_weight_vector(weights)
    weighted_scores = matrix @ weight_vector
    fronts = pareto_fronts(matrix)
    ordered = []
    scores = np.zeros(len(candidates), dtype=np.float32)

    for front_idx, front in enumerate(fronts):
        crowding = crowding_scores(matrix, front)
        front_order = sorted(
            front,
            key=lambda idx: (
                crowding[idx],
                weighted_scores[idx],
            ),
            reverse=True,
        )

        for idx in front_order:
            scores[idx] = (
                (len(fronts) - front_idx)
                + 0.01 * float(weighted_scores[idx])
            )

        ordered.extend(front_order)

    return attach_rank_metadata(
        candidates,
        np.array(ordered),
        "ParetoCrowding",
        "baseline_score",
        scores,
        top_k,
    )


def rank_random(
    candidates: List[Dict],
    top_k: int,
    seed: int,
) -> List[Dict]:
    rng = np.random.default_rng(seed)
    scores = rng.random(len(candidates))
    order = np.argsort(scores)[::-1]

    return attach_rank_metadata(
        candidates,
        order,
        "Random",
        "baseline_score",
        scores,
        top_k,
    )
