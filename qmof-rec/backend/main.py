import logging
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat_routes import router as chat_router
from app.api.routes.material_routes import router as material_router
from app.api.routes.recommendation_routes import router as recommendation_router
from app.api.routes.structure_routes import router as structure_router
from app.api.routes.feedback_routes import router as feedback_router

from app.core.config import settings
from app.rag.vector_store import vector_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("qmof")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting QMOF AI Platform...")

    for issue in settings.validate():
        logger.warning("Configuration issue: %s", issue)

    logger.info("Loading vector database...")
    vector_store.load()
    logger.info("Vector store ready (%d documents).", len(vector_store.documents))

    yield

    logger.info("Shutting down QMOF Platform...")


app = FastAPI(
    title="QMOF AI Materials Discovery Platform",
    version="2.0.0",
    lifespan=lifespan,
)


# CORS_ORIGINS must be an explicit list of allowed origins (see app/core/config.py).
# An empty list means no cross-origin browser requests are permitted.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(material_router)
app.include_router(recommendation_router)
app.include_router(structure_router)
app.include_router(feedback_router)


@app.get("/")
def root():
    return {
        "message": "QMOF AI Platform Running",
        "status": "healthy",
        "rag": "active",
        "vector_db": "loaded" if vector_store.documents else "empty",
    }


@app.get("/health")
def health():
    """Lightweight health check for deployment platforms (e.g. Railway)."""
    issues = settings.validate()
    return {
        "status": "ok" if not issues else "degraded",
        "issues": issues,
        "vector_db_documents": len(vector_store.documents),
    }
