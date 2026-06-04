from sentence_transformers import SentenceTransformer

from app.core.config import settings


class EmbeddingEngine:

    def __init__(self):

        self.model = SentenceTransformer(
            settings.EMBEDDING_MODEL
        )

    def encode(self, text: str):

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
        )

        return embedding.tolist()


embedding_engine = EmbeddingEngine()


def generate_embedding(text: str):

    return embedding_engine.encode(text)