"""
Database engine + session management.

Defaults to a local SQLite file so the app runs with zero external
dependencies in development. Set DATABASE_URL to point at Postgres (or
any SQLAlchemy-supported DB) in production, e.g.:

    DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/qmof
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./qmof.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables that don't exist yet. Called once at startup."""
    from app.db import models  # noqa: F401 (ensures models are registered)

    Base.metadata.create_all(bind=engine)
