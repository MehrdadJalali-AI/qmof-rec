from fastapi import APIRouter, UploadFile, File, HTTPException

from app.predictor import MaterialPredictor
from app.api.schemas import PredictionResponse


router = APIRouter()

predictor = MaterialPredictor()


@router.get("/health")
def health_check():
    return {
        "status": "running",
        "service": "QMOF Sparse GNN Material Classifier",
    }


@router.post("/predict", response_model=PredictionResponse)
async def predict_material(file: UploadFile = File(...)):
    if not file.filename.endswith(".cif"):
        raise HTTPException(
            status_code=400,
            detail="Only .cif files are supported.",
        )

    try:
        cif_bytes = await file.read()

        result = predictor.predict_from_cif(
            cif_bytes=cif_bytes,
            filename=file.filename,
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )