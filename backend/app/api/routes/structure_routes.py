import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.core.security import is_valid_qmof_id, safe_join

router = APIRouter(
    prefix="/materials",
    tags=["materials"],
)


@router.get(
    "/{qmof_id}/structure",
    response_class=PlainTextResponse,
)
def get_material_structure(qmof_id: str):

    if not settings.QMOF_CIF_DIR:
        raise HTTPException(
            status_code=500,
            detail="QMOF_CIF_DIR is not configured.",
        )

    if not is_valid_qmof_id(qmof_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid material identifier.",
        )

    filename = f"{qmof_id}.cif"

    try:
        cif_path = safe_join(settings.QMOF_CIF_DIR, filename)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid material identifier.",
        )

    if not os.path.exists(cif_path):
        raise HTTPException(
            status_code=404,
            detail=f"CIF file not found for {qmof_id}",
        )

    with open(
        cif_path,
        "r",
        encoding="utf-8",
        errors="ignore",
    ) as f:
        return f.read()
