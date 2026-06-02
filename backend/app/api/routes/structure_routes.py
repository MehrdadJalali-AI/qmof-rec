import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.config import settings


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

    filename = f"{qmof_id}.cif"

    cif_path = os.path.join(
        settings.QMOF_CIF_DIR,
        filename,
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