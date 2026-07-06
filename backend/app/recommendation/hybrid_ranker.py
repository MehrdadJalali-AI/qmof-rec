from app.recommendation.property_scorer import (
    property_scorer,
)

from app.utils.json_utils import (
    sanitize_number,
)


class HybridRanker:

    def _compute_stability_score(
        self,
        material,
        density_score,
        porosity_score,
    ):

        real_stability = sanitize_number(
            material.get("stability"),
            default=None,
        )

        if real_stability is not None:

            return sanitize_number(
                real_stability,
                default=0.0,
            )

        """
        Proxy stability only when
        real descriptor missing
        """

        proxy = 0.6 * density_score + 0.4 * (1 - abs(porosity_score - 0.5))

        return sanitize_number(
            proxy,
            default=0.0,
        )

    def compute_score(
        self,
        material,
        weights,
        semantic_score,
    ):

        semantic_score = sanitize_number(
            semantic_score,
            default=0.0,
        )

        band_gap_score = sanitize_number(
            property_scorer.score_band_gap(material.get("band_gap")),
            default=0.0,
        )

        density_score = sanitize_number(
            property_scorer.score_density(material.get("density")),
            default=0.0,
        )

        porosity_score = sanitize_number(
            property_scorer.score_porosity(material.get("void_fraction")),
            default=0.0,
        )

        stability_score = self._compute_stability_score(
            material=material,
            density_score=density_score,
            porosity_score=porosity_score,
        )

        semantic_weight = sanitize_number(
            weights.get(
                "semantic",
                0.0,
            ),
            default=0.0,
        )

        band_gap_weight = sanitize_number(
            weights.get(
                "band_gap",
                0.0,
            ),
            default=0.0,
        )

        density_weight = sanitize_number(
            weights.get(
                "density",
                0.0,
            ),
            default=0.0,
        )

        porosity_weight = sanitize_number(
            weights.get(
                "porosity",
                0.0,
            ),
            default=0.0,
        )

        stability_weight = sanitize_number(
            weights.get(
                "stability",
                0.0,
            ),
            default=0.0,
        )

        final_score = (
            semantic_weight * semantic_score
            + band_gap_weight * band_gap_score
            + density_weight * density_score
            + porosity_weight * porosity_score
            + stability_weight * stability_score
        )

        final_score = sanitize_number(
            final_score,
            default=0.0,
        )

        return {
            "final_score": round(
                final_score,
                4,
            ),
            "band_gap_score": round(
                band_gap_score,
                4,
            ),
            "density_score": round(
                density_score,
                4,
            ),
            "porosity_score": round(
                porosity_score,
                4,
            ),
            "stability_score": round(
                stability_score,
                4,
            ),
        }


hybrid_ranker = HybridRanker()
