from pydantic import BaseModel


class RecommendationRequest(BaseModel):

    material_type: str
    user_goal: str