from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from app.utils.json_utils import sanitize_number


ACTIVE_OBJECTIVES = [
    "semantic_score",
    "band_gap_score",
    "density_score",
    "stability_score",
]

WEIGHT_KEYS = [
    "semantic",
    "band_gap",
    "density",
    "stability",
]

# Void fraction is absent in the current metadata, so porosity/void fraction is
# kept as an availability warning only and excluded from numerical ranking.
INACTIVE_OBJECTIVES = ["porosity_score"]
EPSILON = 1e-8


def is_observed(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric)


def observed_float(value, default: float = 0.0) -> float:
    if not is_observed(value):
        return default
    return sanitize_number(value, default=default)


def normalize_weights(weights: dict, keys: Iterable[str] = WEIGHT_KEYS) -> dict:
    raw = {
        key: max(0.0, sanitize_number(weights.get(key, 0.0), default=0.0))
        for key in keys
    }
    total = sum(raw.values())
    if total <= 0:
        equal = 1.0 / max(1, len(raw))
        return {key: equal for key in raw}
    return {key: value / total for key, value in raw.items()}


def masked_weighted_sum(scores: dict, weights: dict, availability: dict) -> float:
    active_weights = normalize_weights(weights)
    numerator = 0.0
    denominator = 0.0
    score_keys = {
        "semantic": "semantic_score",
        "band_gap": "band_gap_score",
        "density": "density_score",
        "stability": "stability_score",
    }
    for weight_key, score_key in score_keys.items():
        available_key = score_key.replace("_score", "")
        if availability.get(available_key, True):
            weight = active_weights.get(weight_key, 0.0)
            numerator += weight * sanitize_number(scores.get(score_key), default=0.0)
            denominator += weight
    if denominator <= EPSILON:
        return 0.0
    return numerator / denominator


def masked_distance(left: np.ndarray, right: np.ndarray, left_mask: np.ndarray, right_mask: np.ndarray) -> float:
    joint = np.logical_and(left_mask.astype(bool), right_mask.astype(bool))
    if not np.any(joint):
        # No shared evidence means no distance contribution; callers treat this
        # as neutral rather than inventing a descriptor value.
        return 0.0
    diff = left[joint] - right[joint]
    return float(np.sqrt(np.mean(diff * diff)))


def masked_cosine(left: np.ndarray, right: np.ndarray, left_mask: np.ndarray, right_mask: np.ndarray) -> float:
    joint = np.logical_and(left_mask.astype(bool), right_mask.astype(bool))
    if not np.any(joint):
        # Zero similarity is the neutral fallback when two materials have no
        # jointly observed descriptor dimensions.
        return 0.0
    lvec = left[joint]
    rvec = right[joint]
    denom = float(np.linalg.norm(lvec) * np.linalg.norm(rvec))
    if denom <= EPSILON:
        return 0.0
    return float(np.dot(lvec, rvec) / denom)
