"""Tests for the QMOF-Audit schema, graph builder and pilot-set tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from rdflib import RDF, Literal, URIRef
from rdflib.namespace import XSD

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "audit" / "graph"))
sys.path.insert(0, str(ROOT / "audit" / "pilot"))

from app.recommendation.trace_logger import proxy_record, trace_material  # noqa: E402
from build_graph import (  # noqa: E402
    QA, QUDT, build_graph, graph_snapshot_hash, material_iri, observation_iri,
    score_iri, transformation_iri, validate,
)
import agreement  # noqa: E402

SHA = "a" * 64
RUN = "q3_lightweight_storage|seed42|LEA"


def _records():
    """Two real-looking candidates: one with a missing band gap."""
    ctx = {"run_id": RUN, "query_id": "q3_lightweight_storage", "seed": 42, "method": "LEA",
           "code_version": "test", "config_sha256": SHA, "metadata_sha256": SHA,
           "activated_rules": ["lightweight_storage"]}
    missing = {"qmof_id": "qmof-01be70a", "formula": "Zn2C8H4O6", "band_gap": None, "density": 0.9}
    observed = {"qmof_id": "qmof-13a76dd", "formula": "Zn4C40H28N12O8", "band_gap": 3.309, "density": 0.982}
    recs = []
    for rank, mat in ((1, observed), (2, missing)):
        extra = [proxy_record("proxy_a", "metadata_proxy_a_v1", ["formula", "band_gap", "density"], 0.3,
                              used_in_ranking=False, used_in_diversity=True,
                              fallbacks={} if mat["band_gap"] is not None else {"band_gap": "replaced by 0.0"})]
        recs += trace_material(mat, dict(ctx, rank=rank), extra)
    return recs


@pytest.fixture(scope="module")
def graph():
    return build_graph(_records())


def test_graph_from_traces_conforms(graph):
    conforms, report = validate(graph)
    assert conforms, report


def test_missing_band_gap_is_an_observation_without_value(graph):
    obs = observation_iri("qmof-01be70a", "band_gap")
    assert (obs, QA.availability, QA.Missing) in graph
    assert not list(graph.objects(obs, QA.hasValue))


def test_fallback_is_attached_to_the_transformation(graph):
    tx = transformation_iri(RUN, "qmof-01be70a", "band_gap")
    assert (tx, QA.missingInput, observation_iri("qmof-01be70a", "band_gap")) in graph
    assert graph.value(tx, QA.fallbackPolicy) == Literal("score_set_to_0.0_then_masked")
    score = score_iri(RUN, "qmof-01be70a", "band_gap")
    assert graph.value(score, QA.usedInRanking).toPython() is False


def test_proxy_a_fallback_traced_to_band_gap(graph):
    tx = transformation_iri(RUN, "qmof-01be70a", "proxy_a")
    assert (tx, QA.missingInput, observation_iri("qmof-01be70a", "band_gap")) in graph
    tx_ok = transformation_iri(RUN, "qmof-13a76dd", "proxy_a")
    assert not list(graph.objects(tx_ok, QA.missingInput))


def test_stability_is_a_heuristic_stand_in(graph):
    score = score_iri(RUN, "qmof-13a76dd", "stability")
    assert graph.value(score, QA.evidenceType) == QA.HeuristicProxy
    assert graph.value(score, QA.standsInFor) == Literal("stability")
    from build_graph import PROV
    tx = transformation_iri(RUN, "qmof-13a76dd", "stability")
    assert (tx, PROV.used, observation_iri("qmof-13a76dd", "density")) in graph
    assert graph.value(tx, QA.fallbackPolicy) == Literal("use_density_score")


def test_observed_value_has_qudt_unit(graph):
    from build_graph import UNIT
    obs = observation_iri("qmof-13a76dd", "band_gap")
    value = graph.value(obs, QA.hasValue)
    assert graph.value(value, QUDT.numericValue).toPython() == pytest.approx(3.309)
    assert graph.value(value, QUDT.unit) == UNIT.EV


def test_missing_value_recorded_as_zero_is_rejected(graph):
    from rdflib import BNode
    bad = graph.__class__()
    for t in graph:
        bad.add(t)
    obs = observation_iri("qmof-01be70a", "band_gap")
    v = BNode()
    bad.add((obs, QA.hasValue, v))
    bad.add((v, QUDT.numericValue, Literal(0.0, datatype=XSD.double)))
    bad.add((v, QUDT.unit, URIRef("http://qudt.org/vocab/unit/EV")))
    conforms, report = validate(bad)
    assert not conforms
    assert "never be recorded as a number" in report


def _with_claims(graph, verdict_on_claim=False):
    """The expose's three band-gap claims and their verification results."""
    g = graph.__class__()
    for t in graph:
        g.add(t)
    claims = [
        ("c1", "The pipeline substituted zero because band gap was unavailable.", QA.ComputationClaim, QA.Supported),
        ("c2", "This material has a calculated band gap of zero.", QA.PropertyClaim, QA.InsufficientEvidence),
        ("c3", "The pipeline used an observed band gap.", QA.ComputationClaim, QA.Contradicted),
    ]
    tx = transformation_iri(RUN, "qmof-01be70a", "band_gap")
    snapshot = graph_snapshot_hash(graph)
    for cid, text, ctype, verdict in claims:
        claim, result = QA["claim/" + cid], QA["result/" + cid]
        g.add((claim, RDF.type, QA.Claim))
        g.add((claim, QA.text, Literal(text)))
        g.add((claim, QA.claimType, ctype))
        g.add((claim, QA.aboutMaterial, material_iri("qmof-01be70a")))
        if verdict_on_claim:
            g.add((claim, QA.verdict, verdict))
        g.add((result, RDF.type, QA.VerificationResult))
        g.add((result, QA.verifies, claim))
        g.add((result, QA.verdict, verdict))
        g.add((result, QA.reason, Literal("test")))
        g.add((result, QA.ruleVersion, Literal("verifier_v0")))
        g.add((result, QA.graphSnapshot, Literal(snapshot)))
        g.add((result, QA.inspected, tx))
    return g


