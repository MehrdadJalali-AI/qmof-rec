from app.recommendation.query_feedback_engine import (
    query_feedback_engine,
)

from app.utils.json_utils import (
    sanitize_number,
)


class FeedbackRanker:

    def rerank(
        self,
        query,
        recommendations,
    ):

        reranked = []

        for item in recommendations:

            qmof_id = item.get(
                "qmof_id",
                "",
            )

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

            feedback_boost = query_feedback_engine.get_feedback_boost(
                query=query,
                qmof_id=qmof_id,
            )

            final_score = base_score + feedback_boost

            updated = dict(item)

            updated["feedback_boost"] = round(
                sanitize_number(
                    feedback_boost,
                    default=0.0,
                ),
                4,
            )

            updated["final_score"] = round(
                sanitize_number(
                    final_score,
                    default=0.0,
                ),
                4,
            )

            reranked.append(updated)

        reranked.sort(
            key=lambda x: x.get(
                "final_score",
                0.0,
            ),
            reverse=True,
        )

        for index, item in enumerate(
            reranked,
            start=1,
        ):
            item["rank"] = index

        return reranked


feedback_ranker = FeedbackRanker()
