from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
from pathlib import Path
from typing import Dict, List

os.environ.setdefault(
    "MPLCONFIGDIR",
    "/private/tmp/qmof-matplotlib",
)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app.evaluation.baselines import (
    OBJECTIVE_COLUMNS,
    rank_pareto_crowding,
    rank_random,
    rank_semantic_only,
    rank_topsis,
    rank_weighted_sum,
)
from app.evaluation.metrics import evaluate_ranking
from app.evaluation.query_suite import QUERY_SUITE
from app.recommendation.lea_optimizer import LotusEffectOptimizer


def safe_float(
    value,
    default: float = 0.0,
) -> float:
    try:
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except Exception:
        return default


def score_band_gap(
    value,
    mode: str,
) -> float:
    value = safe_float(
        value,
        default=np.nan,
    )

    if math.isnan(value):
        return 0.0

    if mode == "wide":
        return min(
            1.0,
            max(
                0.0,
                value / 5.0,
            ),
        )

    if 1.0 <= value <= 3.5:
        return 1.0

    if value < 1.0:
        return max(
            0.2,
            value,
        )

    return max(
        0.2,
        1.0 - min(
            1.0,
            (value - 3.5) / 3.5,
        ),
    )


def score_density(
    value,
) -> float:
    value = safe_float(
        value,
        default=np.nan,
    )

    if math.isnan(value):
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            1.0 - (value / 4.0),
        ),
    )


def score_porosity(
    value,
) -> float:
    value = safe_float(
        value,
        default=np.nan,
    )

    if math.isnan(value):
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            value,
        ),
    )


def formula_tokens(
    formula: str,
) -> List[str]:
    return [
        token.lower()
        for token in re.findall(
            r"[A-Z][a-z]?",
            formula or "",
        )
    ]


def semantic_proxy(
    material: Dict,
    query: Dict,
) -> float:
    text = (
        str(material.get("text", ""))
        + " "
        + str(material.get("formula", ""))
    ).lower()
    keywords = query.get("keywords", [])
    keyword_hits = sum(
        1
        for keyword in keywords
        if keyword.lower() in text
    )

    band_gap = safe_float(
        material.get("band_gap"),
        default=np.nan,
    )
    density = safe_float(
        material.get("density"),
        default=np.nan,
    )
    formula = material.get("formula") or ""
    metals = formula_tokens(formula)

    property_signal = 0.0

    if "band" in keywords or "gap" in keywords:
        property_signal += 0.5 if not math.isnan(band_gap) else 0.0

    if "density" in keywords or "lightweight" in keywords:
        property_signal += score_density(density)

    if "co2" in keywords or "adsorption" in keywords:
        property_signal += 0.2 if any(
            element in metals
            for element in ["cu", "zn", "co", "ni", "mg"]
        ) else 0.0

    score = (
        keyword_hits / max(1, len(keywords))
        + property_signal
    )

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


def stability_proxy(
    material: Dict,
) -> float:
    formula = material.get("formula") or ""
    elements = formula_tokens(formula)

    benign_metals = {
        "zn",
        "cu",
        "co",
        "ni",
        "mg",
        "zr",
        "fe",
        "al",
    }
    heavy_penalty = {
        "pb",
        "hg",
        "cd",
    }

    score = 0.5

    if any(element in benign_metals for element in elements):
        score += 0.25

    if any(element in heavy_penalty for element in elements):
        score -= 0.25

    if safe_float(material.get("density"), default=9.0) < 2.0:
        score += 0.1

    return max(
        0.0,
        min(
            1.0,
            score,
        ),
    )


def build_candidate_pool(
    materials: List[Dict],
    query: Dict,
    candidate_pool_size: int,
) -> List[Dict]:
    band_gap_mode = (
        "wide"
        if "wide" in query["query"].lower()
        or "insulating" in query["query"].lower()
        else "suitable"
    )

    candidates = []

    for material in materials:
        candidate = dict(material)
        candidate["semantic_score"] = semantic_proxy(
            material,
            query,
        )
        candidate["band_gap_score"] = score_band_gap(
            material.get("band_gap"),
            band_gap_mode,
        )
        candidate["density_score"] = score_density(
            material.get("density")
        )
        candidate["porosity_score"] = score_porosity(
            material.get("void_fraction")
        )
        candidate["stability_score"] = stability_proxy(
            material
        )
        candidates.append(candidate)

    weight_vector = np.array(
        [
            query["weights"].get("semantic", 0.0),
            query["weights"].get("band_gap", 0.0),
            query["weights"].get("density", 0.0),
            query["weights"].get("porosity", 0.0),
            query["weights"].get("stability", 0.0),
        ],
        dtype=np.float32,
    )
    weight_vector = weight_vector / weight_vector.sum()

    matrix = np.array(
        [
            [
                candidate[column]
                for column in OBJECTIVE_COLUMNS
            ]
            for candidate in candidates
        ],
        dtype=np.float32,
    )
    retrieval_scores = (
        0.55 * matrix[:, 0]
        + 0.45 * (matrix @ weight_vector)
    )
    order = np.argsort(retrieval_scores)[::-1]

    return [
        candidates[int(idx)]
        for idx in order[:candidate_pool_size]
    ]


