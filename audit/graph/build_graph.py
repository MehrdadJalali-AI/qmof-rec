#!/usr/bin/env python3
"""Turn QMOF-Rec execution traces into a QMOF-Audit provenance graph.

Input: the JSONL file written by the protocol
(``<output-dir>/execution_traces/traces.jsonl``, schema ``qmof-rec-trace/1``).
Output: an RDF graph (Turtle) using PROV-O, QUDT and the QMOF-Audit vocabulary,
validated against ``audit/schema/shapes.ttl``. A graph that fails validation
is not written, because it cannot be trusted as evidence.

Usage:
    python3 audit/graph/build_graph.py TRACES.jsonl OUT.ttl [--method LEA] [--seed 42]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from rdflib import RDF, RDFS, BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import XSD

QA = Namespace("https://github.com/MehrdadJalali-AI/qmof-rec/audit#")
PROV = Namespace("http://www.w3.org/ns/prov#")
QUDT = Namespace("http://qudt.org/schema/qudt/")
UNIT = Namespace("http://qudt.org/vocab/unit/")

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schema"
GRAPH_BUILDER_VERSION = "build_graph_v1"

COMPUTED_PROPERTIES = {"band_gap", "density", "void_fraction"}
EVIDENCE = {
    "computed": QA.Computed,
    "predicted": QA.Predicted,
    "heuristic_proxy": QA.HeuristicProxy,
    "experimental": QA.Experimental,
}
UNITS = {"eV": UNIT.EV, "g/cm3": UNIT["GM-PER-CentiM3"], "dimensionless": UNIT.UNITLESS}
SOURCE_FIELDS = {
    "band_gap": "outputs.hse06.bandgap",
    "density": "info.density",
    "void_fraction": "info.void_fraction",
}


def _iri(*parts: str) -> URIRef:
    return URIRef(str(QA) + "/".join(quote(str(p), safe="-_.") for p in parts))


def material_iri(qmof_id: str) -> URIRef:
    return _iri("material", qmof_id)


def observation_iri(qmof_id: str, prop: str) -> URIRef:
    return _iri("obs", qmof_id, prop)


def run_iri(run_id: str) -> URIRef:
    return _iri("run", run_id)


def score_iri(run_id: str, qmof_id: str, prop: str) -> URIRef:
    return _iri("score", run_id, qmof_id, prop)


def transformation_iri(run_id: str, qmof_id: str, prop: str) -> URIRef:
    return _iri("tx", run_id, qmof_id, prop)


def _fallback_inputs(policy: str | None) -> list[str]:
    """Properties named as missing in a fallback policy string.

    Formats written by the trace logger: 'score_set_to_0.0_then_masked',
    'use_density_score', or 'band_gap: replaced by 0.0; density: replaced by 2.0'.
    """
    if not policy:
        return []
    names = []
    for part in policy.split(";"):
        if ":" in part:
            names.append(part.split(":", 1)[0].strip())
    return names


class GraphBuilder:
    def __init__(self) -> None:
        g = Graph()
        g.bind("qa", QA)
        g.bind("prov", PROV)
        g.bind("qudt", QUDT)
        g.bind("unit", UNIT)
        self.g = g
        self._seen: set[URIRef] = set()

    # -- shared nodes ---------------------------------------------------------

    def _once(self, node: URIRef) -> bool:
        if node in self._seen:
            return False
        self._seen.add(node)
        return True

    def agents(self) -> None:
        g = self.g
        if self._once(QA["agent/qmof-database"]):
            g.add((QA["agent/qmof-database"], RDF.type, PROV.Agent))
            g.add((QA["agent/qmof-database"], RDFS.label, Literal("QMOF database (Rosen et al.)")))
        if self._once(QA["agent/qmof-rec"]):
            g.add((QA["agent/qmof-rec"], RDF.type, PROV.SoftwareAgent))
            g.add((QA["agent/qmof-rec"], RDF.type, PROV.Agent))
            g.add((QA["agent/qmof-rec"], RDFS.label, Literal("QMOF-Rec")))

    def source(self, sha: str) -> URIRef:
        node = _iri("source", sha)
        if self._once(node):
            self.agents()
            self.g.add((node, RDF.type, QA.Source))
            self.g.add((node, QA.sha256, Literal(sha)))
            self.g.add((node, RDFS.label, Literal("QMOF-Rec vector metadata snapshot (metadata.json)")))
            self.g.add((node, PROV.wasAttributedTo, QA["agent/qmof-database"]))
        return node

    def material(self, qmof_id: str, formula: str | None) -> URIRef:
        node = material_iri(qmof_id)
        if self._once(node):
            self.g.add((node, RDF.type, QA.Material))
            self.g.add((node, QA.qmofId, Literal(qmof_id)))
            if formula:
                self.g.add((node, QA.formula, Literal(formula)))
        return node

    def observation(self, rec: dict[str, Any], source: URIRef) -> URIRef:
        prop = rec["property"]
        node = observation_iri(rec["qmof_id"], prop)
        if not self._once(node):
            return node
        g = self.g
        g.add((node, RDF.type, QA.PropertyObservation))
        g.add((node, QA.ofMaterial, material_iri(rec["qmof_id"])))
        g.add((node, QA.propertyName, Literal(prop)))
        g.add((node, QA.evidenceType, EVIDENCE[rec.get("evidence_type") or "computed"]))
        g.add((node, PROV.wasDerivedFrom, source))
        g.add((node, QA.sourceField, Literal(SOURCE_FIELDS.get(prop, prop))))
        if rec.get("method_note"):
            g.add((node, QA.methodNote, Literal(rec["method_note"])))
        if rec.get("raw_value") is not None:
            g.add((node, QA.availability, QA.Observed))
            value = BNode()
            g.add((node, QA.hasValue, value))
            g.add((value, RDF.type, QUDT.QuantityValue))
            g.add((value, QUDT.numericValue, Literal(float(rec["raw_value"]), datatype=XSD.double)))
            g.add((value, QUDT.unit, UNITS[rec.get("unit") or "dimensionless"]))
        else:
            g.add((node, QA.availability, QA.Missing))
        return node

    def run(self, rec: dict[str, Any]) -> URIRef:
        node = run_iri(rec["run_id"])
        if self._once(node):
            self.agents()
            g = self.g
            g.add((node, RDF.type, QA.RecommendationRun))
            g.add((node, QA.queryId, Literal(rec["query_id"])))
            g.add((node, QA.method, Literal(rec["method"])))
            g.add((node, QA.seed, Literal(int(rec["seed"]), datatype=XSD.integer)))
            g.add((node, QA.codeVersion, Literal(rec.get("code_version") or "unavailable")))
            g.add((node, QA.configSha256, Literal(rec.get("config_sha256") or "unavailable")))
            g.add((node, PROV.wasAssociatedWith, QA["agent/qmof-rec"]))
            for rule in rec.get("activated_rules") or []:
                g.add((node, QA.activatedRule, Literal(rule)))
        return node

    def selection(self, rec: dict[str, Any], run: URIRef) -> None:
        node = _iri("selection", rec["run_id"], str(rec["rank"]))
        if self._once(node):
            g = self.g
            g.add((node, RDF.type, QA.Selection))
            g.add((node, QA.ofMaterial, material_iri(rec["qmof_id"])))
            g.add((node, QA.rank, Literal(int(rec["rank"]), datatype=XSD.integer)))
            g.add((node, PROV.wasGeneratedBy, run))

    # -- per-record -----------------------------------------------------------

    def add(self, rec: dict[str, Any]) -> None:
        g = self.g
        qid, prop = rec["qmof_id"], rec["property"]
        source = self.source(rec.get("metadata_sha256") or "0" * 64)
        material = self.material(qid, rec.get("formula"))
        run = self.run(rec)
        self.selection(rec, run)

        if prop in COMPUTED_PROPERTIES:
            self.observation(rec, source)
        if not rec.get("transformation"):
            return  # e.g. void fraction: recorded, never transformed

        tx = transformation_iri(rec["run_id"], qid, prop)
        score = score_iri(rec["run_id"], qid, prop)
        g.add((tx, RDF.type, QA.Transformation))
        g.add((tx, QA.rule, Literal(rec["transformation"])))
        g.add((tx, PROV.wasAssociatedWith, QA["agent/qmof-rec"]))
        g.add((tx, PROV.wasInformedBy, run))

        observed_inputs = set()
        for name in rec.get("inputs") or []:
            if name in COMPUTED_PROPERTIES:
                obs = observation_iri(qid, name)
                if obs not in self._seen:
                    # an input observation not traced as its own record (should not happen)
                    self.observation({"qmof_id": qid, "property": name, "raw_value": None,
                                      "evidence_type": "computed"}, source)
                g.add((tx, PROV.used, obs))
                observed_inputs.add(name)
            else:  # formula, text: attributes of the material record itself
                g.add((tx, PROV.used, material))

        policy = rec.get("fallback_policy")
        missing = set(_fallback_inputs(policy))
        if rec.get("availability") == "missing" and prop in COMPUTED_PROPERTIES:
            missing.add(prop)
        if rec.get("status") == "missing":  # e.g. stability with no density
            missing.update(n for n in observed_inputs)
        for name in sorted(missing):
            if name in COMPUTED_PROPERTIES:
                g.add((tx, QA.missingInput, observation_iri(qid, name)))
        if policy:  # e.g. stability -> 'use_density_score' (no stability value exists)
            g.add((tx, QA.fallbackPolicy, Literal(policy)))

        g.add((score, RDF.type, QA.Score))
        g.add((score, QA.ofMaterial, material))
        g.add((score, QA.propertyName, Literal(prop)))
        g.add((score, PROV.wasGeneratedBy, tx))
        g.add((score, QA.evidenceType, EVIDENCE[rec.get("evidence_type") or "heuristic_proxy"]))
        if rec.get("evidence_type") in (None, "heuristic_proxy"):
            g.add((score, QA.standsInFor, Literal(prop)))
        if rec.get("output_score") not in (None, ""):
            g.add((score, QA.scoreValue, Literal(float(rec["output_score"]), datatype=XSD.double)))
        g.add((score, QA.usedInRanking, Literal(bool(rec.get("used_in_ranking")))))
        g.add((score, QA.usedInDiversity, Literal(bool(rec.get("used_in_diversity")))))
        if rec.get("used_in_ranking"):
            g.add((run, PROV.used, score))


def build_graph(records: Iterable[dict[str, Any]]) -> Graph:
    builder = GraphBuilder()
    # Computed-property records first, so observations exist before
    # transformations that use them.
    records = sorted(records, key=lambda r: (r["property"] not in COMPUTED_PROPERTIES))
    for rec in records:
        builder.add(rec)
    return builder.g


def load_schema() -> tuple[Graph, Graph]:
    ontology = Graph().parse(SCHEMA_DIR / "qmof_audit.ttl")
    shapes = Graph().parse(SCHEMA_DIR / "shapes.ttl")
    return ontology, shapes


def validate(graph: Graph) -> tuple[bool, str]:
    from pyshacl import validate as shacl_validate

    ontology, shapes = load_schema()
    conforms, _report_graph, report_text = shacl_validate(
        graph, shacl_graph=shapes, ont_graph=ontology, inference="rdfs",
        advanced=True, allow_warnings=False,
    )
    return bool(conforms), report_text


def graph_snapshot_hash(graph: Graph) -> str:
    """Content hash of a graph, independent of blank-node labels and order."""
    from rdflib.compare import to_canonical_graph

    lines = sorted(to_canonical_graph(graph).serialize(format="nt").splitlines())
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def read_traces(path: Path, method: str | None = None, seed: int | None = None) -> list[dict[str, Any]]:
    out = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            rec = json.loads(line)
            if method and rec.get("method") != method:
                continue
            if seed is not None and int(rec.get("seed")) != seed:
                continue
            out.append(rec)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("traces", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--method")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--skip-validation", action="store_true",
                        help="write without SHACL validation (large graphs; validate a subset instead)")
    args = parser.parse_args(argv)

    records = read_traces(args.traces, args.method, args.seed)
    graph = build_graph(records)
    if not args.skip_validation:
        conforms, report = validate(graph)
        if not conforms:
            print(report)
            print("SHACL validation failed; graph not written.", file=sys.stderr)
            return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    graph.serialize(args.out, format="turtle")
    print(f"{len(records)} trace records -> {len(graph)} triples -> {args.out}")
    print(f"graph snapshot sha256: {graph_snapshot_hash(graph)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
