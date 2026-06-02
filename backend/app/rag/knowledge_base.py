import pandas as pd

from app.core.config import settings
from app.rag.embedding_engine import embedding_engine
from app.rag.vector_store import vector_store


KNOWLEDGE_BASE = []


def build_material_document(row):

    return f"""
    Material ID: {row.get('qmof_id', '')}

    MOF Name: {row.get('info.name', '')}

    Formula: {row.get('info.formula', '')}

    Metal: {row.get('info.decorated_scaffold', '')}

    Band Gap: {row.get('outputs.pbe.bandgap', '')}

    Surface Area: {row.get('outputs.pbe.surface_area_m2g', '')}

    Void Fraction: {row.get('outputs.pbe.void_fraction', '')}

    Density: {row.get('outputs.pbe.density', '')}

    Applications:
    gas separation,
    catalysis,
    carbon capture,
    semiconductors,
    energy storage
    """


def load_knowledge_base():

    global KNOWLEDGE_BASE

    print("Loading QMOF database...")

    df = pd.read_csv(settings.QMOF_CSV_PATH, low_memory=False,)

    df = df.fillna("")

    for _, row in df.iterrows():

        document = build_material_document(row)

        embedding = embedding_engine.generate_embedding(document)
        metadata = {
            "qmof_id": row.get("qmof_id", ""),
            "name": row.get("info.name", ""),
            "formula": row.get("info.formula", ""),
            "band_gap": row.get("outputs.pbe.bandgap", ""),
            "document": document,
        }

        vector_store.add_doccument(
            embedding=embedding,
            metadata=metadata,
        )

        KNOWLEDGE_BASE.append(metadata)

    print(
        f"Knowledge base loaded with {len(KNOWLEDGE_BASE)} materials."
    )