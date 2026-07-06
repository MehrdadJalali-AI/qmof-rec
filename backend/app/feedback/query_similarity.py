import numpy as np

from app.rag.embedding_engine import (
    embedding_engine,
)


class QuerySimilarity:

    def _embedding(
        self,
        text,
    ):

        if hasattr(
            embedding_engine,
            "generate_embedding",
        ):
            return embedding_engine.generate_embedding(text)

        if hasattr(
            embedding_engine,
            "encode",
        ):
            return embedding_engine.encode(text)

        raise AttributeError(
            "Embedding engine has no generate_embedding or encode method."
        )

    def similarity(
        self,
        query_a,
        query_b,
    ):

        if not query_a or not query_b:
            return 0.0

        try:
            a = np.array(
                self._embedding(query_a),
                dtype=np.float32,
            )

            b = np.array(
                self._embedding(query_b),
                dtype=np.float32,
            )

            denominator = float(np.linalg.norm(a) * np.linalg.norm(b))

            if denominator <= 0:
                return 0.0

            score = float(np.dot(a, b) / denominator)

            if np.isnan(score) or np.isinf(score):
                return 0.0

            return max(
                0.0,
                min(
                    1.0,
                    score,
                ),
            )

        except Exception:
            return 0.0


query_similarity = QuerySimilarity()
