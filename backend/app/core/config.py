import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Centralized application settings, loaded from environment variables.

    Required variables (no safe default; app will refuse to start without them):
        - OPENAI_API_KEY
    """

    # =========================
    # LLM SETTINGS
    # =========================
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # =========================
    # VECTOR SEARCH
    # =========================
    VECTOR_TOP_K = int(os.getenv("VECTOR_TOP_K", "5"))
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "vector_db")
    VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "384"))
    VECTOR_INDEX_PATH = os.getenv("VECTOR_INDEX_PATH", "vector_db/qmof.index")
    VECTOR_METADATA_PATH = os.getenv("VECTOR_METADATA_PATH", "vector_db/metadata.json")

    # =========================
    # ML MODEL
    # =========================
    MODEL_PATH = os.getenv("MODEL_PATH", "app/models/material_classifier.pt")

    # =========================
    # GRAPH SETTINGS
    # =========================
    K_NEIGHBORS = int(os.getenv("K_NEIGHBORS", "8"))

    # =========================
    # DATASET
    # =========================
    QMOF_CSV_PATH = os.getenv(
        "QMOF_CSV_PATH", "../qmof_database/qmof_database/qmof.csv"
    )

    # Directory containing CIF files for /materials/{qmof_id}/structure.
    # No default - must be set explicitly per environment.
    QMOF_CIF_DIR = os.getenv("QMOF_CIF_DIR")

    # =========================
    # CORS
    # =========================
    # Comma-separated list of allowed origins. "*" is rejected when combined
    # with credentials (per the CORS spec / browser enforcement), so treat it
    # as "no origins allowed" rather than silently degrading to wildcard.
    _raw_cors_origins = os.getenv("CORS_ORIGINS", "")
    CORS_ORIGINS = [
        origin.strip()
        for origin in _raw_cors_origins.split(",")
        if origin.strip() and origin.strip() != "*"
    ]

    # =========================
    # MATERIAL CLASSES
    # =========================
    CLASS_NAMES = {
        0: "Conductor",
        1: "Semiconductor",
        2: "Insulator",
    }

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # =========================
    # ENVIRONMENT
    # =========================
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    # =========================
    # DATABASE & AUTH
    # =========================
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./qmof.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    def validate(self) -> list[str]:
        """
        Returns a list of human-readable warnings/errors about missing or
        risky configuration. Does not raise - callers decide how strict to be.
        """
        issues = []

        if not self.OPENAI_API_KEY:
            issues.append("OPENAI_API_KEY is not set - LLM-backed endpoints will fail.")

        if not self.CORS_ORIGINS:
            issues.append(
                "CORS_ORIGINS is empty or '*' - no cross-origin browser requests "
                "will be allowed. Set CORS_ORIGINS to a comma-separated list of "
                "allowed origins for frontend access."
            )

        if not self.QMOF_CIF_DIR:
            issues.append(
                "QMOF_CIF_DIR is not set - /materials/{qmof_id}/structure will "
                "return 500 for all requests."
            )
        elif not os.path.isdir(self.QMOF_CIF_DIR):
            issues.append(f"QMOF_CIF_DIR does not exist: {self.QMOF_CIF_DIR}")

        if self.is_production and not os.path.exists(self.VECTOR_INDEX_PATH):
            issues.append(f"Vector index not found at {self.VECTOR_INDEX_PATH}")

        if self.is_production and self.SECRET_KEY == "dev-secret-change-me-in-production":
            issues.append("SECRET_KEY is using the insecure default - set a real secret in production.")

        return issues


settings = Settings()
