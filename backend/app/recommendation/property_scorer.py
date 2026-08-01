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

        except (TypeError, ValueError):
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

        except (TypeError, ValueError):
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

        except (TypeError, ValueError):
            return 0.0


property_scorer = PropertyScorer()
