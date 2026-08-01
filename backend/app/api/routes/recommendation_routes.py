from fastapi import APIRouter, HTTPException

from app.api.schemas.recommendation_schema import RecommendationRequest
from app.recommendation.recommendation_pipeline import recommendation_pipeline

router = APIRouter(
    prefix="/recommend",
    tags=["recommendation"],
)


@router.post("/")
def recommend_materials(request: RecommendationRequest):
    query = request.resolved_query()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'query' or 'material_type'/'user_goal'.",
        )

    return recommendation_pipeline.recommend(
        query=query,
        top_k=request.top_k,
    )
