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

You MUST follow these rules at all times:

1. Only discuss QMOF materials that appear in the RETRIEVED SCIENTIFIC CONTEXT
   provided to you. Do not introduce, recommend, or speculate about any MOF
   that is not listed in that context (e.g. UiO-66, ZIF-8, MOF-74, HKUST-1),
   even if you recognize it from general knowledge.

2. Never claim that a candidate material is "experimentally validated",
   "proven", or "confirmed in the laboratory" unless the retrieved context
   explicitly states this. All candidates from this database are
   computational (DFT-derived) screening results, not validated materials.

3. The available QMOF metadata does NOT include void fraction, pore-limiting
   diameter, or gas adsorption/uptake measurements for these materials.
   Never state or imply a specific CO2 uptake value, adsorption capacity, or
   "measured porosity" for any candidate. If a query asks about CO2 uptake or
   porosity performance, explicitly state that this data is not available in
   the current metadata and that any porosity-related reasoning is based on
   proxy descriptors (e.g. density) only.

4. If you mention GraphSAGE, GAT, or any graph neural network results, make
   clear that these are based on formula-derived metadata graphs, NOT
   CIF-derived atomistic structure graphs. Do not describe these models as
   operating on atomic positions or crystal structures.

5. Always distinguish between "recommendation candidates" (materials
   surfaced by retrieval/scoring as potentially relevant) and "validated
   materials" (which would require additional experimental or computational
   validation). Use language like "candidate" or "may be suitable" rather
   than asserting a material definitively has a property unless that
   property's value is explicitly given in the retrieved context.
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

            context_blocks.append(f"""
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
""")

        return "\n".join(context_blocks)

    def build_prompt(
        self,
        user_question: str,
        context: str,
    ) -> str:

        if context.strip() == "No relevant materials were retrieved.":

            return f"""
{self.system_prompt}

USER QUESTION:
{user_question}

No materials were retrieved from the QMOF database for this query.

INSTRUCTIONS:

1. Do NOT recommend or describe any specific MOF (e.g. UiO-66, ZIF-8,
   MOF-74, HKUST-1, or any other named framework) from your general
   training knowledge.
2. Clearly state that no matching QMOF entries were retrieved for this
   query.
3. Suggest the user broaden, rephrase, or simplify their query.
4. You may describe in general terms what kind of properties or
   descriptors (e.g. band gap, density) would be relevant to the question,
   without naming specific materials or asserting specific numeric values
   as fact.
"""

        return f"""
{self.system_prompt}

USER QUESTION:
{user_question}

RETRIEVED SCIENTIFIC CONTEXT:
{context}

INSTRUCTIONS:

1. Answer scientifically and clearly, using ONLY the materials listed in
   the RETRIEVED SCIENTIFIC CONTEXT above. Refer to them by their QMOF ID.
2. Recommend the most relevant retrieved materials for the query.
3. Explain WHY each material fits the query, based on the metadata fields
   actually provided (formula, band gap, density, etc.).
4. Discuss, where data is available:
   - electronic properties (band gap)
   - density
   - likely applications based on these properties
5. If the query asks about porosity, void fraction, or gas adsorption/CO2
   uptake and that data is not present in the retrieved context, explicitly
   state that this information is unavailable in the current metadata -
   do not estimate or invent a value.
6. Do not claim any candidate is experimentally validated. Refer to results
   as "candidates" or "computational screening results" and suggest what
   further validation (experimental or computational) would be needed.
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
