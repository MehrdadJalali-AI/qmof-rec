from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

from app.utils.json_utils import sanitize_number


class LotusEffectOptimizer:

    def __init__(
        self,
        population_size: int = 30,
        max_iterations: int = 60,
        top_k: int = 5,
        seed: Optional[int] = 42,
    ):

        self.population_size = population_size

        self.max_iterations = max_iterations

        self.top_k = top_k

        self.rng = np.random.default_rng(seed)

        self.fitness_history = []

        self.diversity_score = 0.0

    def _objective_names(self):

        return [
            "semantic_score",
            "band_gap_score",
            "density_score",
            "porosity_score",
            "stability_score",
        ]

    def _weights(
        self,
        weights,
    ):

        raw = np.array(
            [
                sanitize_number(
                    weights.get(
                        "semantic",
                        0,
                    ),
                    default=0,
                ),
                sanitize_number(
                    weights.get(
                        "band_gap",
                        0,
                    ),
                    default=0,
                ),
                sanitize_number(
                    weights.get(
                        "density",
                        0,
                    ),
                    default=0,
                ),
                sanitize_number(
                    weights.get(
                        "porosity",
                        0,
                    ),
                    default=0,
                ),
                sanitize_number(
                    weights.get(
                        "stability",
                        0,
                    ),
                    default=0,
                ),
            ],
            dtype=np.float32,
        )

        total = float(raw.sum())

        if total <= 0:

            return np.ones_like(raw) / len(raw)

        return raw / total

    def _candidate_matrix(
        self,
        materials,
    ):

        rows = []

        for material in materials:

            row = []

            for name in self._objective_names():

                value = sanitize_number(
                    material.get(name),
                    default=0,
                )

                row.append(value)

            rows.append(row)

        matrix = np.array(
            rows,
            dtype=np.float32,
        )

        """
        normalize objectives
        avoids one metric dominating
        """

        mins = matrix.min(
            axis=0,
            keepdims=True,
        )

        maxs = matrix.max(
            axis=0,
            keepdims=True,
        )

        denominator = maxs - mins + 1e-8

        matrix = (matrix - mins) / denominator

        return matrix

    def _nearest_candidate(
        self,
        individual,
        candidate_matrix,
    ):

        distances = np.linalg.norm(
            candidate_matrix - individual,
            axis=1,
        )

        return int(np.argmin(distances))

    def _fitness(
        self,
        individual,
        candidate_matrix,
        objective_weights,
        selected_vectors,
    ):

        candidate_idx = self._nearest_candidate(
            individual,
            candidate_matrix,
        )

        objectives = candidate_matrix[candidate_idx]

        weighted_score = float(
            np.dot(
                objectives,
                objective_weights,
            )
        )

        balance_score = float(np.mean(objectives))

        diversity_score = 0

        redundancy_penalty = 0

        if selected_vectors:

            distances = [np.linalg.norm(objectives - vec) for vec in selected_vectors]

            diversity_score = float(np.mean(distances))

            redundancy_penalty = float(np.exp(-diversity_score))

        fitness = (
            weighted_score
            + 0.10 * balance_score
            + 0.10 * diversity_score
            - 0.05 * redundancy_penalty
        )

        return (
            fitness,
            candidate_idx,
        )

    def _lotus_mutation(
        self,
        individual,
        best,
        iteration,
    ):

        progress = iteration / max(
            1,
            self.max_iterations,
        )

        exploration = 1 - progress

        exploitation = progress

        noise_scale = 0.20 * exploration

        gaussian = self.rng.normal(
            loc=0,
            scale=noise_scale,
            size=len(individual),
        )

        mutant = individual + gaussian + exploitation * (best - individual)

        return np.clip(
            mutant,
            0,
            1,
        )

    def _self_cleaning(
        self,
        population,
        fitnesses,
    ):

        replace_count = max(
            1,
            int(0.15 * len(population)),
        )

        indices = np.argsort(fitnesses)[:replace_count]

        dimension = len(population[0])

        for idx in indices:

            population[idx] = self.rng.random(dimension)

    def rank(
        self,
        materials,
        weights,
        top_k=None,
    ):

        if not materials:

            return []

        if top_k is None:

            top_k = self.top_k

        candidate_matrix = self._candidate_matrix(materials)

        objective_weights = self._weights(weights)

        dimension = candidate_matrix.shape[1]

        population_size = min(
            max(
                20,
                len(materials),
            ),
            self.population_size,
        )

        population = [
            candidate_matrix[i % len(candidate_matrix)].copy()
            for i in range(population_size)
        ]

        fitnesses = [0] * population_size

        selected_vectors = []

        best_materials = {}

        self.fitness_history = []

        for iteration in range(self.max_iterations):

            for idx, individual in enumerate(population):

                fitness, candidate_idx = self._fitness(
                    individual,
                    candidate_matrix,
                    objective_weights,
                    selected_vectors,
                )

                fitnesses[idx] = fitness

                qmof_id = str(
                    materials[candidate_idx].get(
                        "qmof_id",
                        candidate_idx,
                    )
                )

                current = best_materials.get(qmof_id)

                if current is None or fitness > current[0]:

                    best_materials[qmof_id] = (
                        fitness,
                        candidate_idx,
                    )

            self.fitness_history.append(float(max(fitnesses)))

            best = population[int(np.argmax(fitnesses))]

            population = [
                self._lotus_mutation(
                    p,
                    best,
                    iteration,
                )
                for p in population
            ]

            if iteration % 10 == 0:

                self._self_cleaning(
                    population,
                    fitnesses,
                )

            selected_vectors = [
                candidate_matrix[idx]
                for _, idx in sorted(
                    best_materials.values(),
                    reverse=True,
                )[:top_k]
            ]

        ordered = sorted(
            best_materials.values(),
            reverse=True,
        )[:top_k]

        results = []

        for rank, (
            fitness,
            idx,
        ) in enumerate(
            ordered,
            start=1,
        ):

            material = dict(materials[idx])

            material["lea_rank"] = rank

            material["lea_score"] = round(
                sanitize_number(
                    fitness,
                    default=0,
                ),
                4,
            )

            material["optimization_method"] = "Lotus Effect Algorithm"

            results.append(material)

        return results


lea_optimizer = LotusEffectOptimizer()
