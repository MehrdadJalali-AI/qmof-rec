import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat_routes import router as chat_router
from app.api.routes.material_routes import router as material_router
from app.api.routes.recommendation_routes import router as recommendation_router
from app.api.routes.structure_routes import router as structure_router


from app.rag.vector_store import vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):

    print("===================================")
    print("Starting QMOF AI Platform...")
    print("===================================")

    print("Loading Vector Database...")
    vector_store.load()

    

    print("RAG System Initialized Successfully")
    print("===================================")

    yield

    print("===================================")
    print("Shutting down QMOF Platform...")
    print("===================================")


app = FastAPI(
    title="QMOF AI Materials Discovery Platform",
    version="2.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(material_router)
app.include_router(recommendation_router)
app.include_router(structure_router)

@app.get("/")
def root():

    return {
        "message": "QMOF AI Platform Running",
        "status": "healthy",
        "rag": "active",
        "vector_db": "loaded",
    }