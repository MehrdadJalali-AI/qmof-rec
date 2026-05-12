from pydantic import BaseModel
from typing import Dict, Any


class PredictionResponse(BaseModel):
    filename: str
    predicted_class_id: int
    predicted_material_type: str
    confidence: float
    class_probabilities: Dict[str, float]
    graph_statistics: Dict[str, Any]