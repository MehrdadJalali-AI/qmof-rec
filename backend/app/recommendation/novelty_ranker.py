import numpy as np

from app.recommendation.objective_utils import ACTIVE_OBJECTIVES, masked_distance
from app.utils.json_utils import (
    sanitize_number,
)


class NoveltyRanker:

    def _vector_with_mask(
        self,
        item,
    ):

        availability = item.get("availability", {}) or {}

        vector = []
        mask = []

        for objective in ACTIVE_OBJECTIVES:
            vector.append(
                sanitize_number(
                    item.get(objective),
                    default=0.0,
                )
            )
            mask.append(bool(availability.get(objective.replace("_score", ""), True)))

        return (
            np.array(
                vector,
                dtype=np.float32,
            ),
            np.array(
                mask,
                dtype=bool,
            ),
        )

    def _normalize_vectors(
        self,
        vectors,
        masks,
    ):

        normalized = vectors.copy()

        for col in range(vectors.shape[1]):
            observed = masks[:, col]
            if not np.any(observed):
                normalized[:, col] = 0.0
                continue
            col_values = vectors[observed, col]
            col_min = float(col_values.min())
            col_max = float(col_values.max())
            denominator = col_max - col_min
            if denominator <= 1e-8:
                normalized[observed, col] = 0.0
            else:
                normalized[observed, col] = (vectors[observed, col] - col_min) / denominator
            normalized[~observed, col] = 0.0

        return normalized

    def add_novelty_scores(
        self,
        candidates,
    ):

        if not candidates:

            return []

        extracted = [self._vector_with_mask(item) for item in candidates]

        vectors = np.array(
            [vector for vector, _ in extracted],
            dtype=np.float32,
        )
        masks = np.array(
            [mask for _, mask in extracted],
            dtype=bool,
        )

        normalized_vectors = self._normalize_vectors(vectors, masks)

        centroid = np.zeros(normalized_vectors.shape[1], dtype=np.float32)
        centroid_mask = np.any(masks, axis=0)
        for col in range(normalized_vectors.shape[1]):
            observed = masks[:, col]
            if np.any(observed):
                centroid[col] = float(np.mean(normalized_vectors[observed, col]))

        distances = []

        for vector, mask in zip(normalized_vectors, masks):

            distance = masked_distance(vector, centroid, mask, centroid_mask)

            distances.append(distance)

        max_distance = max(distances)

        updated = []

        for item, distance in zip(
            candidates,
            distances,
        ):

            novelty_score = distance / (max_distance + 1e-8)

            copied = dict(item)

            copied["novelty_score"] = round(
                sanitize_number(
                    novelty_score,
                    default=0.0,
                ),
                4,
            )

            updated.append(copied)

        return updated

    def rerank(
        self,
        candidates,
        novelty_weight=0.05,
    ):

        novelty_weight = sanitize_number(
            novelty_weight,
            default=0.05,
        )

        novelty_weight = min(
            0.25,
            max(
                0,
                novelty_weight,
            ),
        )

        updated = self.add_novelty_scores(candidates)

        for item in updated:

            base_score = sanitize_number(
                item.get(
                    "final_score",
                    item.get(
                        "lea_score",
                        0.0,
                    ),
                ),
                default=0.0,
            )

            novelty_score = sanitize_number(
                item.get("novelty_score"),
                default=0.0,
            )

            adjusted_score = base_score + novelty_weight * novelty_score

            item["final_score"] = round(
                sanitize_number(
                    adjusted_score,
                    default=0.0,
                ),
                4,
            )

        updated.sort(
            key=lambda x: x.get(
                "final_score",
                0.0,
            ),
            reverse=True,
        )

        return updated


novelty_ranker = NoveltyRanker()
