"""Binned property scores.

The original ``score_*`` methods are unchanged so ranking results stay
identical. The ``*_with_status`` variants return the same score plus a
provenance status, so a missing value scored as 0.0 is recorded as a fallback
rather than looking like a real low score (QMOF-Audit, Phase A).
"""

OBSERVED = "observed"
MISSING_FALLBACK_ZERO = "missing_fallback_zero"

class PropertyScorer:

    # Transformation identifiers used in execution traces. Bump the suffix if a
    # binning rule changes so audits can tell old and new rules apart.
    BAND_GAP_RULE = "band_gap_bin_v1: 1.0<=bg<=3.5 -> 1.0, else 0.5"
    DENSITY_RULE = "density_bin_v1: <1.0 -> 1.0, <2.0 -> 0.7, else 0.4"
    POROSITY_RULE = "porosity_bin_v1: >0.7 -> 1.0, >0.4 -> 0.7, else 0.3"

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

    # --- provenance-aware variants -------------------------------------

    @staticmethod
    def _status(value):
        from app.recommendation.objective_utils import is_observed

        return OBSERVED if is_observed(value) else MISSING_FALLBACK_ZERO

    def score_band_gap_with_status(self, value):
        return self.score_band_gap(value), self._status(value)

    def score_density_with_status(self, value):
        return self.score_density(value), self._status(value)

    def score_porosity_with_status(self, value):
        return self.score_porosity(value), self._status(value)


property_scorer = PropertyScorer()
