from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.db.models import Favorite, SavedQuery, User

router = APIRouter(prefix="/users/me", tags=["user-data"])


class FavoriteCreate(BaseModel):
    qmof_id: str
    note: str | None = None


class FavoriteOut(BaseModel):
    id: str
    qmof_id: str
    note: str | None = None

    class Config:
        from_attributes = True


class SavedQueryOut(BaseModel):
    id: str
    query_text: str
    query_type: str

    class Config:
        from_attributes = True


@router.get("/favorites", response_model=list[FavoriteOut])
def list_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )


@router.post("/favorites", response_model=FavoriteOut, status_code=201)
def add_favorite(
    payload: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fav = Favorite(user_id=current_user.id, qmof_id=payload.qmof_id, note=payload.note)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


@router.delete("/favorites/{favorite_id}", status_code=204)
def remove_favorite(
    favorite_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fav = (
        db.query(Favorite)
        .filter(Favorite.id == favorite_id, Favorite.user_id == current_user.id)
        .first()
    )
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()
    return None


@router.get("/history", response_model=list[SavedQueryOut])
def list_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(SavedQuery)
        .filter(SavedQuery.user_id == current_user.id)
        .order_by(SavedQuery.created_at.desc())
        .limit(50)
        .all()
    )