def load_materials(
    metadata_path: Path,
) -> List[Dict]:
    with metadata_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


def run_method(
    method: str,
    candidates: List[Dict],
    weights: Dict[str, float],
    top_k: int,
    seed: int,
) -> tuple[List[Dict], float, List[float]]:
    started = time.perf_counter()
    history: List[float] = []

    if method == "SemanticOnly":
        ranked = rank_semantic_only(candidates, top_k)
    elif method == "WeightedSum":
        ranked = rank_weighted_sum(candidates, weights, top_k)
    elif method == "TOPSIS":
        ranked = rank_topsis(candidates, weights, top_k)
    elif method == "ParetoCrowding":
        ranked = rank_pareto_crowding(candidates, weights, top_k)
    elif method == "Random":
        ranked = rank_random(candidates, top_k, seed)
    elif method == "LEA":
        optimizer = LotusEffectOptimizer(
            population_size=30,
            max_iterations=60,
            top_k=top_k,
            seed=seed,
        )
        ranked = optimizer.rank(
            candidates,
            weights,
            top_k=top_k,
        )
        for item in ranked:
            item["method"] = "LEA"
            item["rank"] = item.get("lea_rank", item.get("rank"))
        history = optimizer.fitness_history
    else:
        raise ValueError(
            f"Unknown method: {method}"
        )

    elapsed_ms = (
        time.perf_counter() - started
    ) * 1000.0

    return ranked, elapsed_ms, history


def plot_metric_bars(
    summary: pd.DataFrame,
    out_dir: Path,
) -> None:
    metrics = [
        "mean_relevance",
        "balance",
        "diversity",
        "ndcg_at_k",
        "hypervolume_proxy",
    ]
    grouped = summary.groupby("method")[metrics].mean()

    fig, axes = plt.subplots(
        1,
        len(metrics),
        figsize=(18, 4),
    )

    for ax, metric in zip(axes, metrics):
        grouped[metric].sort_values().plot(
            kind="barh",
            ax=ax,
            color="#3b6ea8",
        )
        ax.set_title(metric.replace("_", " ").title())
        ax.set_xlabel("Mean value")
        ax.grid(
            axis="x",
            alpha=0.25,
        )

    fig.tight_layout()
    fig.savefig(
        out_dir / "figure_2_metric_comparison.png",
        dpi=220,
    )
    plt.close(fig)


def plot_runtime(
    summary: pd.DataFrame,
    out_dir: Path,
) -> None:
    grouped = summary.groupby("method")["runtime_ms"].mean()

    fig, ax = plt.subplots(
        figsize=(7, 4),
    )
    grouped.sort_values().plot(
        kind="bar",
        ax=ax,
        color="#6b8e4e",
    )
    ax.set_ylabel("Runtime (ms)")
    ax.set_title("Average Runtime by Ranking Method")
    ax.grid(
        axis="y",
        alpha=0.25,
    )
    fig.tight_layout()
    fig.savefig(
        out_dir / "figure_3_runtime.png",
        dpi=220,
    )
    plt.close(fig)


def plot_lea_convergence(
    convergence: pd.DataFrame,
    out_dir: Path,
) -> None:
    fig, ax = plt.subplots(
        figsize=(7, 4),
    )

    for query_id, group in convergence.groupby("query_id"):
        ax.plot(
            group["iteration"],
            group["best_fitness"],
            label=query_id.replace("_", " "),
            linewidth=1.8,
        )

    ax.set_xlabel("Iteration")
    ax.set_ylabel("Best LEA fitness")
    ax.set_title("LEA Convergence Across Query Scenarios")
    ax.grid(alpha=0.25)
    ax.legend(
        fontsize=7,
        ncol=2,
    )
    fig.tight_layout()
    fig.savefig(
        out_dir / "figure_4_lea_convergence.png",
        dpi=220,
    )
    plt.close(fig)


def plot_objective_radar(
    rankings: pd.DataFrame,
    out_dir: Path,
) -> None:
    lea = rankings[rankings["method"] == "LEA"]
    weighted = rankings[rankings["method"] == "WeightedSum"]
    labels = OBJECTIVE_COLUMNS
    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False,
    ).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(
        figsize=(6.5, 6.5),
        subplot_kw={"projection": "polar"},
    )

    for method, data, color in [
        ("LEA", lea, "#c7522a"),
        ("WeightedSum", weighted, "#3b6ea8"),
    ]:
        values = [
            data[column].mean()
            for column in labels
        ]
        values += values[:1]
        ax.plot(
            angles,
            values,
            label=method,
            color=color,
            linewidth=2,
        )
        ax.fill(
            angles,
            values,
            color=color,
            alpha=0.12,
        )

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(
        [
            label.replace("_score", "").replace("_", " ")
            for label in labels
        ],
        fontsize=8,
    )
    ax.set_ylim(0, 1)
    ax.set_title(
        "Mean Objective Profile of Top Recommendations",
        pad=28,
        fontsize=13,
    )
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=True,
    )
    fig.tight_layout()
    fig.savefig(
        out_dir / "figure_5_objective_radar.png",
        dpi=220,
    )
    plt.close(fig)


