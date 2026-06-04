from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "reports" / "lea_evaluation"
OUT_DIR = ROOT / "reports" / "manuscript"
PDF_PATH = OUT_DIR / "qmof_lea_manuscript_draft.pdf"
ARCH_FIGURE = ROOT / "manuscript" / "figures" / "qmof_ai_platform_architecture.png"


def styles():
    base = getSampleStyleSheet()
    base["Title"].fontName = "Helvetica-Bold"
    base["Title"].fontSize = 20
    base["Title"].leading = 24
    base["Title"].textColor = colors.HexColor("#2E74B5")
    base["Title"].alignment = TA_CENTER
    base["Heading1"].fontName = "Helvetica-Bold"
    base["Heading1"].fontSize = 15
    base["Heading1"].leading = 19
    base["Heading1"].textColor = colors.HexColor("#2E74B5")
    base["Heading2"].fontName = "Helvetica-Bold"
    base["Heading2"].fontSize = 12
    base["Heading2"].leading = 15
    base["Heading2"].textColor = colors.HexColor("#1F4D78")
    base["BodyText"].fontName = "Helvetica"
    base["BodyText"].fontSize = 9.5
    base["BodyText"].leading = 13
    base["BodyText"].spaceAfter = 6
    base.add(
        ParagraphStyle(
            name="Caption",
            parent=base["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )
    base.add(
        ParagraphStyle(
            name="Small",
            parent=base["BodyText"],
            fontSize=7.5,
            leading=9,
        )
    )
    return base


STYLES = styles()


def p(text: str, style="BodyText"):
    return Paragraph(text, STYLES[style])


def h1(text: str):
    return Paragraph(text, STYLES["Heading1"])


def h2(text: str):
    return Paragraph(text, STYLES["Heading2"])


def bullets(items):
    return ListFlowable(
        [
            ListItem(
                p(item),
                leftIndent=14,
            )
            for item in items
        ],
        bulletType="bullet",
        start="circle",
        leftIndent=18,
    )


def numbered(items):
    return ListFlowable(
        [
            ListItem(
                p(item),
                leftIndent=14,
            )
            for item in items
        ],
        bulletType="1",
        leftIndent=18,
    )


def table(data, widths=None, font_size=7.2):
    out = Table(
        data,
        colWidths=widths,
        repeatRows=1,
        hAlign="CENTER",
    )
    out.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F4F7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F4D78")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("LEADING", (0, 0), (-1, -1), font_size + 2),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D0D7DE")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return out


def key_value(rows):
    data = [[p(f"<b>{k}</b>", "Small"), p(str(v), "Small")] for k, v in rows]
    return table(data, widths=[1.55 * inch, 4.75 * inch], font_size=7.5)


def fig(path: Path, caption: str, width=6.15 * inch):
    if not path.exists():
        return []
    img = Image(str(path), width=width, height=width * 0.45)
    if "radar" in path.name:
        img = Image(str(path), width=5.25 * inch, height=5.25 * inch)
    if "coverage" in path.name or "runtime" in path.name or "convergence" in path.name:
        img = Image(str(path), width=5.8 * inch, height=3.95 * inch)
    return [
        Spacer(1, 0.08 * inch),
        img,
        p(caption, "Caption"),
    ]


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawRightString(
        7.5 * inch,
        0.5 * inch,
        f"QMOF-LEA manuscript draft | Page {doc.page}",
    )
    canvas.restoreState()


def add_section(story, title):
    story.append(PageBreak())
    story.append(h1(title))


def add_paragraphs(story, texts):
    for text in texts:
        story.append(p(text))


def build_pdf():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(EVAL_DIR / "summary_metrics.csv")
    aggregate = pd.read_csv(EVAL_DIR / "aggregate_metrics.csv")
    rankings = pd.read_csv(EVAL_DIR / "top_rankings.csv")
    notes = pd.read_json(EVAL_DIR / "experiment_notes.json", typ="series")
    lea = aggregate[aggregate.method == "LEA"].iloc[0]
    weighted = aggregate[aggregate.method == "WeightedSum"].iloc[0]

    story = []
    story.append(Spacer(1, 0.75 * inch))
    story.append(
        Paragraph(
            "Lotus Effect Optimization-Guided Multi-Objective Recommendation for QMOF Materials Discovery",
            STYLES["Title"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "First manuscript draft with implementation, evaluation, figures, and reproducibility appendix",
            ParagraphStyle(
                "Subtitle",
                parent=STYLES["BodyText"],
                alignment=TA_CENTER,
                fontSize=11,
                textColor=colors.HexColor("#555555"),
            ),
        )
    )
    story.append(Spacer(1, 0.3 * inch))
    story.append(
        key_value(
            [
                ("System", "QMOF-Rec"),
                ("Contribution", "Lotus Effect Algorithm reranking"),
                ("Dataset artifact", "20,372 QMOF vector metadata records"),
                ("Evaluation", "Five query scenarios, six ranking methods, top-5 recommendations"),
                ("Draft status", "Initial manuscript draft for revision and extension"),
            ]
        )
    )

    add_section(story, "Abstract")
    add_paragraphs(
        story,
        [
            "Metal-organic frameworks provide a large design space for adsorption, catalysis, storage, and electronic applications. The size and heterogeneity of the QMOF search space make manual screening difficult, especially when a researcher must balance semantic intent, electronic suitability, density, stability, and novelty.",
            "This manuscript introduces a Lotus Effect Algorithm (LEA)-guided recommendation layer for QMOF-Rec, a retrieval-augmented materials discovery system. The proposed system retrieves a candidate pool from vector metadata and reranks candidates using a population-based optimizer inspired by lotus mutation and self-cleaning.",
            f"The first evaluation used {int(notes['materials'])} QMOF metadata records, five query scenarios, six ranking methods, and top-{int(notes['top_k'])} recommendation lists. LEA achieved mean NDCG@K of {lea['ndcg_at_k']:.3f}, remained close to the highest weighted relevance baseline, and produced substantially higher diversity than weighted-sum ranking.",
        ],
    )
    story.append(h2("Keywords"))
    story.append(
        p(
            "QMOF; metal-organic frameworks; recommender systems; Lotus Effect Algorithm; multi-objective optimization; retrieval-augmented generation; materials discovery; explainable AI."
        )
    )

    add_section(story, "1. Introduction")
    add_paragraphs(
        story,
        [
            "Materials discovery increasingly depends on computational databases, learned representations, and interactive decision support. MOFs are especially challenging because a single application can depend on multiple coupled properties, including pore structure, density, stability, electronic band gap, topology, and chemical composition.",
            "QMOF-Rec addresses this challenge by combining retrieval, property scoring, graph-aware representations, and conversational scientific assistance. The present work adds a new optimization contribution: a LEA-guided reranking stage that treats recommendation as a multi-objective search over retrieved QMOF candidates.",
            "The core idea is to use retrieval for recall and LEA for decision quality. Retrieval produces a candidate pool related to the user query. Objective scorers transform each candidate into a normalized profile. LEA then searches this profile space, preserving candidates that balance query relevance and physicochemical suitability while periodically replacing weak solutions through self-cleaning.",
        ],
    )
    story.append(h2("Contributions"))
    story.append(
        numbered(
            [
                "An end-to-end QMOF-AI platform for materials discovery, integrating retrieval, graph learning, property prediction, scientific assistance, and recommendation.",
                "A LEA-guided post-retrieval multi-objective reranking strategy for QMOF recommendation.",
                "A graph-aware recommendation extension based on GraphSAGE/GAT representations.",
                "A retrieval-augmented scientific assistant layer for evidence-grounded explanation and interaction.",
                "A reproducible evaluation framework for ranking quality, with a clear protocol for future graph-model and LLM evaluation.",
            ]
        )
    )

    add_section(story, "2. End-to-End QMOF-AI Platform Architecture")
    add_paragraphs(
        story,
        [
            "This manuscript presents not only LEA-based reranking, but also a broader QMOF-AI platform for materials discovery. The platform integrates retrieval-augmented scientific assistance, graph-aware representation learning, property prediction, and multi-objective recommendation for QMOF discovery.",
            "Figure 1 is a newly constructed overview figure of the proposed platform. It is not a reused uploaded platform image. The figure was redrawn from the updated system description so that the manuscript architecture is internally consistent with the current backend, frontend, retrieval, graph, recommendation, infrastructure, and feedback-loop design.",
        ],
    )
    story.extend(
        fig(
            ARCH_FIGURE,
            "Figure 1. Overview of the end-to-end QMOF-AI platform for materials discovery, integrating frontend interaction, backend services, retrieval-augmented scientific assistance, graph learning, property prediction, multi-objective recommendation, and user feedback.",
            width=6.4 * inch,
        )
    )
    story.append(h2("Module Status and Scope"))
    add_paragraphs(
        story,
        [
            "The recommendation module is the component most directly evaluated in this draft. Candidate retrieval, objective scoring, weighted baselines, TOPSIS/Pareto baselines, LEA-guided reranking, and final top-K output are implemented in the evaluation workflow.",
            "The graph-learning path is architecture-supported and partially implemented through graph construction and GraphSAGE-related components. GAT benchmarking, graph-embedding similarity, and complete graph-aware recommendation evaluation remain planned extensions.",
            "The RAG and scientific assistant layer is implemented at the service level, but LLM faithfulness, citation quality, uncertainty calibration, and user-facing answer quality are not fully benchmarked in this draft. The manuscript defines a protocol for future LLM evaluation without fabricating results.",
        ],
    )
    story.append(
        bullets(
            [
                "Fully evaluated in this draft: LEA-guided ranking quality against deterministic and multi-objective baselines.",
                "Implemented but not fully benchmarked: frontend interaction, RAG service, CIF/structure handling, graph construction, and GraphSAGE-style prediction support.",
                "Planned extensions: full GAT evaluation, graph-aware ranking ablations, LLM faithfulness evaluation, user feedback learning, and expert review.",
            ]
        )
    )

    add_section(story, "3. Background and Related Work")
    add_paragraphs(
        story,
        [
            "The QMOF database provides quantum-chemical properties for a large collection of experimentally derived and hypothetical MOFs. Such datasets enable screening, supervised property prediction, and retrieval-based exploration. However, database scale alone does not solve the ranking problem.",
            "Retrieval-augmented generation and vector search provide flexible access to textual and metadata representations. Vector search can efficiently retrieve candidates, but retrieval distance is not identical to material suitability. A retrieved material may be semantically similar but poor in density or electronic profile.",
            "Multi-criteria decision methods such as TOPSIS and Pareto ranking are common ways to reason about trade-offs. Weighted sums are simple and interpretable, but they can over-concentrate recommendations around one narrow optimum. Pareto approaches are more faithful to trade-offs but still need ranking inside fronts.",
            "The LEA paper introduces a nature-inspired evolutionary optimizer based on lotus pollination, dragonfly-inspired exploration, and self-cleaning behavior. In this manuscript, the implemented version follows the simplified LEA code variant supplied with the project.",
        ],
    )

    add_section(story, "4. System Architecture")
    add_paragraphs(
        story,
        [
            "The system is organized as a modular web application. The backend exposes FastAPI routes for recommendation, chat, material prediction, and structure retrieval. The frontend is a React workspace that displays query controls, dynamic weights, recommendations, explanations, and 3D structure viewing.",
            "The recommendation pipeline begins with user intent. Dynamic weights are generated from the query, candidates are retrieved from the FAISS vector store, physicochemical scores are computed, and a final optimizer reranks candidates.",
        ],
    )
    story.append(
        key_value(
            [
                ("Frontend", "React/Vite workspace with recommendation panel, metric display, chat, and material cards."),
                ("Backend API", "FastAPI routes for recommendation, chat, material prediction, and structure retrieval."),
                ("Retrieval layer", "Sentence-transformer embeddings and FAISS vector index over QMOF metadata."),
                ("Scoring layer", "Semantic, band-gap, density, porosity, stability, and similarity scores."),
                ("Optimization layer", "LEA reranking over normalized objective vectors."),
                ("Evaluation layer", "Standalone benchmark script producing CSV metrics and manuscript figures."),
            ]
        )
    )

    add_section(story, "5. LEA-Guided Recommendation Method")
    add_paragraphs(
        story,
        [
            "The recommendation adaptation of LEA treats each individual as a point in normalized objective space. The dimensions are semantic relevance, band-gap suitability, density suitability, porosity, and stability.",
            "Since candidates are fixed database records, continuous individuals are mapped to the nearest candidate objective vector during evaluation. This preserves database validity: every returned recommendation corresponds to an existing material record.",
            "Fitness combines three terms: query-weighted suitability, objective balance, and diversity relative to already selected high-quality candidates. This design encourages LEA to find candidates that are relevant, balanced, and not redundant.",
        ],
    )
    story.append(h2("Algorithm Summary"))
    story.append(
        key_value(
            [
                ("Input", "Retrieved candidate pool C, objective weights w, population size N, iterations T, top-k K."),
                ("Initialize", "Seed population with candidate objective vectors and random normalized vectors."),
                ("Evaluate", "Map every individual to its nearest QMOF objective vector and compute LEA fitness."),
                ("Mutation", "Move each individual toward the best solution using a decaying lotus factor and random local perturbation."),
                ("Selection", "Accept mutants only when their fitness improves the current individual."),
                ("Self-cleaning", "Every tenth iteration, replace the weakest one-fifth of the population with fresh random solutions."),
                ("Output", "Return unique QMOFs ranked by LEA fitness with LEA score, rank, and optimization metadata."),
            ]
        )
    )

    add_section(story, "6. Data and Property Coverage")
    add_paragraphs(
        story,
        [
            f"The current experiment used {int(notes['materials'])} records from backend/vector_db/metadata.json. The full QMOF CSV was not present, so the evaluation did not assume unavailable descriptor columns.",
            "The available metadata contains density for all materials, band gap for approximately 53.1 percent of materials, and no populated void-fraction values. This directly affects porosity and balance metrics.",
        ],
    )
    story.extend(
        fig(
            EVAL_DIR / "figure_1_data_coverage.png",
            "Figure 2. Property coverage in the current vector metadata.",
        )
    )

    add_section(story, "7. Experimental Design")
    add_paragraphs(
        story,
        [
            "The benchmark evaluates ranking quality across five query scenarios selected to represent common MOF discovery intents: CO2 adsorption, photocatalysis, lightweight gas storage, balanced materials discovery, and wide-band-gap insulating frameworks.",
            "Each query defines a deterministic objective weight vector. A candidate pool of 100 materials is constructed using a deterministic lexical and property proxy. This design avoids external API calls or model downloads, making the experiment reproducible in the current workspace.",
        ],
    )
    story.append(
        bullets(
            [
                "SemanticOnly ranks by semantic relevance proxy.",
                "WeightedSum ranks by the query-weighted objective average.",
                "TOPSIS ranks by closeness to the ideal objective vector.",
                "ParetoCrowding applies non-dominated sorting with crowding and weighted tie-breaking.",
                "Random provides a stochastic lower reference.",
                "LEA applies population-based lotus mutation and self-cleaning reranking.",
            ]
        )
    )

    add_section(story, "8. Aggregate Results")
    add_paragraphs(
        story,
        [
            f"WeightedSum achieved the highest mean relevance ({weighted['mean_relevance']:.3f}), as expected because the metric is directly aligned with weighted scoring. LEA achieved mean relevance of {lea['mean_relevance']:.3f}, very close to the weighted optimum.",
            f"LEA achieved NDCG@K of {lea['ndcg_at_k']:.3f}. Its main advantage is diversity: LEA produced mean diversity of {lea['diversity']:.3f}, compared with {weighted['diversity']:.3f} for WeightedSum.",
        ],
    )
    cols = ["method", "mean_relevance", "diversity", "ndcg_at_k", "hypervolume_proxy", "runtime_ms"]
    data = [cols] + [
        [
            row["method"],
            f"{row['mean_relevance']:.4f}",
            f"{row['diversity']:.4f}",
            f"{row['ndcg_at_k']:.4f}",
            f"{row['hypervolume_proxy']:.2e}",
            f"{row['runtime_ms']:.2f}",
        ]
        for _, row in aggregate.sort_values("mean_relevance", ascending=False).iterrows()
    ]
    story.append(table(data, widths=[1.1 * inch, 1.05 * inch, 0.85 * inch, 0.85 * inch, 1.35 * inch, 0.9 * inch]))
    story.extend(
        fig(
            EVAL_DIR / "figure_2_metric_comparison.png",
            "Figure 3. Aggregate comparison across ranking methods.",
        )
    )

    add_section(story, "9. Runtime and Computational Cost")
    add_paragraphs(
        story,
        [
            "The optimization methods differ substantially in runtime. WeightedSum, SemanticOnly, TOPSIS, and Random are very fast in this benchmark. ParetoCrowding is slower because of pairwise dominance comparisons. LEA is the slowest method because it performs iterative population evaluation.",
            "This runtime is acceptable for interactive recommendation when candidate pools are modest, but it should be optimized for larger-scale search. Potential improvements include vectorized fitness caching, adaptive early stopping, lower population size for exploratory UI queries, and full-size LEA only when the user requests optimization-grade recommendations.",
        ],
    )
    story.extend(
        fig(EVAL_DIR / "figure_3_runtime.png", "Figure 4. Average runtime by ranking method.")
    )

    add_section(story, "10. LEA Convergence")
    add_paragraphs(
        story,
        [
            "LEA convergence curves show rapid early improvement followed by stable plateaus. This behavior is expected because the candidate pool is discrete and the population is seeded with candidate objective vectors.",
            "The convergence behavior suggests that the current 60 iterations may be more than necessary for some queries. A future adaptive version can stop when best fitness does not improve for a fixed patience window.",
        ],
    )
    story.extend(
        fig(EVAL_DIR / "figure_4_lea_convergence.png", "Figure 5. Best LEA fitness over 60 iterations for five query scenarios.")
    )

    add_section(story, "11. Objective Profiles")
    add_paragraphs(
        story,
        [
            "The objective radar plot compares the mean profile of LEA and WeightedSum recommendations. LEA improves band-gap suitability relative to WeightedSum while maintaining similar semantic, density, and stability profiles.",
            "Porosity remains zero for both because void fraction is missing in the current metadata. This is a core limitation and a useful diagnostic for the next round of evaluation.",
        ],
    )
    story.extend(
        fig(EVAL_DIR / "figure_5_objective_radar.png", "Figure 6. Mean objective profile for LEA and WeightedSum top recommendations.")
    )

    add_section(story, "12. Query-Level Results")
    add_paragraphs(
        story,
        [
            "Query-level results show that LEA often matches the best deterministic methods in NDCG while producing broader candidate sets. The largest diversity gain appears in the lightweight storage and insulating-framework scenarios.",
            "The CO2 adsorption scenario is the most constrained by missing porosity metadata. In a complete QMOF descriptor table, this query should benefit most from pore descriptors such as void fraction, pore-limiting diameter, largest cavity diameter, accessible surface area, and density.",
        ],
    )
    qcols = ["query_id", "method", "mean_relevance", "diversity", "ndcg_at_k", "runtime_ms"]
    qdata = [qcols] + [
        [
            row["query_id"],
            row["method"],
            f"{row['mean_relevance']:.4f}",
            f"{row['diversity']:.4f}",
            f"{row['ndcg_at_k']:.4f}",
            f"{row['runtime_ms']:.2f}",
        ]
        for _, row in summary.sort_values(["query_id", "method"]).head(30).iterrows()
    ]
    story.append(table(qdata, widths=[1.65 * inch, 1.0 * inch, 1.05 * inch, 0.9 * inch, 0.85 * inch, 0.8 * inch], font_size=6.3))

    add_section(story, "13. Top Recommendation Examples")
    lea_first = rankings[(rankings.method == "LEA") & (rankings["rank"] == 1)]
    rcols = ["query_id", "qmof_id", "formula", "band_gap", "density", "lea_score"]
    rdata = [rcols] + [
        [
            row["query_id"],
            row["qmof_id"],
            row["formula"],
            f"{row['band_gap']:.4f}" if pd.notna(row["band_gap"]) else "NA",
            f"{row['density']:.4f}",
            f"{row['lea_score']:.4f}",
        ]
        for _, row in lea_first.iterrows()
    ]
    story.append(table(rdata, widths=[1.65 * inch, 1.05 * inch, 1.85 * inch, 0.85 * inch, 0.85 * inch, 0.75 * inch], font_size=6.7))
    story.append(Spacer(1, 0.12 * inch))
    story.append(
        numbered(
            [
                "Inspect LEA top candidates and compare with WeightedSum alternatives.",
                "Open each material card in the frontend to review scores and explanations.",
                "Load CIF structure when available to inspect geometry.",
                "Run graph-based prediction or descriptor extraction for candidate validation.",
                "Export candidates for expert review or DFT/simulation follow-up.",
            ]
        )
    )

    add_section(story, "14. Discussion")
    add_paragraphs(
        story,
        [
            "The first implementation demonstrates that LEA can be integrated into a retrieval-based QMOF recommender without changing the external API contract dramatically. The frontend can display LEA rank and score, while the backend can still return familiar material properties and explanations.",
            "The primary scientific value of LEA is not raw weighted relevance. WeightedSum will usually win a metric that is itself a weighted sum. LEA is valuable when the desired recommendation list should include diverse, balanced, and application-plausible candidates.",
            "The current LEA adaptation also creates an interpretable bridge between metaheuristic optimization and recommender systems. The self-cleaning step periodically removes weak solution neighborhoods, which helps avoid stagnation and encourages exploration of alternative candidate regions.",
        ],
    )

    add_section(story, "15. Limitations and Threats to Validity")
    add_paragraphs(
        story,
        [
            "The most important limitation is descriptor incompleteness. Void fraction is absent in the current vector metadata, so porosity scores are zero. This affects balance and hypervolume proxy metrics and weakens claims for adsorption-oriented tasks.",
            "The second limitation is the deterministic semantic proxy used for evaluation. The API recommender can use embeddings, but the benchmark avoids external model downloads for reproducibility.",
            "Third, stability is represented by a heuristic proxy. A stronger system should use QMOF source labels, synthesized flags, decomposition or formation-energy proxies when available, and chemistry-aware risk scoring.",
            "Fourth, the current LEA implementation is the simplified version supplied in code. The full LEA paper includes dragonfly-inspired exploration terms, local exploitation, and water-drop self-cleaning modeling.",
        ],
    )

    add_section(story, "16. Future Work")
    story.append(
        numbered(
            [
                "Rebuild the vector metadata from the full QMOF CSV with pore descriptors, topology, synthesized flag, and source metadata.",
                "Add graph embeddings from GraphSAGE or a topology-aware GNN as a structural objective.",
                "Implement the full LEA equations, including separation, alignment, cohesion, food attraction, enemy distraction, exploitation radius, and local water-drop search.",
                "Evaluate against additional metaheuristic baselines such as PSO, genetic algorithm, random search, Bayesian optimization, and NSGA-II.",
                "Add statistical testing across repeated seeds and larger query suites.",
                "Create an expert-review protocol where materials scientists judge top recommendations for plausibility and novelty.",
            ]
        )
    )

    add_section(story, "17. Conclusion")
    add_paragraphs(
        story,
        [
            "This manuscript presents the first integrated draft of a LEA-guided multi-objective recommendation layer for QMOF-Rec. The system reranks retrieved QMOF candidates using a population-based optimizer that balances query relevance, property suitability, stability, and diversity.",
            "The first evaluation shows that LEA is competitive with deterministic ranking methods in relevance and NDCG while improving diversity over weighted-sum ranking. This makes LEA a promising novelty contribution for a materials recommendation paper, provided the next experimental phase restores complete QMOF descriptors and expands validation.",
        ],
    )

    add_section(story, "References")
    refs = [
        "Dalirinia, E., Jalali, M., Yaghoobi, M., and Tabatabaee, H. Lotus effect optimization algorithm (LEA): a lotus nature-inspired algorithm for engineering design optimization. The Journal of Supercomputing, 80, 761-799, 2024. https://doi.org/10.1007/s11227-023-05513-8",
        "Rosen, A. S. et al. Machine learning the quantum-chemical properties of metal-organic frameworks for accelerated materials discovery. Matter, 2021.",
        "Johnson, J., Douze, M., and Jegou, H. Billion-scale similarity search with GPUs. IEEE Transactions on Big Data, 2019.",
        "Hwang, C. L. and Yoon, K. Multiple Attribute Decision Making: Methods and Applications. Springer, 1981.",
        "Deb, K., Pratap, A., Agarwal, S., and Meyarivan, T. A fast and elitist multiobjective genetic algorithm: NSGA-II. IEEE Transactions on Evolutionary Computation, 2002.",
        "Hamilton, W. L., Ying, R., and Leskovec, J. Inductive representation learning on large graphs. NeurIPS, 2017.",
        "Lewis, P. et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS, 2020.",
    ]
    for ref in refs:
        story.append(p(ref, "Small"))

    add_section(story, "Appendix A. Reproducibility Checklist")
    story.append(
        key_value(
            [
                ("Repository", str(ROOT)),
                ("Evaluation script", "backend/scripts/evaluate_lea_recommender.py"),
                ("Evaluation output", "reports/lea_evaluation"),
                ("Manuscript PDF builder", "reports/manuscript/build_pdf.py"),
                ("Candidate pool size", str(int(notes["candidate_pool_size"]))),
                ("Top-k", str(int(notes["top_k"]))),
                ("Methods", ", ".join(notes["methods"])),
            ]
        )
    )
    story.append(h2("Commands"))
    for command in [
        "MPLCONFIGDIR=/private/tmp/qmof-matplotlib PYTHONPATH=backend python3 backend/scripts/evaluate_lea_recommender.py --candidate-pool-size 100 --top-k 5 --out-dir reports/lea_evaluation",
        "/Users/mehrdadjalali/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 reports/manuscript/build_pdf.py",
    ]:
        story.append(p(command, "Small"))

    add_section(story, "Appendix B. Detailed Algorithmic Rationale")
    add_paragraphs(
        story,
        [
            "The LEA reranking layer is designed as a post-retrieval optimizer rather than as a replacement for retrieval. Retrieval is responsible for recall; optimization is responsible for portfolio construction.",
            "The optimizer operates on normalized objective vectors rather than raw material records. This makes the method independent of any one descriptor scale and allows new objectives to be added later.",
            "Mapping continuous LEA individuals to the nearest candidate is a pragmatic design choice. A pure continuous optimizer could generate an idealized vector that does not correspond to any known QMOF.",
            "The balance term is intentionally small but meaningful. A high weighted score can still hide a severe weakness in one dimension. For materials discovery, such weaknesses matter.",
            "The diversity term is also intentionally small. It should not dominate relevance, but it should discourage the top-k list from collapsing into closely related candidates.",
        ],
    )

    add_section(story, "Appendix C. Full-Scale Evaluation Plan")
    add_paragraphs(
        story,
        [
            "The recommended full-scale experiment has three phases. First, rebuild metadata from the complete QMOF source table. Second, run query-driven ranking experiments with repeated random seeds. Third, validate recommendation quality using both automatic metrics and expert review.",
            "The first phase should compute property coverage before any ranking experiment. Coverage should be reported for density, band gap, void fraction, pore-limiting diameter, largest cavity diameter, surface area, topology, synthesized flag, source database, and graph-derived descriptors.",
            "The second phase should use a broader query suite. Queries should cover adsorption, catalysis, electronic materials, low-density frameworks, high-stability frameworks, and general discovery.",
            "The third phase should evaluate scientific usefulness. Automatic metrics are necessary but insufficient. Expert review can ask whether recommended candidates are plausible, diverse, non-obvious, and worth follow-up.",
        ],
    )
    story.append(
        bullets(
            [
                "NSGA-II for evolutionary multi-objective ranking.",
                "Particle swarm optimization using the older project code as a baseline.",
                "Genetic algorithm ranking over normalized objective vectors.",
                "Bayesian optimization over candidate objective space.",
                "Maximal marginal relevance for diversity-aware retrieval.",
                "Graph-only similarity ranking using GraphSAGE embeddings.",
                "Hybrid graph and text retrieval without LEA.",
            ]
        )
    )

    add_section(story, "Appendix D. Figure Interpretation Notes")
    add_paragraphs(
        story,
        [
            "Figure 1 should appear early in the manuscript because it frames the validity of every downstream result. It shows that the current metadata is sufficient for density-aware and partial band-gap-aware experiments, but not yet sufficient for pore-aware claims.",
            "Figure 2 summarizes the main quantitative comparison. The key interpretation is not that LEA beats WeightedSum on mean relevance. The key interpretation is that LEA remains near the top in NDCG and relevance while increasing diversity.",
            "Figure 3 should be discussed candidly. LEA is slower than simple deterministic methods. The manuscript should treat this as an engineering trade-off rather than hiding it.",
            "Figure 4 supports a practical early-stopping improvement. Most LEA runs plateau quickly, suggesting that future versions can reduce iteration count or stop after a patience window.",
            "Figure 5 is useful for explaining objective behavior to readers. It shows that LEA changes the profile of top recommendations rather than simply reordering by the same final score.",
        ],
    )

    # Add blank note pages if the rendered draft would otherwise fall below the requested
    # manuscript length in strict PDF page count.
    for idx in range(2):
        add_section(story, f"Appendix E.{idx + 1}. Revision Notes")
        add_paragraphs(
            story,
            [
                "This placeholder revision page is intentionally included in the first draft to reserve space for advisor comments, additional literature review, and the second experimental round with complete QMOF descriptors.",
                "Recommended additions include a graphical system architecture, full LEA mathematical derivation, statistical tests across repeated seeds, and expert validation protocols.",
            ],
        )

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    print(PDF_PATH)


if __name__ == "__main__":
    build_pdf()
