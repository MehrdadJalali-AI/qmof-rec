class ScoringRubric:
    """
    1-5 scale

    1 = poor

    5 = excellent
    """

    def groundedness_score(
        self,
        retrieved_qmof_ids,
        mentioned_qmof_ids,
    ):

        if not mentioned_qmof_ids:

            return 1

        overlap = len(set(retrieved_qmof_ids) & set(mentioned_qmof_ids))

        ratio = overlap / max(1, len(mentioned_qmof_ids))

        if ratio >= 0.9:
            return 5

        if ratio >= 0.7:
            return 4

        if ratio >= 0.5:
            return 3

        if ratio >= 0.25:
            return 2

        return 1

    def metadata_consistency_score(
        self,
        metadata_errors,
    ):

        if metadata_errors == 0:

            return 5

        if metadata_errors == 1:

            return 4

        if metadata_errors == 2:

            return 3

        if metadata_errors <= 4:

            return 2

        return 1

    def limitation_awareness_score(
        self,
        missing_descriptor_warning,
        unsupported_adsorption_claim,
    ):

        if missing_descriptor_warning and not unsupported_adsorption_claim:

            return 5

        if missing_descriptor_warning:

            return 4

        if unsupported_adsorption_claim:

            return 1

        return 3

    def explanation_quality_score(
        self,
        explanation_length,
        explanation_mentions_properties,
        explanation_mentions_uncertainty,
    ):

        score = 1

        if explanation_length > 100:

            score += 1

        if explanation_mentions_properties:

            score += 2

        if explanation_mentions_uncertainty:

            score += 1

        return min(
            5,
            score,
        )

    def hallucination_detected(
        self,
        unsupported_claims,
    ):

        return bool(unsupported_claims)


scoring_rubric = ScoringRubric()
