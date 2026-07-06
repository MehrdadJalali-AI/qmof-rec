import re


# Phrases that, if present in the same sentence as a "dangerous" pattern,
# indicate the model is correctly stating data is unavailable, qualifying a
# claim, or explicitly declining to confirm something - i.e. the DESIRED
# behavior, not a hallucination.
NEGATION_MARKERS = [
    "not available",
    "unavailable",
    "not provided",
    "no data",
    "not included",
    "cannot be assessed",
    "cannot be determined",
    "is missing",
    "are missing",
    "not measured",
    "no measured",
    "not reported",
    "does not provide",
    "do not provide",
    "no information",
    "not specify",
    "cannot specify",
    "cannot be confirmed",
    "can be confirmed",  # covers "cannot ... can be confirmed" phrasing variants
    "none of the candidates",
    "not detailed",
    "not be confirmed",
    "further experimental",
    "further validation",
    "would be required",
    "is necessary to confirm",
    "i cannot provide",
    "cannot provide",
    "due to the lack",
    "due to the absence",
    "lack of relevant data",
    "absence of such data",
    "is lacking",
    "are lacking",
    "data is lacking",
    "absence of",
    "means we cannot",
    "we cannot assess",
    "cannot assess",
    "no specific data",
    "the lack of",
    "limits the ability",
    "limited information",
    "without specific data",
    "often correlates with",
    "potential gas",
    "potential co2",
    "may enhance",
    "may suggest",
    "may indicate",
    "could suggest",
    "without specific",
    "remains speculative",
    "is speculative",
]


def _sentences(text):
    return re.split(r"(?<=[.!?])\s+", text)


def _has_negation(sentence):
    return any(marker in sentence for marker in NEGATION_MARKERS)


def _flag_with_context(text, dangerous_patterns):
    """
    Returns True if any dangerous pattern appears in a sentence, AND neither
    that sentence nor its immediate neighbors contain a negation/limitation
    marker. Checking neighbors handles cases where the model states the topic
    in one sentence and the "data unavailable" caveat in an adjacent one.
    """

    sentences = _sentences(text)

    for i, sentence in enumerate(sentences):

        for pattern in dangerous_patterns:

            if pattern not in sentence:
                continue

            # Sentences that merely preview/introduce a list (e.g. "...the
            # following candidates are available regarding X and Y:\n\n###
            # Candidates\n\n1. ...") are not themselves claims about X or Y.
            # If the pattern occurs before the first colon in the sentence,
            # treat it as part of an introductory clause and skip.
            colon_index = sentence.find(":")

            if colon_index != -1 and sentence.find(pattern) < colon_index:
                continue

            window = sentences[max(0, i - 1) : i + 2]

            if any(_has_negation(s) for s in window):
                continue

            return True

    return False


class HallucinationChecker:

    def unsupported_adsorption_claim(
        self,
        generated_answer,
    ):

        text = generated_answer.lower()

        dangerous_patterns = [
            "co2 uptake",
            "measured adsorption",
            "adsorption capacity",
            "highest uptake",
            "experimental uptake",
            "validated adsorption",
            "adsorption performance",
            "gas uptake",
            "storage capacity",
        ]

        return _flag_with_context(text, dangerous_patterns)

    def experimental_validation_claim(
        self,
        generated_answer,
    ):

        text = generated_answer.lower()

        patterns = [
            "experimentally validated",
            "validated experimentally",
            "proven experimentally",
            "confirmed experimentally",
            "laboratory validated",
            "real-world validation",
            "verified experimentally",
        ]

        return _flag_with_context(text, patterns)

    def unsupported_porosity_claim(
        self,
        generated_answer,
    ):

        text = generated_answer.lower()

        patterns = [
            "highest porosity",
            "measured porosity",
            "confirmed porosity",
            "known porosity",
            "reported porosity",
            "validated porosity",
        ]

        return _flag_with_context(text, patterns)

    def graph_misrepresentation(
        self,
        generated_answer,
    ):

        text = generated_answer.lower()

        dangerous = [
            "atomistic graph",
            "cif derived graph",
            "atomic graph network",
            "structure graph neural network",
        ]

        has_graphsage = "graphsage" in text or "gat" in text

        if not has_graphsage:

            return False

        for item in dangerous:

            if item in text:

                return True

        return False

    def detect(
        self,
        generated_answer,
    ):

        unsupported_adsorption = self.unsupported_adsorption_claim(generated_answer)

        experimental_validation = self.experimental_validation_claim(generated_answer)

        unsupported_porosity = self.unsupported_porosity_claim(generated_answer)

        graph_error = self.graph_misrepresentation(generated_answer)

        hallucination = any(
            [
                unsupported_adsorption,
                experimental_validation,
                unsupported_porosity,
                graph_error,
            ]
        )

        return {
            "hallucination_detected": hallucination,
            "unsupported_adsorption_claim": unsupported_adsorption,
            "experimental_validation_claim": experimental_validation,
            "unsupported_porosity_claim": unsupported_porosity,
            "graph_misrepresentation": graph_error,
        }


hallucination_checker = HallucinationChecker()