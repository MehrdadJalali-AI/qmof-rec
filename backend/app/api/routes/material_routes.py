from fastapi import APIRouter, UploadFile, File

from app.services.material_service import (
    material_service,
)

router = APIRouter(
    prefix="/materials",
    tags=["materials"],
)


@router.post("/predict")
async def predict_material(
    file: UploadFile = File(...)
):

    contents = await file.read()

    result = material_service.predict_material(
        contents,
        file.filename,
    )

    return result