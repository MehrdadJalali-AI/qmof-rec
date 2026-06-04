class PropertyScorer:

    def score_band_gap(
        self,
        value,
    ):

        try:
            value = float(value)

            if 1.0 <= value <= 3.5:
                return 1.0

            return 0.5

        except:
            return 0.0

    def score_density(
        self,
        value,
    ):

        try:
            value = float(value)

            if value < 1.0:
                return 1.0

            elif value < 2.0:
                return 0.7

            return 0.4

        except:
            return 0.0

    def score_porosity(
        self,
        value,
    ):

        try:
            value = float(value)

            if value > 0.7:
                return 1.0

            elif value > 0.4:
                return 0.7

            return 0.3

        except:
            return 0.0

    def score_stability(
        self,
        material,
    ):

        synthesized = material.get(
            "synthesized"
        )

        if isinstance(
            synthesized,
            bool,
        ):
            return 1.0 if synthesized else 0.4

        stability = material.get(
            "stability"
        )

        try:
            stability = float(stability)

            return max(
                0.0,
                min(
                    1.0,
                    stability,
                ),
            )

        except:
            return 0.5


property_scorer = PropertyScorer()
