import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    # Naive UTC on purpose: SQLite drops tzinfo on round-trip, so mixing
    # aware/naive datetimes here would break comparisons like
    # RefreshToken.is_active after a reload from the DB. Postgres is fine
    # with naive UTC too as long as it's used consistently everywhere.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)

    queries = relationship("SavedQuery", back_populates="owner", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="owner", cascade="all, delete-orphan")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="owner", cascade="all, delete-orphan"
    )


class SavedQuery(Base):
    """A recommendation/chat query a user has run, kept for history."""

    __tablename__ = "saved_queries"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    query_text = Column(Text, nullable=False)
    query_type = Column(String, default="recommendation")  # recommendation | chat
    created_at = Column(DateTime, default=_now)

    owner = relationship("User", back_populates="queries")


class Favorite(Base):
    """A material a user has bookmarked."""

    __tablename__ = "favorites"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    qmof_id = Column(String, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)

    owner = relationship("User", back_populates="favorites")


class RefreshToken(Base):
    """
    A record of an issued refresh token, stored as a hash (never the raw
    token) so it can be looked up and revoked without the DB itself being
    a bearer-token store. A row disappearing or having revoked_at set
    invalidates that refresh token immediately, even if it hasn't expired.
    """

    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_now)
    revoked_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="refresh_tokens")

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None and self.expires_at > _now()
