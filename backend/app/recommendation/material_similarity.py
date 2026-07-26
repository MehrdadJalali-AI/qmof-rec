import numpy as np

from sklearn.metrics.pairwise import (
    cosine_similarity,
)

from app.recommendation.feature_extractor import (
    feature_extractor,
)


class MaterialSimilarity:

    def similarity(
        self,
        query_material,
        candidate_material,
    ):

        q = feature_extractor.extract(query_material)

        c = feature_extractor.extract(candidate_material)

        if np.linalg.norm(q) == 0:

            return 0.0

        if np.linalg.norm(c) == 0:

            return 0.0

        try:

            score = cosine_similarity(
                [q],
                [c],
            )[
                0
            ][0]

            if np.isnan(score):

                return 0.0

            return float(score)

        except Exception:

            return 0.0


material_similarity = MaterialSimilarity()
