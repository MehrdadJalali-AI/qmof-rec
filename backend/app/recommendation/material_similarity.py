from app.recommendation.feature_extractor import (
    feature_extractor,
)

from app.recommendation.objective_utils import masked_cosine


class MaterialSimilarity:

    def similarity(
        self,
        query_material,
        candidate_material,
    ):

        q, q_mask = feature_extractor.extract_with_mask(query_material)

        c, c_mask = feature_extractor.extract_with_mask(candidate_material)

        try:

            return masked_cosine(q, c, q_mask, c_mask)

        except Exception:

            return 0.0


material_similarity = MaterialSimilarity()
