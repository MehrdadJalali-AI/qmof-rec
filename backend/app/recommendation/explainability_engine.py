class ExplainabilityEngine:

    def explain(
        self,
        material,
        scores,
    ):

        explanations = []

        if scores.get("band_gap_score", 0.0) > 0.8:
            explanations.append("Suitable electronic band gap")

        if scores.get("density_score", 0.0) > 0.8:
            explanations.append("Low density structure")

        if not scores.get("void_fraction_available", False):
            explanations.append("Void fraction unavailable; porosity is not used for numerical ranking")

        return explanations


explainability_engine = ExplainabilityEngine()
