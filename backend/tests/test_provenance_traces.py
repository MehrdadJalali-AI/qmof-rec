"""QMOF-Audit Phase A: provenance fields and execution traces.

These tests check that provenance is recorded correctly AND that recording it
changes nothing about the scores used for ranking.
"""

import json

import numpy as np

from app.recommendation.hybrid_ranker import hybrid_ranker
from app.recommendation.objective_utils import masked_distance, masked_distance_with_support
from app.recommendation.property_scorer import (
    MISSING_FALLBACK_ZERO,
    OBSERVED,
    property_scorer,
)
from app.recommendation.trace_logger import proxy_record, trace_material, write_jsonl

WEIGHTS = {"semantic": 0.3, "band_gap": 0.2, "density": 0.3, "stability": 0.2}


def _by_property(records):
    return {r["property"]: r for r in records}


def test_scorer_status_variants_return_identical_scores():
    for value in [None, float("nan"), "", 0.0, 0.5, 2.0, 3.5, 5.1]:
        assert property_scorer.score_band_gap_with_status(value)[0] == property_scorer.score_band_gap(value)
        assert property_scorer.score_density_with_status(value)[0] == property_scorer.score_density(value)


def test_missing_band_gap_is_a_recorded_fallback_not_a_low_score():
    assert property_scorer.score_band_gap_with_status(None) == (0.0, MISSING_FALLBACK_ZERO)
    assert property_scorer.score_band_gap_with_status(2.0) == (1.0, OBSERVED)
    # A genuine value outside the bin is observed, even though it scores 0.5.
    assert property_scorer.score_band_gap_with_status(0.0) == (0.5, OBSERVED)


def test_stability_without_measurement_is_labelled_density_proxy():
    scored = hybrid_ranker.compute_score({"band_gap": None, "density": 1.5}, WEIGHTS, 0.8)
    assert scored["stability_source"] == "density_proxy"
    assert scored["stability_score"] == scored["density_score"] == 0.7
    assert scored["provenance"]["band_gap"] == "missing_masked"
    assert scored["provenance"]["void_fraction"] == "missing_excluded"


def test_measured_stability_is_labelled_measured():
    scored = hybrid_ranker.compute_score({"density": 1.5, "stability": 0.9}, WEIGHTS, 0.8)
    assert scored["stability_source"] == "measured"


def test_old_stability_api_unchanged():
    assert hybrid_ranker._compute_stability_score({"density": 0.9}, 1.0, True) == (1.0, True)
    assert hybrid_ranker._compute_stability_score({}, 0.0, False) == (0.0, False)


def test_distance_support_separates_identical_from_no_evidence():
    a, b = np.array([0.2, 0.0]), np.array([0.2, 0.9])
    assert masked_distance_with_support(a, b, np.array([1, 0]), np.array([1, 1])) == (0.0, 1)
    assert masked_distance_with_support(a, b, np.array([1, 0]), np.array([0, 1])) == (0.0, 0)
    assert masked_distance(a, b, np.array([1, 0]), np.array([0, 1])) == 0.0


def test_trace_for_missing_band_gap_matches_expose_examples():
    material = {"qmof_id": "qmof-test001", "formula": "Zn2C8H4O6", "band_gap": None, "density": 1.2}
    records = _by_property(trace_material(material, {"run_id": "t", "rank": 1}))

    bg = records["band_gap"]
    # "The pipeline substituted zero because band gap was unavailable" is only
    # half true: 0.0 is stored, but it never enters ranking.
    assert bg["availability"] == "missing"
    assert bg["fallback_policy"] == "score_set_to_0.0_then_masked"
    assert bg["output_score"] == 0.0
    assert bg["used_in_ranking"] is False
    # "This material has a calculated band gap of zero" has no evidence.
    assert bg["raw_value"] is None

    stab = records["stability"]
    assert stab["evidence_type"] == "heuristic_proxy"
    assert stab["inputs"] == ["density"]
    assert stab["fallback_policy"] == "use_density_score"
    assert stab["used_in_ranking"] is True

    assert records["void_fraction"]["used_in_ranking"] is False


def test_trace_for_observed_band_gap():
    material = {"qmof_id": "qmof-test002", "formula": "CuC4O4", "band_gap": 2.75, "density": 1.77}
    bg = _by_property(trace_material(material, {"run_id": "t"}))["band_gap"]
    assert bg["availability"] == "observed"
    assert bg["raw_value"] == 2.75
    assert bg["unit"] == "eV"
    assert bg["evidence_source"] == "qmof:outputs.hse06.bandgap"
    assert bg["used_in_ranking"] is True


def test_overrides_capture_scenario_rescoring():
    material = {"qmof_id": "qmof-test004", "formula": "LiC7H8NO2", "band_gap": 5.07, "density": 0.94}
    bg = _by_property(trace_material(
        material, {"run_id": "t"},
        overrides={"band_gap": {"output_score": 1.0, "transformation": "insulating_wide_gap_v1"}},
    ))["band_gap"]
    assert bg["output_score"] == 1.0
    assert bg["transformation"] == "insulating_wide_gap_v1"
    assert bg["raw_value"] == 5.07


def test_proxy_record_marks_fallbacks():
    rec = proxy_record("proxy_a", "metadata_proxy_a_v1", ["band_gap"], 0.3, False, True, {"band_gap": "replaced by 0.0"})
    assert rec["evidence_type"] == "heuristic_proxy"
    assert rec["status"] == "derived_with_fallback"
    assert "replaced by 0.0" in rec["fallback_policy"]


def test_traces_serialize_as_jsonl(tmp_path):
    material = {"qmof_id": "qmof-test003", "formula": "C", "band_gap": float("nan"), "density": 1.0}
    path = tmp_path / "traces.jsonl"
    count = write_jsonl(path, trace_material(material, {"run_id": "t"}))
    lines = path.read_text().splitlines()
    assert count == len(lines) == 4
    assert all(json.loads(line)["trace_schema"] == "qmof-rec-trace/1" for line in lines)
