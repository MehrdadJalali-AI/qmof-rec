from __future__ import annotations

from typing import Dict, List

import numpy as np

from app.evaluation.baselines import (
    OBJECTIVE_COLUMNS,
    objective_matrix,
    query_weight_vector,
)


def pairwise_diversity(
    ranked: List[Dict],
) -> float:
    if len(ranked) <= 1:
        return 0.0

    matrix = objective_matrix(ranked)
    distances = [
        np.linalg.norm(first - second)
        for i, first in enumerate(matrix)
        for second in matrix[i + 1 :]
    ]

    return float(
        np.mean(distances)
    ) if distances else 0.0


def ndcg_at_k(
    ranked_relevance: np.ndarray,
    ideal_relevance: np.ndarray,
) -> float:
    def dcg(values: np.ndarray) -> float:
        gains = (2**values) - 1
        discounts = np.log2(
            np.arange(len(values)) + 2
        )
        return float(
            np.sum(gains / discounts)
        )

    ideal_dcg = dcg(ideal_relevance)

    if ideal_dcg <= 0:
        return 0.0

    return dcg(ranked_relevance) / ideal_dcg


def evaluate_ranking(
    ranked: List[Dict],
    candidate_pool: List[Dict],
    weights: Dict[str, float],
    top_k: int,
) -> Dict[str, float]:
    matrix = objective_matrix(ranked)
    pool_matrix = objective_matrix(candidate_pool)
    weight_vector = query_weight_vector(weights)

    relevance = matrix @ weight_vector
    pool_relevance = pool_matrix @ weight_vector
    ideal = np.sort(pool_relevance)[::-1][:top_k]

    objective_means = {
        f"mean_{column}": float(
            np.mean(matrix[:, idx])
        )
        for idx, column in enumerate(OBJECTIVE_COLUMNS)
    }

    balance = float(
        np.mean(
            np.min(
                matrix,
                axis=1,
            )
        )
    )

    hypervolume_proxy = float(
        np.mean(
            np.prod(
                matrix + 1e-9,
                axis=1,
            )
        )
    )

    return {
        "mean_relevance": float(np.mean(relevance)),
        "best_relevance": float(np.max(relevance)),
        "balance": balance,
        "diversity": pairwise_diversity(ranked),
        "hypervolume_proxy": hypervolume_proxy,
        "ndcg_at_k": ndcg_at_k(relevance, ideal),
        **objective_means,
    }
