import json
import os
from datetime import datetime

FEEDBACK_FILE = "app/feedback/query_feedback.json"


class FeedbackStore:

    def __init__(self):

        os.makedirs(
            os.path.dirname(FEEDBACK_FILE),
            exist_ok=True,
        )

        if not os.path.exists(FEEDBACK_FILE):
            with open(
                FEEDBACK_FILE,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump([], file)

    def load(self):

        try:
            with open(
                FEEDBACK_FILE,
                "r",
                encoding="utf-8",
            ) as file:
                return json.load(file)

        except Exception:
            return []

    def save(
        self,
        data,
    ):

        with open(
            FEEDBACK_FILE,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=2,
                ensure_ascii=False,
            )

    def add_feedback(
        self,
        feedback,
    ):

        data = self.load()

        feedback["created_at"] = datetime.utcnow().isoformat()

        data.append(feedback)

        self.save(data)

        return feedback


feedback_store = FeedbackStore()
