import re


class MetadataChecker:

    def extract_qmof_ids(
        self,
        text,
    ):

        if not text:

            return []

        # Real QMOF IDs look like "qmof-8a95c27" (7-character lowercase hex
        # suffix). The previous pattern (QMOF[-_]?\d+) only matched purely
        # numeric suffixes and never matched real IDs, which silently broke
        # groundedness scoring.
        pattern = r"qmof[-_][0-9a-f]{6,8}"

        found = re.findall(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        cleaned = [item.lower() for item in found]

        return list(set(cleaned))

    def check_metadata_consistency(
        self,
        generated_answer,
        retrieved_materials,
    ):

        errors = 0

        metadata_used = []

        mentioned_qmof_ids = self.extract_qmof_ids(generated_answer)

        retrieved_lookup = {
            str(item.get("qmof_id", "")).lower(): item for item in retrieved_materials
        }

        for qmof_id in mentioned_qmof_ids:

            if qmof_id not in retrieved_lookup:

                # The LLM referenced a QMOF ID that wasn't in the retrieved
                # context - this is a genuine grounding/consistency error.
                errors += 1

                continue

            material = retrieved_lookup[qmof_id]

            formula = str(material.get("formula", ""))

            density = material.get("density")

            band_gap = material.get("band_gap")

            # Track which metadata fields were *available* for mentioned
            # materials (used for explanation-quality scoring). Whether the
            # answer restates each field verbatim is a completeness/style
            # consideration, not a correctness error - an answer can
            # correctly summarize multiple candidates without repeating
            # every formula for every one of them.
            if formula:

                metadata_used.append("formula")

            if density is not None:

                metadata_used.append("density")

            if band_gap is not None:

                metadata_used.append("band_gap")

        return {
            "metadata_errors": errors,
            "mentioned_qmof_ids": mentioned_qmof_ids,
            "metadata_fields_used": sorted(list(set(metadata_used))),
        }

    def missing_descriptor_warning(
        self,
        generated_answer,
    ):

        keywords = [
            "missing",
            "unavailable",
            "not provided",
            "cannot verify",
            "insufficient data",
            "not available",
        ]

        text = generated_answer.lower()

        for keyword in keywords:

            if keyword in text:

                return True

        return False


metadata_checker = MetadataChecker()