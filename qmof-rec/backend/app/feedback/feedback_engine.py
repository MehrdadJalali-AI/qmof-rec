from datetime import datetime

from app.feedback.feedback_store import (
    feedback_store,
)

from app.feedback.query_similarity import (
    query_similarity,
)

SIMILARITY_THRESHOLD = 0.70

MAX_FEEDBACK_BOOST = 0.20


class FeedbackEngine:

    def submit(
        self,
        query,
        qmof_id,
        relevance,
        usefulness,
        comment=None,
    ):

        relevance = int(relevance)

        usefulness = int(usefulness)

        relevance = max(
            1,
            min(
                5,
                relevance,
            ),
        )

        usefulness = max(
            1,
            min(
                5,
                usefulness,
            ),
        )

        feedback = {
            "query": query,
            "qmof_id": qmof_id,
            "relevance": relevance,
            "usefulness": usefulness,
            "comment": comment or "",
            "timestamp": datetime.utcnow().isoformat(),
        }

        return feedback_store.add_feedback(feedback)

    def _recency_weight(
        self,
        timestamp,
    ):

        try:

            created = datetime.fromisoformat(timestamp)

            days = (datetime.utcnow() - created).days

            """
            recent feedback matters more
            """

            return max(
                0.5,
                1.0 - days / 365,
            )

        except (ValueError, TypeError):

            return 1.0

    def query_feedback_score(
        self,
        query,
        qmof_id,
    ):

        data = feedback_store.load()

        if not data:

            return 0.0

        weighted_scores = []

        seen_queries = set()

        for item in data:

            if item.get("qmof_id") != qmof_id:

                continue

            stored_query = item.get(
                "query",
                "",
            )

            duplicate_key = (
                stored_query,
                qmof_id,
            )

            """
            avoid duplicate spam
            """

            if duplicate_key in seen_queries:

                continue

            seen_queries.add(duplicate_key)

            similarity = query_similarity.similarity(
                query,
                stored_query,
            )

            if similarity < SIMILARITY_THRESHOLD:

                continue

            relevance = float(
                item.get(
                    "relevance",
                    1,
                )
            )

            usefulness = float(
                item.get(
                    "usefulness",
                    1,
                )
            )

            normalized_rating = (relevance + usefulness) / 10.0

            centered_score = normalized_rating - 0.5

            recency = self._recency_weight(item.get("timestamp", ""))

            weighted_scores.append(similarity * centered_score * recency)

        if not weighted_scores:

            return 0.0

        boost = sum(weighted_scores) / len(weighted_scores)

        boost = max(
            -MAX_FEEDBACK_BOOST,
            min(
                MAX_FEEDBACK_BOOST,
                boost,
            ),
        )

        return round(
            boost,
            4,
        )


feedback_engine = FeedbackEngine()
