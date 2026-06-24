class ExplainabilityEngine:

    def explain(
        self,
        material,
        scores,
    ):

        explanations = []

        if scores["band_gap_score"] > 0.8:
            explanations.append("Suitable electronic band gap")

        if scores["porosity_score"] > 0.8:
            explanations.append("High porosity for adsorption")

        if scores["density_score"] > 0.8:
            explanations.append("Low density structure")

        return explanations


explainability_engine = ExplainabilityEngine()
