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


BAND_GAP_COLUMN = "outputs.hse06.bandgap"
BAND_GAP_SOURCE = "qmof:outputs.hse06.bandgap"
PBE_BAND_GAP_COLUMN = "outputs.pbe.bandgap"


def value_or_unavailable(value):
    if pd.isna(value):
        return None
    return value


def display_value(value):
    observed = value_or_unavailable(value)
    return "unavailable" if observed is None else observed


def build_vector_database():
    logger.info("Loading QMOF CSV from %s", settings.QMOF_CSV_PATH)

    df = pd.read_csv(settings.QMOF_CSV_PATH, low_memory=False)
    logger.info("Loaded %d rows", len(df))

    skipped = 0

    for idx, row in df.iterrows():
        try:
            # All numeric fields go through display_value() so that missing
            # values are serialized as "unavailable" rather than "nan".
            # Band gap is the HSE06 value; the source is recorded below.
            text = (
                f"Material ID: {row.get('qmof_id', '')}\n"
                f"Formula: {row.get('info.formula', '')}\n"
                f"Band Gap (HSE06): {display_value(row.get(BAND_GAP_COLUMN))}\n"
                f"Density: {display_value(row.get('info.density'))}\n"
                f"Void Fraction: {display_value(row.get('info.void_fraction'))}"
            )

            embedding = embedding_engine.encode(text)

            metadata = {
                "qmof_id": row.get("qmof_id"),
                "formula": row.get("info.formula"),
                "band_gap": value_or_unavailable(row.get(BAND_GAP_COLUMN)),
                # Provenance: "missing" band gap means no HSE06 value.
                "band_gap_source": BAND_GAP_SOURCE,
                # Kept separate; never merged into band_gap.
                "band_gap_pbe": value_or_unavailable(row.get(PBE_BAND_GAP_COLUMN)),
                "density": value_or_unavailable(row.get("info.density")),
                "void_fraction": value_or_unavailable(row.get("info.void_fraction")),
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