def test_three_band_gap_verdicts_conform(graph):
    conforms, report = validate(_with_claims(graph))
    assert conforms, report


def test_verdict_on_claim_is_rejected(graph):
    conforms, _ = validate(_with_claims(graph, verdict_on_claim=True))
    assert not conforms


def test_snapshot_hash_is_order_independent():
    a = graph_snapshot_hash(build_graph(_records()))
    b = graph_snapshot_hash(build_graph(list(reversed(_records()))))
    assert a == b


# --- pilot set -----------------------------------------------------------------

PILOT = ROOT / "audit" / "pilot" / "pilot_cases.jsonl"


def test_pilot_set_shape():
    cases = [json.loads(line) for line in PILOT.read_text().splitlines()]
    assert len(cases) == 40
    cats = {c["category"] for c in cases}
    assert len(cats) == 5
    for cat in cats:
        assert sum(c["category"] == cat for c in cases) == 8
    assert len({c["case_id"] for c in cases}) == 40
    assert all(c["labeller_1_verdict"] in agreement.VERDICTS for c in cases)
    assert all(c["expected_verdict"] is None for c in cases)  # set only after adjudication
    # every category mixes correct claims and errors
    for cat in cats:
        verdicts = {c["labeller_1_verdict"] for c in cases if c["category"] == cat}
        assert len(verdicts) >= 2, cat


def test_cohen_kappa_known_values():
    assert agreement.cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert agreement.cohen_kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == pytest.approx(0.0)
    # textbook example: po = 0.7, pe = 0.5 -> kappa = 0.4
    a = ["y"] * 5 + ["n"] * 5
    b = ["y"] * 4 + ["n"] + ["y"] * 2 + ["n"] * 3
    assert agreement.cohen_kappa(a, b) == pytest.approx(0.4)


def test_normalise_aliases():
    assert agreement.normalise("Insufficient") == "insufficient_evidence"
    assert agreement.normalise("") is None
    with pytest.raises(ValueError):
        agreement.normalise("maybe")
