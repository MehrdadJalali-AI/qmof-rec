"""
Builds the FAISS vector index and metadata file from the QMOF CSV dataset.

Usage:
    python -m scripts.build_vector_index
"""

import logging

import pandas as pd

from app.rag.vector_store import vector_store
from app.rag.embedding_engine import embedding_engine
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("qmof.build_index")


def build_vector_database():
    logger.info("Loading QMOF CSV from %s", settings.QMOF_CSV_PATH)

    df = pd.read_csv(settings.QMOF_CSV_PATH, low_memory=False)
    logger.info("Loaded %d rows", len(df))

    skipped = 0

    for idx, row in df.iterrows():
        try:
            text = (
                f"Material ID: {row.get('qmof_id', '')}\n"
                f"Formula: {row.get('info.formula', '')}\n"
                f"Band Gap: {row.get('outputs.hse06.bandgap', '')}\n"
                f"Density: {row.get('info.density', '')}\n"
                f"Void Fraction: {row.get('info.void_fraction', '')}"
            )

            embedding = embedding_engine.encode(text)

            metadata = {
                "qmof_id": row.get("qmof_id"),
                "formula": row.get("info.formula"),
                "band_gap": row.get("outputs.hse06.bandgap"),
                "density": row.get("info.density"),
                "void_fraction": row.get("info.void_fraction"),
                "text": text,
            }

            vector_store.add_document(embedding, metadata)

            if idx % 1000 == 0:
                logger.info("Processed %d / %d", idx, len(df))

        except Exception as exc:
            skipped += 1
            logger.warning("Skipping row %d: %s", idx, exc)

    logger.info(
        "Saving vector database (%d documents, %d skipped)...",
        len(vector_store.documents),
        skipped,
    )
    vector_store.save()
    logger.info("Done.")


if __name__ == "__main__":
    build_vector_database()
