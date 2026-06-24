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
    LotusEffectOptimizer,
)

from app.recommendation.novelty_ranker import (
    novelty_ranker,
)

from app.recommendation.feedback_ranker import (
    feedback_ranker,
)

from app.utils.json_utils import (
    sanitize_for_json,
    sanitize_number,
)


class RecommendationPipeline:

    def _candidate_pool_size(
        self,
        top_k,
    ):

        top_k = int(
            sanitize_number(
                top_k,
                default=5,
            )
        )

        top_k = max(
            1,
            top_k,
        )

        retrieval_multiplier = 5

        return max(
            top_k * retrieval_multiplier,
            top_k + 5,
        )

    def _novelty_weight(
        self,
        weights,
    ):

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

        novelty_weight = 0.03 + 0.04 * (porosity_weight + stability_weight)

        return min(
            0.10,
            max(
                0.03,
                novelty_weight,
            ),
        )

    def _similarity_weight(
        self,
        weights,
    ):

        semantic_weight = sanitize_number(
            weights.get(
                "semantic",
                0.0,
            ),
            default=0.0,
        )

        return min(
            0.20,
            max(
                0.08,
                0.10 + 0.10 * semantic_weight,
            ),
        )

    def recommend(
        self,
        query,
        top_k=5,
    ):

        top_k = int(
            sanitize_number(
                top_k,
                default=5,
            )
        )

        top_k = max(
            1,
            top_k,
        )

        weights = dynamic_weight_engine.generate_weights(query)

        candidate_pool_size = self._candidate_pool_size(top_k)

        retrieved = retrieve_materials(
            query=query,
            top_k=candidate_pool_size,
        )

        if not retrieved:

            return sanitize_for_json(
                {
                    "query": query,
                    "weights": weights,
                    "candidate_pool_size": candidate_pool_size,
                    "optimization_method": "LEA + novelty + query-specific feedback",
                    "recommendation_count": 0,
                    "recommendations": [],
                }
            )

        candidates = []

        reference_material = retrieved[0].get(
            "document",
            {},
        )

        similarity_weight = self._similarity_weight(weights)

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

            semantic_score = sanitize_number(
                1.0 / (1.0 + raw_distance),
                default=0.0,
            )

            hybrid_scores = hybrid_ranker.compute_score(
                material=material,
                weights=weights,
                semantic_score=semantic_score,
            )

            similarity_score = sanitize_number(
                material_similarity.similarity(
                    reference_material,
                    material,
                ),
                default=0.0,
            )

            base_score = sanitize_number(
                hybrid_scores.get(
                    "final_score",
                    0.0,
                ),
                default=0.0,
            )

            final_score = sanitize_number(
                base_score + similarity_weight * similarity_score,
                default=0.0,
            )

            scoring_context = {
                **hybrid_scores,
                "similarity_score": similarity_score,
                "similarity_weight": similarity_weight,
                "final_score": final_score,
            }

            explanations = explainability_engine.explain(
                material,
                scoring_context,
            )

            candidate = {
                "qmof_id": material.get("qmof_id"),
                "formula": material.get("formula"),
                "band_gap": sanitize_number(
                    material.get("band_gap"),
                    default=None,
                ),
                "density": sanitize_number(
                    material.get("density"),
                    default=None,
                ),
                "void_fraction": sanitize_number(
                    material.get("void_fraction"),
                    default=None,
                ),
                "semantic_score": round(
                    semantic_score,
                    4,
                ),
                "similarity_score": round(
                    similarity_score,
                    4,
                ),
                "similarity_weight": round(
                    similarity_weight,
                    4,
                ),
                "band_gap_score": sanitize_number(
                    hybrid_scores.get(
                        "band_gap_score",
                        0.0,
                    ),
                    default=0.0,
                ),
                "density_score": sanitize_number(
                    hybrid_scores.get(
                        "density_score",
                        0.0,
                    ),
                    default=0.0,
                ),
                "porosity_score": sanitize_number(
                    hybrid_scores.get(
                        "porosity_score",
                        0.0,
                    ),
                    default=0.0,
                ),
                "stability_score": sanitize_number(
                    hybrid_scores.get(
                        "stability_score",
                        material.get(
                            "stability",
                            0.0,
                        ),
                    ),
                    default=0.0,
                ),
                "base_score": round(
                    base_score,
                    4,
                ),
                "final_score": round(
                    final_score,
                    4,
                ),
                "explanations": explanations,
            }

            candidates.append(candidate)

        dynamic_population_size = max(
            20,
            min(
                100,
                len(candidates),
            ),
        )

        dynamic_iterations = max(
            20,
            min(
                100,
                top_k * 12,
            ),
        )

        lea_optimizer = LotusEffectOptimizer(
            population_size=dynamic_population_size,
            max_iterations=dynamic_iterations,
            top_k=top_k,
            seed=42,
        )

        lea_ranked = lea_optimizer.rank(
            materials=candidates,
            weights=weights,
            top_k=top_k,
        )

        novelty_weight = self._novelty_weight(weights)

        novelty_ranked = novelty_ranker.rerank(
            candidates=lea_ranked,
            novelty_weight=novelty_weight,
        )

        feedback_ranked = feedback_ranker.rerank(
            query=query,
            recommendations=novelty_ranked,
        )

        result = {
            "query": query,
            "weights": weights,
            "candidate_pool_size": candidate_pool_size,
            "optimization_method": "LEA + novelty + query-specific feedback",
            "lea_population_size": dynamic_population_size,
            "lea_iterations": dynamic_iterations,
            "lea_diversity_score": round(
                sanitize_number(
                    lea_optimizer.diversity_score,
                    default=0.0,
                ),
                4,
            ),
            "novelty_weight": round(
                novelty_weight,
                4,
            ),
            "similarity_weight": round(
                similarity_weight,
                4,
            ),
            "recommendation_count": len(feedback_ranked),
            "recommendations": feedback_ranked,
        }

        return sanitize_for_json(result)


recommendation_pipeline = RecommendationPipeline()
