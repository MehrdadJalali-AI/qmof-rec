from app.recommendation.property_scorer import (
    property_scorer,
)

from app.utils.json_utils import (
    sanitize_number,
)


class HybridRanker:

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
            property_scorer.score_band_gap(
                material.get(
                    "band_gap"
                )
            )
        )

        density_score = sanitize_number(
            property_scorer.score_density(
                material.get(
                    "density"
                )
            )
        )

        porosity_score = sanitize_number(
            property_scorer.score_porosity(
                material.get(
                    "void_fraction"
                )
            )
        )

        final_score = (

            weights.get(
                "semantic",
                0,
            ) * semantic_score

            +

            weights.get(
                "band_gap",
                0,
            ) * band_gap_score

            +

            weights.get(
                "density",
                0,
            ) * density_score

            +

            weights.get(
                "porosity",
                0,
            ) * porosity_score

        )

        final_score = sanitize_number(
            final_score
        )

        return {

            "final_score":
                round(
                    final_score,
                    4,
                ),

            "band_gap_score":
                band_gap_score,

            "density_score":
                density_score,

            "porosity_score":
                porosity_score,
        }


hybrid_ranker = HybridRanker()