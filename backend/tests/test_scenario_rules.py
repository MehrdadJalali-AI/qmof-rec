import json
import sys
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import run_final_diversity_aware_masked_protocol as p
from app.recommendation.dynamic_weight_engine import dynamic_weight_engine as engine

@pytest.mark.parametrize("query,rule", [("photocatalytic", "photocatalysis"), ("photocatalyst", "photocatalysis"), ("insulating", "insulating_frameworks"), ("wide-band-gap", "insulating_frameworks"), ("carbon dioxide", "co2_adsorption"), ("gas storage", "lightweight_storage"), ("multi-objective", "balanced_screening")])
def test_controlled_variants(query, rule):
    assert rule in engine.activated_rules(query)

def test_all_frozen_queries():
    cfg=json.loads((ROOT/"configs/final_scenario_rules.json").read_text())
    intended=["co2_adsorption","photocatalysis","lightweight_storage","balanced_screening","insulating_frameworks"]
    for q, rule in zip(cfg["query_scenarios"], intended):
        assert rule in engine.activated_rules(q["query"])
        assert engine.generate_weights(q["query"]) == q["normalized_weights"]
        assert sum(q["normalized_weights"].values()) == pytest.approx(1)

def test_safe_overlap():
    assert p.semantic_overlap({"text":"CO2 adsorption"}, "CO2") == 1
    assert p.semantic_overlap({"text":"co2 ADSORPTION"}, "CO2") == 1
    assert p.semantic_overlap({"formula":"Co2C8H4", "text":"Formula: Co2C8H4"}, "CO2") == 0
    assert p.semantic_overlap({"text":"Co2"}, "CO2") == 0
    assert p.semantic_overlap({"text":"Formula"}, "for") == 0
    assert engine.activated_rules("Co2") == []
    assert engine.generate_weights("PHOTOCATALYTIC") == engine.generate_weights("photocatalytic")

def test_insulating_score_direction():
    rows=[dict(qmof_id=str(i), formula="C8Zn", text="", density=1.2, band_gap=g) for i,g in enumerate([2.,4.])]
    ranges=p.physical_ranges(rows)
    w=engine.generate_weights("insulating")
    scores=[p.score_record(r,"q5_insulating_frameworks","insulating",w,ranges) for r in rows]
    assert scores[1]["band_gap_score"] > scores[0]["band_gap_score"]
