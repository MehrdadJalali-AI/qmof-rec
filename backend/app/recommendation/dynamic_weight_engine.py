class DynamicWeightEngine:

    def generate_weights(
        self,
        query: str,
    ):

        query = query.lower()

        weights = {
            "semantic": 0.30,
            "band_gap": 0.20,
            "density": 0.15,
            "porosity": 0.20,
            "stability": 0.15,
        }

        if "photocatalysis" in query:
            weights["band_gap"] += 0.25

        if "gas adsorption" in query:
            weights["porosity"] += 0.25

        if "co2" in query:
            weights["porosity"] += 0.15

        if "stable" in query:
            weights["stability"] += 0.20

        if "lightweight" in query:
            weights["density"] += 0.20

        total = sum(weights.values())

        normalized = {
            k: round(v / total, 4)
            for k, v in weights.items()
        }

        return normalized


dynamic_weight_engine = DynamicWeightEngine()