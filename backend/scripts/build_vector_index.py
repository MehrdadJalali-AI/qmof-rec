import pandas as pd

from app.rag.vector_store import vector_store
from app.rag.embedding_engine import embedding_engine

from app.core.config import settings


def build_vector_database():

    print("Loading QMOF CSV...")

    df = pd.read_csv(
        settings.QMOF_CSV_PATH,
        low_memory=False,
    )

    print(f"Loaded {len(df)} rows")

    for idx, row in df.iterrows():

        try:

            text = f"""
            Material ID: {row.get('qmof_id', '')}
            Formula: {row.get('info.formula', '')}
            Band Gap: {row.get('outputs.hse06.bandgap', '')}
            Density: {row.get('info.density', '')}
            Void Fraction: {row.get('info.void_fraction', '')}
            """

            embedding = embedding_engine.generate_embedding(text)

            metadata = {
                "qmof_id": row.get("qmof_id"),
                "formula": row.get("info.formula"),
                "band_gap": row.get("outputs.hse06.bandgap"),
                "density": row.get("info.density"),
                "void_fraction": row.get("info.void_fraction"),
                "text": text,
            }

            vector_store.add_document(
                embedding,
                metadata,
            )

            if idx % 1000 == 0:
                print(f"Processed {idx}")

        except Exception as e:

            print(f"Skipping row {idx}: {e}")

    print("Saving vector database...")

    vector_store.save()

    print("DONE")


if __name__ == "__main__":

    build_vector_database()