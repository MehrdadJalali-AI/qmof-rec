import copy
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_extended_evaluation as extended
import run_final_diversity_aware_masked_protocol as protocol


def config():
    return json.loads((ROOT / "configs/final_diversity_aware_masked_protocol.json").read_text())


def candidates():
    metadata = [
        {
            "qmof_id": f"qmof-{index}",
            "formula": formula,
            "band_gap": None if index == 0 else 0.8 + index * 0.4,
            "density": 0.7 + index * 0.2,
            "void_fraction": None,
            "text": "porous stable framework",
        }
        for index, formula in enumerate(["C8H4O4Zn", "C6H4N2Cu", "C9H6O6Co", "C10H8N2Ni", "C7H5O5Fe", "C12H8O4Ti", "C5H3N3Cd", "C11H7O6Mg"])
    ]
    ranges = protocol.physical_ranges(metadata)
    query_def = config()["query_scenarios"][0]
    weights = protocol.dynamic_weight_engine.generate_weights(query_def["query"])
    scored = [protocol.score_record(row, query_def["query_id"], query_def["query"], weights, ranges) for row in metadata]
    return scored, weights, query_def


def test_proxy_a_missing_band_gap_fallback_matches_zero_contribution():
    missing = {"formula": "C8H4O4Zn", "density": 1.2, "band_gap": None}
    zero = {"formula": "C8H4O4Zn", "density": 1.2, "band_gap": 0.0}
    assert protocol.metadata_proxy(missing, "a") == protocol.metadata_proxy(zero, "a")


def test_co2_query_does_not_match_cobalt_formula_or_formula_label():
    cobalt = {
        "formula": "Co2C22H16N4O10",
        "text": "Material ID: example\nFormula: Co2C22H16N4O10\nDensity: 1.2",
    }
    assert protocol.semantic_overlap(cobalt, "stable porous MOFs for CO2 adsorption") == 0.0


def test_co2_query_matches_explicit_co2_text_token():
    explicit = {
        "formula": "Zn4O",
        "text": "Candidate discussed for CO2 adsorption in a separate textual annotation",
    }
    assert protocol.semantic_overlap(explicit, "CO2 adsorption") == 1.0


def test_candidate_pool_is_deterministic_for_a_seed():
    rows, _, query_def = candidates()
    first = protocol.candidate_pool(rows, query_def["query_id"], query_def["query"], 42, 6)
    second = protocol.candidate_pool(rows, query_def["query_id"], query_def["query"], 42, 6)
    assert [row["qmof_id"] for row in first] == [row["qmof_id"] for row in second]


def test_mmr_stops_at_k_with_unique_candidates():
    rows, _, _ = candidates()
    cfg = config()
    ranked = protocol.mmr_top_k(rows, cfg, "hybrid_material")
    assert len(ranked) == cfg["top_k"]
    assert len({row["qmof_id"] for row in ranked}) == cfg["top_k"]


def test_lea_modes_are_explicit_and_return_unique_top_k():
    rows, weights, query_def = candidates()
    cfg = config()
    methods = protocol.run_methods(rows, weights, query_def["query_id"], query_def["query"], 42, cfg, "hybrid_material")
    for name in ["LEA", "LEA gamma=0 only", "LEA true no diversity", "LEA no self-cleaning"]:
        assert name in methods
        top = methods[name].ranked[: cfg["top_k"]]
        assert len({row["qmof_id"] for row in top}) == cfg["top_k"]


def test_true_no_diversity_sets_both_coefficients_to_zero():
    cfg = config()
    true_none = copy.deepcopy(cfg)
    true_none["lea_parameters"]["gamma"] = 0.0
    true_none["lea_parameters"]["redundancy_penalty"] = 0.0
    gamma_only = copy.deepcopy(cfg)
    gamma_only["lea_parameters"]["gamma"] = 0.0
    assert (true_none["lea_parameters"]["gamma"], true_none["lea_parameters"]["redundancy_penalty"]) == (0.0, 0.0)
    assert (gamma_only["lea_parameters"]["gamma"], gamma_only["lea_parameters"]["redundancy_penalty"]) == (0.0, 0.05)


def test_de_returns_exactly_k_unique_candidates():
    rows, weights, _ = candidates()
    ranked, diagnostics = extended.de_portfolio(rows, weights, 42, config())
    assert len(ranked) == config()["top_k"]
    assert len({row["qmof_id"] for row in ranked}) == config()["top_k"]
    assert diagnostics["function_evaluations"] == 1800


def test_sensitivity_grid_has_35_configurations():
    assert len(extended.GAMMAS) == 7
    assert len(extended.PENALTIES) == 5
    assert len(extended.GAMMAS) * len(extended.PENALTIES) == 35
