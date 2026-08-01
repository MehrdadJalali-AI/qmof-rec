from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.constants import SUPPORTED_FILE_TYPES
from app.core.security import validate_file_extension
from app.services.material_service import material_service

router = APIRouter(
    prefix="/materials",
    tags=["materials"],
)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/predict")
async def predict_material(
    file: UploadFile = File(...),
):
    if not validate_file_extension(file.filename or "", SUPPORTED_FILE_TYPES):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed extensions: {SUPPORTED_FILE_TYPES}",
        )

    contents = await file.read()

    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File too large.",
        )

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    try:
        result = material_service.predict_material(
            contents,
            file.filename,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to process structure file: {exc}",
        )

    return result
