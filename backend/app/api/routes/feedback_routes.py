from fastapi import APIRouter

from pydantic import BaseModel

from app.feedback.feedback_engine import (
    feedback_engine,
)

router = APIRouter()


class FeedbackRequest(BaseModel):

    query: str

    qmof_id: str

    relevance: int

    usefulness: int

    comment: str | None = None


@router.post("/feedback/")
def submit_feedback(request: FeedbackRequest):

    feedback_engine.submit(
        query=request.query,
        qmof_id=request.qmof_id,
        relevance=request.relevance,
        usefulness=request.usefulness,
        comment=request.comment,
    )

    return {"success": True, "message": "feedback stored"}
