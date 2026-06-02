from dotenv import load_dotenv
import os

load_dotenv()


class Settings:

    # =========================
    # LLM SETTINGS
    # =========================

    LLM_PROVIDER = os.getenv(
        "LLM_PROVIDER",
        "openai",
    )

    OPENAI_API_KEY = os.getenv(
        "OPENAI_API_KEY",
    )

    OPENAI_MODEL = os.getenv(
        "OPENAI_MODEL",
        "gpt-4o-mini",
    )

    # =========================
    # VECTOR SEARCH
    # =========================

    VECTOR_TOP_K = int(
        os.getenv(
            "VECTOR_TOP_K",
            5,
        )
    )

    VECTOR_DB_PATH = os.getenv(
        "VECTOR_DB_PATH",
        "vector_db",
    )

    VECTOR_DIMENSION = int(
        os.getenv(
            "VECTOR_DIMENSION",
            384,
        )
    )

    VECTOR_INDEX_PATH = os.getenv(
        "VECTOR_INDEX_PATH",
        "vector_db/qmof.index",
    )

    VECTOR_METADATA_PATH = os.getenv(
        "VECTOR_METADATA_PATH",
        "vector_db/metadata.json",
    )

    # =========================
    # ML MODEL
    # =========================

    MODEL_PATH = os.getenv(
        "MODEL_PATH",
        "app/models/material_classifier.pt",
    )

    # =========================
    # GRAPH SETTINGS
    # =========================

    K_NEIGHBORS = int(
        os.getenv(
            "K_NEIGHBORS",
            8,
        )
    )

    # =========================
    # DATASET
    # =========================

    QMOF_CSV_PATH = os.getenv(
        "QMOF_CSV_PATH",
        "../qmof_database/qmof_database/qmof.csv",
    )

    # =========================
    # CORS
    # =========================

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "*",
    )

    # =========================
    # MATERIAL CLASSES
    # =========================

    CLASS_NAMES = {
        0: "Conductor",
        1: "Semiconductor",
        2: "Insulator",
    }

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )

    QMOF_CIF_DIR = os.getenv(
    "QMOF_CIF_DIR",
    )


settings = Settings()