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
        self.fitness_history: List[float] = []
        self.diversity_score = 0.0

    def _objective_names(
        self,
    ) -> List[str]:
        return [
            "semantic_score",
            "band_gap_score",
            "density_score",
            "porosity_score",
            "stability_score",
        ]

    def _weights(
        self,
        weights: Dict[str, float],
    ) -> np.ndarray:
        raw_weights = np.array(
            [
                weights.get("semantic", 0.0),
                weights.get("band_gap", 0.0),
                weights.get("density", 0.0),
                weights.get("porosity", 0.0),
                weights.get("stability", 0.0),
            ],
            dtype=np.float32,
        )

        total = raw_weights.sum()

        if total <= 0:
            return np.ones_like(raw_weights) / len(raw_weights)

        return raw_weights / total

    def _candidate_matrix(
        self,
        materials: List[Dict],
    ) -> np.ndarray:
        rows = []

        for material in materials:
            rows.append(
                [
                    sanitize_number(
                        material.get(name),
                        default=0.0,
                    )
                    for name in self._objective_names()
                ]
            )

        return np.array(
            rows,
            dtype=np.float32,
        )

    def _nearest_candidate(
        self,
        individual: np.ndarray,
        candidate_matrix: np.ndarray,
    ) -> int:
        distances = np.linalg.norm(
            candidate_matrix - individual,
            axis=1,
        )

        return int(
            np.argmin(distances)
        )

    def _fitness(
        self,
        individual: np.ndarray,
        candidate_matrix: np.ndarray,
        objective_weights: np.ndarray,
        selected_vectors: List[np.ndarray],
    ) -> Tuple[float, int]:
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

        balance_score = float(
            np.min(objectives)
        )

        diversity_score = 0.0

        if selected_vectors:
            distances = [
                np.linalg.norm(objectives - selected)
                for selected in selected_vectors
            ]
            diversity_score = float(
                np.mean(distances)
            )

        fitness = (
            weighted_score
            + 0.12 * balance_score
            + 0.08 * diversity_score
        )

        return fitness, candidate_idx

    def _lotus_mutation(
        self,
        individual: np.ndarray,
        best: np.ndarray,
        iteration: int,
    ) -> np.ndarray:
        random_walk = self.rng.random(len(individual)) - 0.5
        lotus_factor = 0.5 + 0.3 * np.exp(
            -iteration / max(1, self.max_iterations)
        )

        mutant = (
            individual
            + lotus_factor * (best - individual)
            + self.rng.random() * random_walk
        )

        return np.clip(
            mutant,
            0.0,
            1.0,
        )

    def _self_cleaning(
        self,
        population: List[np.ndarray],
        fitnesses: List[float],
    ) -> None:
        sorted_indices = np.argsort(fitnesses)
        n_replace = max(
            1,
            self.population_size // 5,
        )

        dimension = len(population[0])

        for idx in sorted_indices[:n_replace]:
            population[idx] = self.rng.random(dimension)

    def rank(
        self,
        materials: List[Dict],
        weights: Dict[str, float],
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        if not materials:
            return []

        if top_k is None:
            top_k = self.top_k

        candidate_matrix = self._candidate_matrix(materials)
        objective_weights = self._weights(weights)
        dimension = candidate_matrix.shape[1]

        population = [
            candidate_matrix[i % len(candidate_matrix)].copy()
            if i < len(candidate_matrix)
            else self.rng.random(dimension)
            for i in range(self.population_size)
        ]

        fitnesses = [0.0] * self.population_size
        top_by_id: Dict[str, Tuple[float, int, np.ndarray]] = {}
        selected_vectors: List[np.ndarray] = []
        self.fitness_history = []

        for iteration in range(self.max_iterations):
            for i, individual in enumerate(population):
                fitness, candidate_idx = self._fitness(
                    individual,
                    candidate_matrix,
                    objective_weights,
                    selected_vectors,
                )
                fitnesses[i] = fitness

                qmof_id = str(
                    materials[candidate_idx].get(
                        "qmof_id",
                        candidate_idx,
                    )
                )

                current = top_by_id.get(qmof_id)

                if current is None or fitness > current[0]:
                    top_by_id[qmof_id] = (
                        fitness,
                        candidate_idx,
                        individual.copy(),
                    )

            self.fitness_history.append(
                max(fitnesses)
            )

            best_idx = int(
                np.argmax(fitnesses)
            )
            best = population[best_idx]

            new_population = []

            for i, individual in enumerate(population):
                mutant = self._lotus_mutation(
                    individual,
                    best,
                    iteration,
                )
                trial_fitness, trial_candidate_idx = self._fitness(
                    mutant,
                    candidate_matrix,
                    objective_weights,
                    selected_vectors,
                )

                if trial_fitness > fitnesses[i]:
                    new_population.append(mutant)
                    fitnesses[i] = trial_fitness

                    qmof_id = str(
                        materials[trial_candidate_idx].get(
                            "qmof_id",
                            trial_candidate_idx,
                        )
                    )
                    top_by_id[qmof_id] = (
                        trial_fitness,
                        trial_candidate_idx,
                        mutant.copy(),
                    )

                else:
                    new_population.append(individual)

            population = new_population

            if iteration % 10 == 0:
                self._self_cleaning(
                    population,
                    fitnesses,
                )

            selected_vectors = [
                candidate_matrix[item[1]]
                for item in sorted(
                    top_by_id.values(),
                    key=lambda item: item[0],
                    reverse=True,
                )[:top_k]
            ]

        ordered = sorted(
            top_by_id.values(),
            key=lambda item: item[0],
            reverse=True,
        )

        selected = []

        for rank, (fitness, candidate_idx, _) in enumerate(
            ordered[:top_k],
            start=1,
        ):
            material = dict(
                materials[candidate_idx]
            )
            material["lea_rank"] = rank
            material["lea_score"] = round(
                sanitize_number(fitness),
                4,
            )
            material["optimization_method"] = (
                "Lotus Effect Algorithm"
            )
            selected.append(material)

        if len(selected) > 1:
            vectors = self._candidate_matrix(selected)
            distances = [
                np.linalg.norm(a - b)
                for i, a in enumerate(vectors)
                for b in vectors[i + 1 :]
            ]
            self.diversity_score = (
                float(np.mean(distances))
                if distances
                else 0.0
            )

        return selected


lea_optimizer = LotusEffectOptimizer()
