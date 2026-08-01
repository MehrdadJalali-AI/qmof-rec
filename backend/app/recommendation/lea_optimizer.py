from __future__ import annotations

from typing import Optional

import numpy as np

from app.recommendation.objective_utils import (
    ACTIVE_OBJECTIVES,
    WEIGHT_KEYS,
    masked_balance_score,
    masked_distance,
    normalize_weights,
)
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

        return list(ACTIVE_OBJECTIVES)

    def _weights(
        self,
        weights,
    ):

        normalized = normalize_weights(weights, keys=WEIGHT_KEYS)

        return np.array(
            [normalized[key] for key in WEIGHT_KEYS],
            dtype=np.float32,
        )

    def _candidate_matrix(
        self,
        materials,
    ):

        rows = []
        masks = []

        for material in materials:

            row = []
            mask = []

            availability = material.get("availability", {}) or {}

            for name in self._objective_names():

                value = sanitize_number(
                    material.get(name),
                    default=0.0,
                )

                row.append(value)

                available_key = name.replace("_score", "")
                mask.append(bool(availability.get(available_key, True)))

            rows.append(row)
            masks.append(mask)

        matrix = np.array(
            rows,
            dtype=np.float32,
        )
        availability_matrix = np.array(
            masks,
            dtype=bool,
        )

        normalized = matrix.copy()

        for col in range(matrix.shape[1]):
            observed = availability_matrix[:, col]
            if not np.any(observed):
                normalized[:, col] = 0.0
                continue

            col_values = matrix[observed, col]
            col_min = float(col_values.min())
            col_max = float(col_values.max())
            denominator = col_max - col_min

            if denominator <= 1e-8:
                normalized[observed, col] = 0.0
            else:
                normalized[observed, col] = (matrix[observed, col] - col_min) / denominator

            normalized[~observed, col] = 0.0

        return normalized, availability_matrix

    def _nearest_candidate(
        self,
        individual,
        individual_mask,
        candidate_matrix,
        availability_matrix,
    ):

        distances = [
            masked_distance(individual, row, individual_mask, mask)
            for row, mask in zip(candidate_matrix, availability_matrix)
        ]

        return int(np.argmin(distances))

    def _fitness(
        self,
        individual,
        individual_mask,
        candidate_matrix,
        availability_matrix,
        objective_weights,
        selected_vectors,
        selected_masks,
    ):

        candidate_idx = self._nearest_candidate(
            individual,
            individual_mask,
            candidate_matrix,
            availability_matrix,
        )

        objectives = candidate_matrix[candidate_idx]
        mask = availability_matrix[candidate_idx]

        active_weights = objective_weights * mask.astype(np.float32)
        weight_total = float(active_weights.sum())

        if weight_total <= 1e-8:
            weighted_score = 0.0
        else:
            weighted_score = float(np.dot(objectives, active_weights) / weight_total)

        balance_score = masked_balance_score(objectives, mask)

        diversity_score = 0.0

        redundancy_penalty = 0.0

        if selected_vectors:

            distances = [
                masked_distance(objectives, vec, mask, selected_mask)
                for vec, selected_mask in zip(selected_vectors, selected_masks)
            ]

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

        candidate_matrix, availability_matrix = self._candidate_matrix(materials)

        objective_weights = self._weights(weights)

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

        population_masks = [
            availability_matrix[i % len(availability_matrix)].copy()
            for i in range(population_size)
        ]

        fitnesses = [0.0] * population_size

        selected_vectors = []
        selected_masks = []

        best_materials = {}

        self.fitness_history = []

        for iteration in range(self.max_iterations):

            for idx, individual in enumerate(population):

                fitness, candidate_idx = self._fitness(
                    individual,
                    population_masks[idx],
                    candidate_matrix,
                    availability_matrix,
                    objective_weights,
                    selected_vectors,
                    selected_masks,
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

            best_index = int(np.argmax(fitnesses))
            best = population[best_index]

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

            ordered_so_far = sorted(
                best_materials.values(),
                reverse=True,
            )[:top_k]
            selected_vectors = [candidate_matrix[idx] for _, idx in ordered_so_far]
            selected_masks = [availability_matrix[idx] for _, idx in ordered_so_far]

        ordered = sorted(
            best_materials.values(),
            reverse=True,
        )[:top_k]

        results = []

        selected_vectors = [candidate_matrix[idx] for _, idx in ordered]
        selected_masks = [availability_matrix[idx] for _, idx in ordered]
        if len(selected_vectors) > 1:
            pairwise = []
            for i in range(len(selected_vectors)):
                for j in range(i + 1, len(selected_vectors)):
                    pairwise.append(
                        masked_distance(
                            selected_vectors[i],
                            selected_vectors[j],
                            selected_masks[i],
                            selected_masks[j],
                        )
                    )
            self.diversity_score = float(np.mean(pairwise)) if pairwise else 0.0
        else:
            self.diversity_score = 0.0

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
