import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import Token, UserCreate, UserLogin, UserOut
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    refresh_token_expiry,
    verify_password,
)
from app.db.database import get_db
from app.db.models import RefreshToken, User, _now

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User, db: Session) -> Token:
    """Create an access token + a refresh token, persisting a hash of the
    refresh token so it can be looked up/revoked server-side later."""
    jti = str(uuid.uuid4())
    refresh_token = create_refresh_token(user.id, jti)

    db.add(
        RefreshToken(
            id=jti,
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=refresh_token_expiry(),
        )
    )
    db.commit()

    return Token(
        access_token=create_access_token(user.id),
        refresh_token=refresh_token,
        user=UserOut.model_validate(user),
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_tokens(user, db)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    return _issue_tokens(user, db)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=Token)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_payload = decode_token(payload.refresh_token)
    if not token_payload or token_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    stored = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_token(payload.refresh_token))
        .first()
    )
    if not stored or not stored.is_active:
        # Either never issued by us, already used/rotated, or revoked
        # (e.g. after logout) - reject even if the JWT signature is valid.
        raise HTTPException(status_code=401, detail="Refresh token has been revoked or expired")

    user = db.query(User).filter(User.id == token_payload.get("sub")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Rotate: revoke the old refresh token and issue a brand new pair.
    # This limits how long a leaked refresh token stays useful.
    stored.revoked_at = _now()
    db.commit()

    return _issue_tokens(user, db)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    """Revoke a specific refresh token (e.g. the one held by the device
    calling logout). Safe to call even if the token is already invalid."""
    stored = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_token(payload.refresh_token))
        .first()
    )
    if stored and stored.revoked_at is None:
        stored.revoked_at = _now()
        db.commit()
    return None


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke every refresh token for the current user - use this for
    'sign out everywhere' or after a suspected credential compromise."""
    now = _now()
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id, RefreshToken.revoked_at.is_(None)
    ).update({"revoked_at": now})
    db.commit()
    return None


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
