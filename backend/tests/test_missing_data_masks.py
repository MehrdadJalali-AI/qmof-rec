import numpy as np

from app.recommendation.dynamic_weight_engine import dynamic_weight_engine
from app.recommendation.feature_extractor import feature_extractor
from app.recommendation.hybrid_ranker import hybrid_ranker
from app.recommendation.lea_optimizer import LotusEffectOptimizer
from app.recommendation.material_similarity import material_similarity


def test_missing_and_genuine_zero_have_different_masks():
    missing_vector, missing_mask = feature_extractor.extract_with_mask(
        {"band_gap": None, "density": 0.0, "stability": None}
    )
    zero_vector, zero_mask = feature_extractor.extract_with_mask(
        {"band_gap": 0.0, "density": 0.0, "stability": 0.0}
    )

    assert np.allclose(missing_vector, zero_vector)
    assert missing_mask.tolist() == [False, True, False]
    assert zero_mask.tolist() == [True, True, True]


def test_dynamic_weights_exclude_porosity_even_for_co2_query():
    weights = dynamic_weight_engine.generate_weights("CO2 gas adsorption lightweight MOFs")

    assert "porosity" not in weights
    assert set(weights) == {"semantic", "band_gap", "density", "stability"}
    assert abs(sum(weights.values()) - 1.0) < 1e-3


def test_hybrid_ranker_does_not_score_unavailable_void_fraction():
    scores = hybrid_ranker.compute_score(
        material={"band_gap": 2.0, "density": 0.8, "void_fraction": None},
        weights={"semantic": 0.3, "band_gap": 0.2, "density": 0.3, "stability": 0.2},
        semantic_score=0.9,
    )

    assert scores["porosity_score"] is None
    assert scores["void_fraction_available"] is False
    assert "stability" in scores["availability"]
    assert scores["final_score"] > 0


def test_masked_similarity_is_symmetric_and_finite():
    left = {"band_gap": 2.0, "density": None, "stability": 0.5}
    right = {"band_gap": 3.0, "density": 0.0, "stability": None}

    lr = material_similarity.similarity(left, right)
    rl = material_similarity.similarity(right, left)

    assert np.isfinite(lr)
    assert np.isfinite(rl)
    assert lr == rl


def test_lea_ignores_porosity_score_when_ranking():
    materials = [
        {
            "qmof_id": "a",
            "semantic_score": 0.8,
            "band_gap_score": 0.5,
            "density_score": 0.5,
            "stability_score": 0.5,
            "porosity_score": 1.0,
            "availability": {"semantic": True, "band_gap": True, "density": True, "stability": True},
        },
        {
            "qmof_id": "b",
            "semantic_score": 0.7,
            "band_gap_score": 0.5,
            "density_score": 0.5,
            "stability_score": 0.5,
            "porosity_score": 0.0,
            "availability": {"semantic": True, "band_gap": True, "density": True, "stability": True},
        },
    ]
    optimizer = LotusEffectOptimizer(population_size=20, max_iterations=5, top_k=2, seed=1)
    ranked = optimizer.rank(
        materials=materials,
        weights={"semantic": 1.0, "band_gap": 0.0, "density": 0.0, "stability": 0.0, "porosity": 100.0},
        top_k=2,
    )

    assert ranked[0]["qmof_id"] == "a"
