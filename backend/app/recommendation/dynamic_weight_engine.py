from app.recommendation.objective_utils import normalize_weights


class DynamicWeightEngine:

    def generate_weights(
        self,
        query: str,
    ):

        query = query.lower()

        weights = {
            "semantic": 0.35,
            "band_gap": 0.25,
            "density": 0.20,
            "stability": 0.20,
        }

        if "photocatalysis" in query:
            weights["band_gap"] += 0.25

        if "stable" in query:
            weights["stability"] += 0.20

        if "lightweight" in query or "gas adsorption" in query or "co2" in query:
            weights["density"] += 0.15

        normalized = normalize_weights(weights)

        return {k: round(v, 4) for k, v in normalized.items()}


dynamic_weight_engine = DynamicWeightEngine()
