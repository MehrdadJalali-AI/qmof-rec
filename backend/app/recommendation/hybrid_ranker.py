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


STABILITY_MEASURED = "measured"
STABILITY_DENSITY_PROXY = "density_proxy"
STABILITY_MISSING = "missing"


class HybridRanker:

    def _compute_stability_score(
        self,
        material,
        density_score,
        density_available,
    ):

        score, available, _source = self._compute_stability_score_with_source(
            material=material,
            density_score=density_score,
            density_available=density_available,
        )

        return score, available

    def _compute_stability_score_with_source(
        self,
        material,
        density_score,
        density_available,
    ):
        """Return (score, available, source).

        source is STABILITY_MEASURED, STABILITY_DENSITY_PROXY or
        STABILITY_MISSING. Without a measured stability value the score is the
        binned density score: a heuristic proxy, not stability evidence.
        """

        real_stability = material.get("stability")

        if is_observed(real_stability):

            return sanitize_number(
                real_stability,
                default=0.0,
            ), True, STABILITY_MEASURED

        if density_available:

            return sanitize_number(
                density_score,
                default=0.0,
            ), True, STABILITY_DENSITY_PROXY

        return 0.0, False, STABILITY_MISSING

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

        (
            stability_score,
            stability_available,
            stability_source,
        ) = self._compute_stability_score_with_source(
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
            # Provenance fields (QMOF-Audit Phase A). They do not affect
            # final_score; they record how each objective score was produced.
            "stability_source": stability_source,
            "provenance": {
                "band_gap": "observed" if band_gap_available else "missing_masked",
                "density": "observed" if density_available else "missing_masked",
                "stability": stability_source,
                "void_fraction": "observed" if void_fraction_available else "missing_excluded",
            },
        }


hybrid_ranker = HybridRanker()
