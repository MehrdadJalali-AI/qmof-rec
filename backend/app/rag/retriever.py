from app.rag.embedding_engine import generate_embedding
from app.rag.vector_store import vector_store

from app.core.config import settings


def retrieve_materials(
    query: str,
    top_k: int = None,
):

    if top_k is None:
        top_k = settings.VECTOR_TOP_K

    query_embedding = generate_embedding(query)

    results = vector_store.search(
        embedding=query_embedding,
        top_k=top_k,
    )

    return results
