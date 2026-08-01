from app.recommendation.objective_utils import (
    is_observed,
    masked_weighted_sum,
    observed_float,
)
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
        density_available,
    ):

        real_stability = material.get("stability")

        if is_observed(real_stability):

            return sanitize_number(
                real_stability,
                default=0.0,
            ), True

        if density_available:

            return sanitize_number(
                density_score,
                default=0.0,
            ), True

        return 0.0, False

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

        band_gap_available = is_observed(material.get("band_gap"))
        density_available = is_observed(material.get("density"))
        void_fraction_available = is_observed(material.get("void_fraction"))

        band_gap_score = (
            sanitize_number(
                property_scorer.score_band_gap(material.get("band_gap")),
                default=0.0,
            )
            if band_gap_available
            else 0.0
        )

        density_score = (
            sanitize_number(
                property_scorer.score_density(material.get("density")),
                default=0.0,
            )
            if density_available
            else 0.0
        )

        stability_score, stability_available = self._compute_stability_score(
            material=material,
            density_score=density_score,
            density_available=density_available,
        )

        scores = {
            "semantic_score": semantic_score,
            "band_gap_score": band_gap_score,
            "density_score": density_score,
            "stability_score": stability_score,
        }
        availability = {
            "semantic": True,
            "band_gap": band_gap_available,
            "density": density_available,
            "stability": stability_available,
        }

        final_score = masked_weighted_sum(
            scores=scores,
            weights=weights,
            availability=availability,
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
            "porosity_score": None,
            "stability_score": round(
                stability_score,
                4,
            ),
            "availability": availability,
            "void_fraction_available": void_fraction_available,
            "void_fraction_note": "unavailable; excluded from numerical ranking",
        }


hybrid_ranker = HybridRanker()
