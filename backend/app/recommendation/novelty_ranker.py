import numpy as np

from app.utils.json_utils import (
    sanitize_number,
)


class NoveltyRanker:

    def _vector(
        self,
        item,
    ):

        vector = [
            sanitize_number(
                item.get("semantic_score"),
                default=0.0,
            ),
            sanitize_number(
                item.get("band_gap_score"),
                default=0.0,
            ),
            sanitize_number(
                item.get("density_score"),
                default=0.0,
            ),
            sanitize_number(
                item.get("porosity_score"),
                default=0.0,
            ),
            sanitize_number(
                item.get("stability_score"),
                default=0.0,
            ),
        ]

        return np.array(
            vector,
            dtype=np.float32,
        )

    def _normalize_vectors(
        self,
        vectors,
    ):

        mins = vectors.min(
            axis=0,
            keepdims=True,
        )

        maxs = vectors.max(
            axis=0,
            keepdims=True,
        )

        denominator = maxs - mins + 1e-8

        normalized = (vectors - mins) / denominator

        return normalized

    def add_novelty_scores(
        self,
        candidates,
    ):

        if not candidates:

            return []

        vectors = np.array(
            [self._vector(item) for item in candidates],
            dtype=np.float32,
        )

        normalized_vectors = self._normalize_vectors(vectors)

        centroid = np.mean(
            normalized_vectors,
            axis=0,
        )

        distances = []

        for vector in normalized_vectors:

            distance = float(np.linalg.norm(vector - centroid))

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