def plot_data_coverage(
    materials: List[Dict],
    out_dir: Path,
) -> None:
    labels = [
        "density",
        "band_gap",
        "void_fraction",
    ]
    coverage = []

    for label in labels:
        present = 0

        for material in materials:
            value = safe_float(
                material.get(label),
                default=np.nan,
            )
            if not math.isnan(value):
                present += 1

        coverage.append(
            present / len(materials)
        )

    fig, ax = plt.subplots(
        figsize=(6, 4),
    )
    ax.bar(
        labels,
        coverage,
        color=["#6b8e4e", "#3b6ea8", "#c7522a"],
    )
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Available fraction")
    ax.set_title("Vector Metadata Property Coverage")
    ax.grid(
        axis="y",
        alpha=0.25,
    )

    for idx, value in enumerate(coverage):
        ax.text(
            idx,
            min(value + 0.035, 1.06),
            f"{value:.1%}",
            ha="center",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(
        out_dir / "figure_1_data_coverage.png",
        dpi=220,
    )
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("backend/vector_db/metadata.json"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("reports/lea_evaluation"),
    )
    parser.add_argument(
        "--candidate-pool-size",
        type=int,
        default=250,
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )
    args = parser.parse_args()

    args.out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    materials = load_materials(args.metadata)
    methods = [
        "SemanticOnly",
        "WeightedSum",
        "TOPSIS",
        "ParetoCrowding",
        "Random",
        "LEA",
    ]

    summary_rows = []
    ranking_rows = []
    convergence_rows = []

    for query_index, query in enumerate(QUERY_SUITE):
        pool = build_candidate_pool(
            materials,
            query,
            args.candidate_pool_size,
        )

        for method in methods:
            ranked, runtime_ms, history = run_method(
                method,
                pool,
                query["weights"],
                args.top_k,
                args.seed + query_index,
            )
            metrics = evaluate_ranking(
                ranked,
                pool,
                query["weights"],
                args.top_k,
            )
            summary_rows.append(
                {
                    "query_id": query["query_id"],
                    "query": query["query"],
                    "method": method,
                    "runtime_ms": runtime_ms,
                    **metrics,
                }
            )

            for item in ranked:
                ranking_rows.append(
                    {
                        "query_id": query["query_id"],
                        "query": query["query"],
                        "method": method,
                        "rank": item.get("rank", item.get("lea_rank")),
                        "qmof_id": item.get("qmof_id"),
                        "formula": item.get("formula"),
                        "band_gap": item.get("band_gap"),
                        "density": item.get("density"),
                        "void_fraction": item.get("void_fraction"),
                        **{
                            column: item.get(column, 0.0)
                            for column in OBJECTIVE_COLUMNS
                        },
                        "lea_score": item.get("lea_score", ""),
                        "baseline_score": item.get("baseline_score", ""),
                    }
                )

            for iteration, best_fitness in enumerate(history):
                convergence_rows.append(
                    {
                        "query_id": query["query_id"],
                        "iteration": iteration,
                        "best_fitness": best_fitness,
                    }
                )

    summary = pd.DataFrame(summary_rows)
    rankings = pd.DataFrame(ranking_rows)
    convergence = pd.DataFrame(convergence_rows)

    summary.to_csv(
        args.out_dir / "summary_metrics.csv",
        index=False,
    )
    rankings.to_csv(
        args.out_dir / "top_rankings.csv",
        index=False,
    )
    convergence.to_csv(
        args.out_dir / "lea_convergence.csv",
        index=False,
    )

    aggregate = (
        summary.groupby("method")
        .mean(numeric_only=True)
        .reset_index()
    )
    aggregate.to_csv(
        args.out_dir / "aggregate_metrics.csv",
        index=False,
    )

    plot_data_coverage(
        materials,
        args.out_dir,
    )
    plot_metric_bars(
        summary,
        args.out_dir,
    )
    plot_runtime(
        summary,
        args.out_dir,
    )
    plot_lea_convergence(
        convergence,
        args.out_dir,
    )
    plot_objective_radar(
        rankings,
        args.out_dir,
    )

    notes = {
        "materials": len(materials),
        "query_count": len(QUERY_SUITE),
        "candidate_pool_size": args.candidate_pool_size,
        "top_k": args.top_k,
        "methods": methods,
        "limitations": [
            "Evaluation uses metadata.json because qmof.csv is not present in the workspace.",
            "Void fraction is absent in the current vector metadata, so porosity is a placeholder objective in this run.",
            "Semantic relevance is evaluated with a deterministic lexical/property proxy to avoid external model downloads.",
        ],
    }
    with (
        args.out_dir / "experiment_notes.json"
    ).open("w", encoding="utf-8") as handle:
        json.dump(
            notes,
            handle,
            indent=2,
        )

    print(
        f"Wrote evaluation outputs to {args.out_dir}"
    )


if __name__ == "__main__":
    main()
