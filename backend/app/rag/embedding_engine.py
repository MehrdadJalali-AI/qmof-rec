from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingEngine:
    """
    Wraps the sentence-transformer embedding model.

    The model is loaded lazily on first use rather than at import time, so
    that importing this module (e.g. from scripts or tests that don't need
    embeddings) doesn't pay the model-load cost or fail if the model can't
    be downloaded.
    """

    def __init__(self):
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._model

    def encode(self, text: str) -> list[float]:
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()


embedding_engine = EmbeddingEngine()


def generate_embedding(text: str) -> list[float]:
    return embedding_engine.encode(text)
