from app.rag.retriever import retrieve_materials

from app.recommendation.dynamic_weight_engine import (
    dynamic_weight_engine,
)

from app.recommendation.hybrid_ranker import (
    hybrid_ranker,
)

from app.recommendation.explainability_engine import (
    explainability_engine,
)

from app.recommendation.material_similarity import (
    material_similarity,
)

from app.recommendation.lea_optimizer import (
    lea_optimizer,
)

from app.utils.json_utils import (
    sanitize_for_json,
    sanitize_number,
)


class RecommendationPipeline:


    def recommend(
        self,
        query,
        top_k=5,
    ):

        """
        Phase 2 Recommendation Flow

        Query

        ↓

        Retrieve Candidates

        ↓

        Dynamic Weights

        ↓

        Hybrid Ranking

        ↓

        Similarity Re-ranking

        ↓

        Lotus Effect Optimization

        ↓

        Explainability
        """

        weights = dynamic_weight_engine.generate_weights(
            query
        )

        candidate_pool_size = max(
            top_k,
            top_k * 5,
        )

        retrieved = retrieve_materials(

            query=query,

            top_k=candidate_pool_size,

        )

        if not retrieved:

            return {

                "query": query,

                "weights": weights,

                "recommendations": [],

            }

        ranked_results = []

        reference_material = retrieved[0].get(
            "document",
            {},
        )

        for item in retrieved:

            material = item.get(
                "document",
                {},
            )

            raw_distance = sanitize_number(

                item.get(
                    "score",
                    999,
                ),

                default=999,

            )

            semantic_score = (

                1 /

                (

                    1 +

                    raw_distance

                )

            )

            semantic_score = sanitize_number(
                semantic_score
            )

            hybrid_scores = hybrid_ranker.compute_score(

                material=material,

                weights=weights,

                semantic_score=semantic_score,

            )

            similarity_score = material_similarity.similarity(

                reference_material,

                material,

            )

            similarity_score = sanitize_number(
                similarity_score,
                default=0,
            )

            final_score = (

                hybrid_scores[
                    "final_score"
                ]

                +

                0.15 *

                similarity_score

            )

            explanations = explainability_engine.explain(

                material,

                {

                    **hybrid_scores,

                    "similarity_score":

                        similarity_score,

                    "final_score":

                        final_score,

                },

            )

            ranked_results.append({

                "qmof_id":

                    material.get(
                        "qmof_id"
                    ),

                "formula":

                    material.get(
                        "formula"
                    ),

                "band_gap":

                    sanitize_number(

                        material.get(
                            "band_gap"
                        ),

                        default=None,

                    ),

                "density":

                    sanitize_number(

                        material.get(
                            "density"
                        ),

                        default=None,

                    ),

                "void_fraction":

                    sanitize_number(

                        material.get(
                            "void_fraction"
                        ),

                        default=None,

                    ),

                "semantic_score":

                    round(
                        semantic_score,
                        4,
                    ),

                "similarity_score":

                    round(
                        similarity_score,
                        4,
                    ),

                "band_gap_score":

                    round(
                        hybrid_scores[
                            "band_gap_score"
                        ],
                        4,
                    ),

                "density_score":

                    round(
                        hybrid_scores[
                            "density_score"
                        ],
                        4,
                    ),

                "porosity_score":

                    round(
                        hybrid_scores[
                            "porosity_score"
                        ],
                        4,
                    ),

                "stability_score":

                    round(
                        hybrid_scores[
                            "stability_score"
                        ],
                        4,
                    ),

                "final_score":

                    round(
                        final_score,
                        4,
                    ),

                "explanations":

                    explanations,

            })

        ranked_results = lea_optimizer.rank(
            materials=ranked_results,
            weights=weights,
            top_k=top_k,
        )

        for material in ranked_results:
            material["explanations"] = explainability_engine.explain(
                material,
                material,
            )

        result = {

            "query": query,

            "weights": weights,

            "optimization": {

                "method": "Lotus Effect Algorithm",

                "candidate_pool_size":

                    len(
                        retrieved
                    ),

                "iterations":

                    lea_optimizer.max_iterations,

                "population_size":

                    lea_optimizer.population_size,

                "best_fitness_history":

                    [
                        round(
                            sanitize_number(value),
                            4,
                        )
                        for value in lea_optimizer.fitness_history
                    ],

                "diversity_score":

                    round(
                        sanitize_number(
                            lea_optimizer.diversity_score
                        ),
                        4,
                    ),

            },

            "recommendation_count":

                len(
                    ranked_results
                ),

            "recommendations":

                ranked_results,

        }

        return sanitize_for_json(
            result
        )


recommendation_pipeline = RecommendationPipeline()
