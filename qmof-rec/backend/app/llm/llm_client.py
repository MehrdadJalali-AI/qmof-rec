import logging

from openai import OpenAI, OpenAIError

from app.core.config import settings

logger = logging.getLogger("qmof.llm")


class LLMClient:

    def __init__(self):
        self._client = None

    @property
    def client(self) -> OpenAI:
        """Lazily construct the OpenAI client so import-time failures are avoided."""
        if self._client is None:
            if not settings.OPENAI_API_KEY:
                raise RuntimeError(
                    "OPENAI_API_KEY is not configured. Set it in the environment "
                    "to use chat/recommendation endpoints."
                )
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert AI scientist specialized in MOFs, "
                            "materials science, graph neural networks, chemistry, "
                            "and QMOF analysis."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.2,
            )
        except OpenAIError as exc:
            logger.error("OpenAI API call failed: %s", exc)
            return (
                "The AI assistant is temporarily unavailable due to an upstream "
                "error. Please try again shortly."
            )

        return response.choices[0].message.content


llm_client = LLMClient()
