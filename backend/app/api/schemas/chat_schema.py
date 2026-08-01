from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    question: str
    answer: str
    retrieved_count: int
    retrieved_materials: list[dict[str, Any]]
