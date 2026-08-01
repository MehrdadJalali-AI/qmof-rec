import numpy as np

from app.recommendation.objective_utils import is_observed, observed_float


class FeatureExtractor:

    feature_names = [
        "band_gap",
        "density",
        "stability",
    ]

    def extract_with_mask(
        self,
        material,
    ):

        values = []
        mask = []

        for name in self.feature_names:
            value = material.get(name)
            available = is_observed(value)
            values.append(float(observed_float(value, default=0.0)))
            mask.append(available)

        vector = np.array(
            values,
            dtype=np.float32,
        )

        availability_mask = np.array(
            mask,
            dtype=bool,
        )

        vector = np.nan_to_num(
            vector,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        return vector, availability_mask

    def extract(
        self,
        material,
    ):

        vector, _ = self.extract_with_mask(material)
        return vector


feature_extractor = FeatureExtractor()
