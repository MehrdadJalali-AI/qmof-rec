from openai import OpenAI

from app.core.config import settings


class LLMClient:

    def __init__(self):

        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

    def generate(
        self,
        prompt: str,
    ):

        response = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert AI scientist "
                        "specialized in MOFs, "
                        "materials science, "
                        "graph neural networks, "
                        "chemistry, and QMOF analysis."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content


llm_client = LLMClient()