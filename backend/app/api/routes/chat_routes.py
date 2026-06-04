from fastapi import APIRouter

from app.api.schemas.chat_schema import (
    ChatRequest,
)

from app.services.chat_service import (
    chat_service,
)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


@router.post("/")
def ask_question(request: ChatRequest):

    return chat_service.ask(
        request.question
    )