from app.feedback.feedback_engine import feedback_engine


class QueryFeedbackEngine:

    def get_feedback_boost(
        self,
        query,
        qmof_id,
    ):

        return feedback_engine.query_feedback_score(
            query=query,
            qmof_id=qmof_id,
        )


query_feedback_engine = QueryFeedbackEngine()
