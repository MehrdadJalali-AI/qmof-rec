import os
import json
import math

import faiss
import numpy as np

from app.core.config import settings


class VectorStore:

    def __init__(self):

        self.index = faiss.IndexFlatL2(
            settings.VECTOR_DIMENSION
        )

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

            results.append({
                "score": round(safe_score, 6),
                "document": self.documents[idx],
            })

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
            print("Vector index not found.")
            return

        if not os.path.exists(settings.VECTOR_METADATA_PATH):
            print("Vector metadata not found.")
            return

        self.index = faiss.read_index(
            settings.VECTOR_INDEX_PATH
        )

        with open(
            settings.VECTOR_METADATA_PATH,
            "r",
            encoding="utf-8",
        ) as f:

            self.documents = json.load(f)

        print(
            f"Loaded {len(self.documents)} documents into vector store."
        )


vector_store = VectorStore()