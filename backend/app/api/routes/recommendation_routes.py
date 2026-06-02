from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.recommendation.recommendation_pipeline import (
    recommendation_pipeline,
)

router = APIRouter(
    prefix="/recommend",
    tags=["recommendation"],
)


class RecommendationRequest(BaseModel):

    material_type: Optional[str] = None

    user_goal: Optional[str] = None

    query: Optional[str] = None

    top_k: int = 5


@router.post("/")
def recommend_materials(
    request: RecommendationRequest,
):

    """
    Supports BOTH:

    OLD:

    {
        "material_type":"MOF",
        "user_goal":"CO2 adsorption"
    }

    NEW:

    {
        "query":"stable porous MOFs for CO2 adsorption"
    }
    """

    if request.query:

        query = request.query

    else:

        material_type = request.material_type or ""

        user_goal = request.user_goal or ""

        query = f"{material_type} {user_goal}".strip()

    result = recommendation_pipeline.recommend(
        query=query,
        top_k=request.top_k,
    )

    return result