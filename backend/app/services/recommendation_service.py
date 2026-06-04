from app.llm.recommendation_agent import recommendation_agent


class RecommendationService:

    def recommend(
        self,
        material_type,
        user_goal,
    ):

        return recommendation_agent.recommend(
            material_type,
            user_goal,
        )


recommendation_service = RecommendationService()