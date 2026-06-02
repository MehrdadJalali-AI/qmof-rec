from typing import List, Dict, Any

from app.llm.llm_client import llm_client
from app.rag.retriever import retrieve_materials
from app.utils.json_utils import sanitize_for_json


class ScientificChatEngine:

    def __init__(self):

        self.system_prompt = """
You are an expert AI materials discovery assistant specialized in:

- Metal-Organic Frameworks (MOFs)
- QMOF database analysis
- graph neural networks
- sparse graph learning
- materials recommendation
- scientific retrieval-augmented generation (RAG)

You provide:
- scientifically grounded responses
- concise but technically accurate explanations
- material recommendations with justification
- uncertainty awareness
- research-oriented reasoning
"""

    def build_context(
        self,
        retrieved_materials: List[Dict[str, Any]],
    ) -> str:

        if not retrieved_materials:
            return "No relevant materials were retrieved."

        context_blocks = []

        for idx, item in enumerate(
            retrieved_materials,
            start=1,
        ):

            document = item.get(
                "document",
                {},
            )

            score = item.get(
                "score",
                0.0,
            )

            material_text = document.get(
                "text",
                "",
            )

            qmof_id = document.get(
                "qmof_id",
                "unknown",
            )

            formula = document.get(
                "formula",
                "unknown",
            )

            band_gap = document.get(
                "band_gap",
                "unknown",
            )

            density = document.get(
                "density",
                "unknown",
            )

            void_fraction = document.get(
                "void_fraction",
                "unknown",
            )

            context_blocks.append(
                f"""
==================================================
Candidate Material {idx}

Similarity Score:
{score}

QMOF ID:
{qmof_id}

Formula:
{formula}

Band Gap:
{band_gap}

Density:
{density}

Void Fraction:
{void_fraction}

Scientific Context:
{material_text}
==================================================
"""
            )

        return "\n".join(context_blocks)

    def build_prompt(
        self,
        user_question: str,
        context: str,
    ) -> str:

        return f"""
{self.system_prompt}

USER QUESTION:
{user_question}

RETRIEVED SCIENTIFIC CONTEXT:
{context}

INSTRUCTIONS:

1. Answer scientifically and clearly.
2. Recommend the most relevant materials.
3. Explain WHY each material fits the query.
4. Discuss:
   - electronic properties
   - porosity
   - stability
   - density
   - likely applications
5. Mention uncertainty if data is incomplete.
6. Suggest future experimental or computational validation steps.
7. Keep the answer structured and readable.
"""

    def ask(
        self,
        question: str,
        top_k: int = 5,
    ):

        retrieved_materials = retrieve_materials(
            query=question,
            top_k=top_k,
        )

        context = self.build_context(
            retrieved_materials=retrieved_materials,
        )

        prompt = self.build_prompt(
            user_question=question,
            context=context,
        )

        answer = llm_client.generate(prompt)

        response = {
            "question": str(question),
            "answer": str(answer),
            "retrieved_count": int(len(retrieved_materials)),
            "retrieved_materials": retrieved_materials,
        }

        return sanitize_for_json(response)


chat_engine = ScientificChatEngine()