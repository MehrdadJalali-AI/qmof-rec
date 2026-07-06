from typing import Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    """
    Supports both the legacy and current request shapes:

    Legacy:
        {"material_type": "MOF", "user_goal": "CO2 adsorption"}

    Current:
        {"query": "stable porous MOFs for CO2 adsorption"}
    """

    material_type: Optional[str] = None
    user_goal: Optional[str] = None
    query: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=50)

    def resolved_query(self) -> str:
        if self.query:
            return self.query.strip()

        material_type = self.material_type or ""
        user_goal = self.user_goal or ""
        return f"{material_type} {user_goal}".strip()
