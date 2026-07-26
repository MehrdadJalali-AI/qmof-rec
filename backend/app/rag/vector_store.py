import os
import json
import math
import logging

import faiss
import numpy as np

from app.core.config import settings

logger = logging.getLogger("qmof.vector_store")


class VectorStore:

    def __init__(self):

        self.index = faiss.IndexFlatL2(settings.VECTOR_DIMENSION)

        self.documents = []

    def add_document(
        self,
        embedding,
        metadata,
    ):

        vector = np.array(
            [embedding],
            dtype=np.float32,
        )

        self.index.add(vector)

        self.documents.append(metadata)

    def search(
        self,
        embedding,
        top_k=None,
    ):

        if top_k is None:
            top_k = settings.VECTOR_TOP_K

        # Lazily load the persisted index/metadata if this VectorStore
        # instance hasn't been populated yet. main.py's FastAPI lifespan
        # calls load() explicitly at server startup, but standalone scripts
        # (evaluation, tests) import `vector_store` directly and never
        # trigger that hook - without this, search() would silently return
        # [] for every query.
        if self.index.ntotal == 0 and not self.documents:
            self.load()

        if self.index.ntotal == 0:
            return []

        vector = np.array(
            [embedding],
            dtype=np.float32,
        )

        distances, indices = self.index.search(
            vector,
            top_k,
        )

        results = []

        for distance, idx in zip(
            distances[0],
            indices[0],
        ):

            if idx < 0:
                continue

            if idx >= len(self.documents):
                continue

            safe_score = float(distance)

            if math.isnan(safe_score):
                safe_score = 0.0

            if math.isinf(safe_score):
                safe_score = 0.0

            results.append(
                {
                    "score": round(safe_score, 6),
                    "document": self.documents[idx],
                }
            )

        return results

    def save(self):

        os.makedirs(
            os.path.dirname(settings.VECTOR_INDEX_PATH),
            exist_ok=True,
        )

        faiss.write_index(
            self.index,
            settings.VECTOR_INDEX_PATH,
        )

        with open(
            settings.VECTOR_METADATA_PATH,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                self.documents,
                f,
                indent=2,
                ensure_ascii=False,
            )

    def load(self):

        if not os.path.exists(settings.VECTOR_INDEX_PATH):
            logger.warning("Vector index not found at %s", settings.VECTOR_INDEX_PATH)
            return

        if not os.path.exists(settings.VECTOR_METADATA_PATH):
            logger.warning(
                "Vector metadata not found at %s", settings.VECTOR_METADATA_PATH
            )
            return

        self.index = faiss.read_index(settings.VECTOR_INDEX_PATH)

        with open(
            settings.VECTOR_METADATA_PATH,
            "r",
            encoding="utf-8",
        ) as f:

            self.documents = json.load(f)

        logger.info("Loaded %d documents into vector store.", len(self.documents))


vector_store = VectorStore()
