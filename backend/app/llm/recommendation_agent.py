from typing import Dict, Any, List

from app.rag.retriever import retrieve_materials
from app.llm.llm_client import llm_client
from app.utils.json_utils import sanitize_for_json


class RecommendationAgent:

    def __init__(self):

        self.system_prompt = """
You are an expert AI materials recommendation system specialized in:

- Metal Organic Frameworks (MOFs)
- QMOF database analysis
- porous materials
- semiconductors
- gas storage
- catalysis
- graph neural networks
- scientific retrieval systems

Your job:
- recommend scientifically relevant materials
- explain WHY the materials fit the user goal
- discuss properties:
  - band gap
  - density
  - porosity
  - stability
  - applications
- provide concise research-oriented reasoning
"""

    def build_context(
        self,
        retrieved_materials: List[Dict[str, Any]],
    ) -> str:

        if not retrieved_materials:
            return "No relevant materials retrieved."

        blocks = []

        for idx, item in enumerate(
            retrieved_materials,
            start=1,
        ):

            doc = item.get(
                "document",
                {},
            )

            blocks.append(
                f"""
========================
Candidate {idx}

QMOF ID:
{doc.get("qmof_id", "unknown")}

Formula:
{doc.get("formula", "unknown")}

Band Gap:
{doc.get("band_gap", "unknown")}

Density:
{doc.get("density", "unknown")}

Void Fraction:
{doc.get("void_fraction", "unknown")}

Description:
{doc.get("text", "")}

Similarity Score:
{item.get("score", 0.0)}
========================
"""
            )

        return "\n".join(blocks)

    def build_prompt(
        self,
        material_type: str,
        user_goal: str,
        context: str,
    ) -> str:

        return f"""
{self.system_prompt}

USER REQUEST:

Material Type:
{material_type}

Research Goal:
{user_goal}

RETRIEVED MATERIALS:
{context}

TASKS:

1. Recommend the BEST candidate materials.
2. Explain why each material fits the goal.
3. Discuss:
   - electronic properties
   - porosity
   - density
   - likely applications
4. Mention uncertainty if data is incomplete.
5. Keep the response scientific but concise.
"""

    def recommend(
        self,
        material_type: str,
        user_goal: str,
        top_k: int = 5,
    ):

        query = f"{material_type} {user_goal}"

        retrieved_materials = retrieve_materials(
            query=query,
            top_k=top_k,
        )

        context = self.build_context(
            retrieved_materials=retrieved_materials,
        )

        prompt = self.build_prompt(
            material_type=material_type,
            user_goal=user_goal,
            context=context,
        )

        answer = llm_client.generate(
            prompt
        )

        recommendations = []

        for item in retrieved_materials:

            doc = item.get(
                "document",
                {},
            )

            recommendations.append({

                "qmof_id": doc.get(
                    "qmof_id",
                    "unknown",
                ),

                "formula": doc.get(
                    "formula",
                    "unknown",
                ),

                "band_gap": doc.get(
                    "band_gap",
                    None,
                ),

                "density": doc.get(
                    "density",
                    None,
                ),

                "void_fraction": doc.get(
                    "void_fraction",
                    None,
                ),

                "score": item.get(
                    "score",
                    0.0,
                ),
            })

        return sanitize_for_json({

            "material_type": material_type,

            "user_goal": user_goal,

            "retrieved_count": len(
                recommendations
            ),

            "recommendations": recommendations,

            "llm_analysis": str(answer),
        })


recommendation_agent = RecommendationAgent()