#!/usr/bin/env python3
"""Build the QMOF-Audit 40-case pilot set from the frozen QMOF-Rec results.

Eight cases in each of the five categories of the expose (Section 7), every
claim grounded in a real QMOF record and real ranking output:

    missing_inputs_fallbacks, evidence_type, numerical_comparison,
    record_conflicts, unsupported_application

Inputs (all committed in the repository):
    artifacts/final_scenario_rules/benchmark/rankings_all_topk.csv
    backend/vector_db/metadata.json
    backend/data/relaxed_structures/<qmof_id>.cif

Outputs (in audit/pilot/):
    pilot_cases.jsonl     full cases with evidence and labeller-1 draft verdicts
    pilot_blind.csv       claim + evidence only, for the independent labeller 2

Labelling protocol: labeller 1 (the builder of this set) drafts a verdict and
rationale. Labeller 2 fills ``pilot_blind.csv`` without seeing them.
``agreement.py`` then reports Cohen's kappa, and disagreements are
adjudicated into ``expected_verdict``. Until then ``expected_verdict`` is null.

The set is regenerated deterministically:
    python3 audit/pilot/build_pilot_set.py
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from pymatgen.core import Composition  # noqa: E402

from app.recommendation.trace_logger import trace_material  # noqa: E402

RANKINGS = ROOT / "artifacts" / "final_scenario_rules" / "benchmark" / "rankings_all_topk.csv"
METADATA = ROOT / "backend" / "vector_db" / "metadata.json"
CIF_DIR = ROOT / "backend" / "data" / "relaxed_structures"
OUT_DIR = Path(__file__).resolve().parent

PILOT_VERSION = "pilot_v1"
LABELLER_1 = "S. S. Banerjee (draft)"
AVOGADRO = 6.02214076e23
SUPPORTED, CONTRADICTED, INSUFFICIENT = "supported", "contradicted", "insufficient_evidence"


def finite(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else value


def cif_density(qmof_id: str) -> float:
    """Density in g/cm3 from the relaxed CIF: formula mass / cell volume."""
    text = (CIF_DIR / f"{qmof_id}.cif").read_text()
    volume = float(re.search(r"_cell_volume\s+([\d.]+)", text).group(1))
    formula = re.search(r"_chemical_formula_sum\s+'([^']+)'", text).group(1)
    return Composition(formula).weight / AVOGADRO / (volume * 1e-24)


class Data:
    def __init__(self) -> None:
        self.rows = list(csv.DictReader(RANKINGS.open(encoding="utf-8")))
        self.meta = {r["qmof_id"]: r for r in json.loads(METADATA.read_text())}

    def material(self, qmof_id: str) -> dict:
        r = self.meta[qmof_id]
        return {"qmof_id": qmof_id, "formula": r["formula"], "band_gap": finite(r["band_gap"]),
                "density": finite(r["density"]), "void_fraction": finite(r.get("void_fraction"))}

    def trace(self, qmof_id: str) -> dict:
        return {t["property"]: t for t in trace_material(self.material(qmof_id), {})}

    def top(self, query_id: str, method: str = "LEA", seed: str = "42") -> list[dict]:
        rows = [r for r in self.rows if r["query_id"] == query_id and r["method"] == method and r["seed"] == seed]
        return sorted(rows, key=lambda r: int(r["rank"]))

    def first_row(self, qmof_id: str) -> dict:
        return next(r for r in self.rows if r["qmof_id"] == qmof_id)


def ev(kind: str, ref: str, value=None) -> dict:
    """An evidence pointer a labeller can check."""
    out = {"kind": kind, "ref": ref}
    if value is not None:
        out["value"] = value
    return out


def run_ref(row: dict) -> str:
    return f"{row['query_id']}|seed{row['seed']}|{row['method']}|rank{row['rank']}"


def fmt(x: float, n: int = 3) -> str:
    return f"{x:.{n}f}"


def build_cases(data: Data) -> list[dict]:
    cases: list[dict] = []

    def add(category, claim, claim_type, qmof_ids, evidence, draft, rationale, context=None):
        cases.append({
            "case_id": f"{category[:4].upper()}-{sum(c['category'] == category for c in cases) + 1:02d}",
            "category": category,
            "claim": claim,
            "claim_type": claim_type,
            "qmof_ids": qmof_ids,
            "context": context,
            "evidence": evidence,
            "labeller_1": LABELLER_1,
            "labeller_1_verdict": draft,
            "labeller_1_rationale": rationale,
            "labeller_2_verdict": None,
            "expected_verdict": None,
            "pilot_version": PILOT_VERSION,
        })

    lea_co2 = data.top("q1_co2_adsorption")
    lea_ins = data.top("q5_insulating_frameworks")
    lea_store = data.top("q3_lightweight_storage")

    # Materials with a missing HSE06 band gap that appear in some top-5 list.
    missing_ids = sorted({r["qmof_id"] for r in data.rows if finite(r["band_gap"]) is None})
    m1, m2, m3 = missing_ids[0], missing_ids[1], missing_ids[2]
    r1, r2, r3 = data.first_row(m1), data.first_row(m2), data.first_row(m3)
    obs = lea_co2[0]  # observed band gap
    t1, tobs = data.trace(m1), data.trace(obs["qmof_id"])

    # ---- 1. Missing inputs / fallbacks ---------------------------------------
    cat = "missing_inputs_fallbacks"
    add(cat, f"The pipeline set the band-gap score of {m1} to 0.0 because its band gap was unavailable.",
        "computation", [m1],
        [ev("trace", f"{run_ref(r1)}/band_gap", {"availability": t1["band_gap"]["availability"],
                                                 "fallback_policy": t1["band_gap"]["fallback_policy"],
                                                 "output_score": t1["band_gap"]["output_score"]}),
         ev("metadata", f"{m1}.band_gap", None)],
        SUPPORTED, "The trace records availability=missing, fallback score_set_to_0.0_then_masked, output 0.0.",
        run_ref(r1))
    add(cat, f"{m1} has a calculated band gap of 0 eV.", "property", [m1],
        [ev("metadata", f"{m1}.band_gap", None), ev("trace", f"{run_ref(r1)}/band_gap", {"raw_value": None})],
        INSUFFICIENT, "No band-gap value exists in the snapshot; 0.0 is a fallback score, not a calculated property.",
        run_ref(r1))
    add(cat, f"The ranking of {m1} used an observed band gap.", "computation", [m1],
        [ev("trace", f"{run_ref(r1)}/band_gap", {"availability": "missing", "used_in_ranking": False})],
        CONTRADICTED, "The execution record documents a missing band gap and a fallback, not an observation.",
        run_ref(r1))
    add(cat, f"Proxy A for {m2} was computed with its missing band gap replaced by 0.0.", "computation", [m2],
        [ev("code", "scripts/run_final_diversity_aware_masked_protocol.py::metadata_proxy", "band_gap default 0.0"),
         ev("metadata", f"{m2}.band_gap", None)],
        SUPPORTED, "metadata_proxy(flavor='a') uses finite_float(band_gap, 0.0); the band gap is missing.",
        run_ref(r2))
    add(cat, f"The band-gap score of {m2} contributed to its ranking score.", "computation", [m2],
        [ev("trace", f"{run_ref(r2)}/band_gap", {"used_in_ranking": False}),
         ev("ranking", run_ref(r2), {"availability_mask": r2["availability_mask"]})],
        CONTRADICTED, "The band-gap objective is masked out (mask 0) when the band gap is missing.",
        run_ref(r2))
    add(cat, f"Proxy S for {m3} replaced its missing density with the default 2.0 g/cm3.",
        "computation", [m3],
        [ev("code", "scripts/run_final_diversity_aware_masked_protocol.py::metadata_proxy",
            "density default 2.0 only when density is missing"),
         ev("metadata", f"{m3}.density", finite(data.meta[m3]["density"]))],
        CONTRADICTED, "Density is observed for this material (as for all records); no density fallback was applied.",
        run_ref(r3))
    add(cat, f"The band gap of {obs['qmof_id']} ({fmt(finite(obs['band_gap']))} eV) was used in the CO2 LEA ranking.",
        "computation", [obs["qmof_id"]],
        [ev("trace", f"{run_ref(obs)}/band_gap", {"availability": tobs["band_gap"]["availability"],
                                                  "used_in_ranking": tobs["band_gap"]["used_in_ranking"]})],
        SUPPORTED, "Band gap is observed and the band-gap objective is active (mask 1).", run_ref(obs))
    add(cat, f"The void fraction of {obs['qmof_id']} was used to rank it for CO2 adsorption.", "computation",
        [obs["qmof_id"]], [ev("trace", f"{run_ref(obs)}/void_fraction",
                              {"availability": "missing", "fallback_policy": "excluded_from_ranking"})],
        CONTRADICTED, "Void fraction is absent for all records and excluded from ranking.", run_ref(obs))

    # ---- 2. Evidence-type distinctions --------------------------------------
    cat = "evidence_type"
    a, b = lea_co2[0], lea_co2[2]
    add(cat, f"The density of {a['qmof_id']} ({fmt(finite(a['density']))} g/cm3) is a computed value from the QMOF relaxed structure.",
        "property", [a["qmof_id"]],
        [ev("trace", f"{run_ref(a)}/density", {"evidence_type": "computed", "evidence_source": "qmof:info.density"})],
        SUPPORTED, "Density comes from info.density of the relaxed structure (evidence type computed).", run_ref(a))
    add(cat, f"The stability score of {a['qmof_id']} is based on measured stability data.", "property", [a["qmof_id"]],
        [ev("trace", f"{run_ref(a)}/stability", {"evidence_type": "heuristic_proxy",
                                                 "fallback_policy": "use_density_score"})],
        CONTRADICTED, "No stability value exists; the score is copied from the density bin (heuristic proxy).",
        run_ref(a))
    add(cat, f"The stability score of {b['qmof_id']} is a heuristic derived from its density.", "computation",
        [b["qmof_id"]], [ev("trace", f"{run_ref(b)}/stability", {"inputs": ["density"],
                                                                 "transformation": "stability_from_density_bin_v1"})],
        SUPPORTED, "Trace: stability transformation uses density only.", run_ref(b))
    add(cat, f"The band gap of {b['qmof_id']} ({fmt(finite(b['band_gap']))} eV) was measured experimentally.",
        "property", [b["qmof_id"]], [ev("trace", f"{run_ref(b)}/band_gap", {"evidence_type": "computed",
                                                                           "evidence_source": "qmof:outputs.hse06.bandgap"})],
        CONTRADICTED, "The value is an HSE06 calculation recorded as computed; the snapshot contains no experimental band gaps.",
        run_ref(b))
    add(cat, f"The band gap of {b['qmof_id']} was computed with the HSE06 functional.", "property", [b["qmof_id"]],
        [ev("trace", f"{run_ref(b)}/band_gap", {"evidence_source": "qmof:outputs.hse06.bandgap"})],
        SUPPORTED, "The source field is outputs.hse06.bandgap.", run_ref(b))
    add(cat, f"Proxy S for {lea_co2[1]['qmof_id']} is a trained GraphSAGE embedding.", "computation",
        [lea_co2[1]["qmof_id"]], [ev("code", "scripts/run_final_diversity_aware_masked_protocol.py::metadata_proxy",
                                     "hand-written formula of metal/hetero fractions and density")],
        CONTRADICTED, "Proxy S is an engineered formula-derived score, not a trained model output.",
        run_ref(lea_co2[1]))
    add(cat, f"A machine-learning model predicts a band gap of 2.0 eV for {lea_co2[3]['qmof_id']}.", "property",
        [lea_co2[3]["qmof_id"]], [ev("trace", f"{run_ref(lea_co2[3])}/band_gap", {"evidence_type": "computed"})],
        INSUFFICIENT, "The protocol records no predicted values; no prediction for this material exists to check.",
        run_ref(lea_co2[3]))
    add(cat, f"The relevance score of {lea_co2[4]['qmof_id']} for the CO2 query is an embedding similarity.",
        "computation", [lea_co2[4]["qmof_id"]],
        [ev("trace", f"{run_ref(lea_co2[4])}/semantic_relevance",
            {"transformation": "deterministic_semantic_proxy_v2", "method_note": "not an embedding similarity"})],
        CONTRADICTED, "The offline benchmark uses a deterministic token-overlap proxy, not embeddings.",
        run_ref(lea_co2[4]))

    # ---- 3. Numerical comparisons (unit-aware) --------------------------------
    cat = "numerical_comparison"
    s = lea_store
    d = {r["qmof_id"]: finite(r["density"]) for r in s}
    g = {r["qmof_id"]: finite(r["band_gap"]) for r in s}
    x, y = s[0]["qmof_id"], s[1]["qmof_id"]  # Zn4 (0.982) vs Zn4 (0.828)
    add(cat, f"{y} has a lower density than {x}.", "property", [x, y],
        [ev("metadata", f"{x}.density", d[x]), ev("metadata", f"{y}.density", d[y])],
        SUPPORTED if d[y] < d[x] else CONTRADICTED, f"{fmt(d[y])} vs {fmt(d[x])} g/cm3.")
    add(cat, f"{x} has a lower density than {y}.", "property", [x, y],
        [ev("metadata", f"{x}.density", d[x]), ev("metadata", f"{y}.density", d[y])],
        SUPPORTED if d[x] < d[y] else CONTRADICTED, f"{fmt(d[x])} vs {fmt(d[y])} g/cm3.")
    add(cat, f"The density of {x} is about {round(d[x] * 1000)} kg/m3.", "property", [x],
        [ev("metadata", f"{x}.density", d[x]), ev("unit", "1 g/cm3 = 1000 kg/m3")],
        SUPPORTED, f"{fmt(d[x])} g/cm3 = {round(d[x] * 1000)} kg/m3.")
    add(cat, f"The density of {x} is {fmt(d[x])} kg/m3.", "property", [x],
        [ev("metadata", f"{x}.density", d[x]), ev("unit", "metadata density is in g/cm3")],
        CONTRADICTED, "The number is correct in g/cm3; in kg/m3 it is 1000 times larger.")
    hi = lea_ins[0]
    add(cat, f"{hi['qmof_id']} has a band gap more than 1 eV wider than {x}.", "property", [hi["qmof_id"], x],
        [ev("metadata", f"{hi['qmof_id']}.band_gap", finite(hi["band_gap"])), ev("metadata", f"{x}.band_gap", g[x])],
        SUPPORTED if finite(hi["band_gap"]) - g[x] > 1 else CONTRADICTED,
        f"{fmt(finite(hi['band_gap']))} - {fmt(g[x])} = {fmt(finite(hi['band_gap']) - g[x])} eV.")
    lightest = min(s, key=lambda r: finite(r["density"]))
    heaviest = max(s, key=lambda r: finite(r["density"]))
    add(cat, f"{lightest['qmof_id']} has the lowest density of the five LEA picks for the lightweight-storage query (seed 42).",
        "property", [r["qmof_id"] for r in s],
        [ev("ranking", f"q3_lightweight_storage|seed42|LEA", {r["qmof_id"]: finite(r["density"]) for r in s})],
        SUPPORTED, "Minimum of the five listed densities.", "q3_lightweight_storage|seed42|LEA")
    add(cat, f"{heaviest['qmof_id']} has the lowest density of the five LEA picks for the lightweight-storage query (seed 42).",
        "property", [r["qmof_id"] for r in s],
        [ev("ranking", f"q3_lightweight_storage|seed42|LEA", {r["qmof_id"]: finite(r["density"]) for r in s})],
        CONTRADICTED, "It is the highest of the five listed densities.", "q3_lightweight_storage|seed42|LEA")
    add(cat, f"{x} has a wider band gap than {m1}.", "property", [x, m1],
        [ev("metadata", f"{x}.band_gap", g[x]), ev("metadata", f"{m1}.band_gap", None)],
        INSUFFICIENT, f"{m1} has no band-gap value, so the comparison cannot be made.")

    # ---- 4. Record conflicts ----------------------------------------------------
    cat = "record_conflicts"
    for row in (lea_co2[0], lea_ins[0], lea_ins[2]):
        q = row["qmof_id"]
        dm, dc = finite(data.meta[q]["density"]), cif_density(q)
        agree = abs(dm - dc) / dm < 0.01
        add(cat, f"The metadata density of {q} agrees with the density computed from its relaxed CIF (within 1%).",
            "property", [q], [ev("metadata", f"{q}.density", dm), ev("cif", f"backend/data/relaxed_structures/{q}.cif",
                                                                  {"computed_density": dc})],
            SUPPORTED if agree else CONTRADICTED, f"{fmt(dm, 4)} vs {fmt(dc, 4)} g/cm3 (same structure, same definition).")
    q = lea_ins[1]["qmof_id"]
    dm, dc = finite(data.meta[q]["density"]), cif_density(q)
    add(cat, f"The density recorded for {q} conflicts with the density of its own relaxed CIF.", "property", [q],
        [ev("metadata", f"{q}.density", dm), ev("cif", f"backend/data/relaxed_structures/{q}.cif", {"computed_density": dc})],
        CONTRADICTED if abs(dm - dc) / dm < 0.01 else SUPPORTED, f"{fmt(dm, 4)} vs {fmt(dc, 4)} g/cm3: no conflict.")
    # Same formula, different QMOF IDs: distinct materials, so not a conflict.
    fa, fb = "qmof-a1a5849", "qmof-b1cbe7a"
    formula = data.meta[fa]["formula"]
    add(cat, f"QMOF has conflicting density records for {formula}: {fa} lists {fmt(finite(data.meta[fa]['density']))} g/cm3 and {fb} lists {fmt(finite(data.meta[fb]['density']))} g/cm3.",
        "property", [fa, fb],
        [ev("metadata", f"{fa}.formula", formula), ev("metadata", f"{fb}.formula", data.meta[fb]["formula"]),
         ev("metadata", f"{fa}.density", finite(data.meta[fa]["density"])),
         ev("metadata", f"{fb}.density", finite(data.meta[fb]["density"]))],
        CONTRADICTED, "Different QMOF IDs are different structures (e.g. polymorphs) with the same formula; different densities are expected, not a conflict.")
    add(cat, f"{fa} and {fb} are the same material because they share the formula {formula}.", "property", [fa, fb],
        [ev("metadata", f"{fa}.formula", formula), ev("cif", f"{fa}.cif vs {fb}.cif", "different cells and densities")],
        CONTRADICTED, "Same composition but distinct structures; identical formula does not identify a material.")
    hb = lea_co2[2]["qmof_id"]
    add(cat, f"The HSE06 band gap of {hb} conflicts with its PBE band gap.", "property", [hb],
        [ev("trace", f"{hb}/band_gap", {"evidence_source": "qmof:outputs.hse06.bandgap"}),
         ev("metadata", f"{hb}.band_gap_pbe", "not in snapshot")],
        INSUFFICIENT, "No PBE value is in the snapshot, and values from different functionals are not comparable as a conflict.")
    add(cat, f"There is a record conflict for {hb}: its band gap differs between two QMOF-Rec runs.", "computation", [hb],
        [ev("ranking", "rankings_all_topk.csv", {"distinct_band_gap_values_for_material":
                                                 sorted({r['band_gap'] for r in data.rows if r['qmof_id'] == hb})})],
        CONTRADICTED, "Every run reads the same snapshot value for this material.")

    # ---- 5. Unsupported application claims ------------------------------------
    cat = "unsupported_application"
    c1, c2 = lea_co2[0]["qmof_id"], lea_co2[1]["qmof_id"]
    add(cat, f"{c1} will show high CO2 uptake at 1 bar and 298 K.", "application", [c1],
        [ev("trace", f"{run_ref(lea_co2[0])}", "no adsorption/uptake property in snapshot")],
        INSUFFICIENT, "No uptake evidence exists for any condition; ranking alone does not establish uptake.",
        run_ref(lea_co2[0]))
    add(cat, f"{c2} is a good CO2 adsorbent because its density is low ({fmt(finite(lea_co2[1]['density']))} g/cm3).",
        "application", [c2], [ev("metadata", f"{c2}.density", finite(lea_co2[1]["density"]))],
        INSUFFICIENT, "The density is correct, but low density does not establish adsorption performance.",
        run_ref(lea_co2[1]))
    add(cat, f"{c1} was ranked first by LEA for the CO2 adsorption query (seed 42).", "computation", [c1],
        [ev("ranking", run_ref(lea_co2[0]), {"rank": 1})], SUPPORTED, "Ranking file shows rank 1.",
        run_ref(lea_co2[0]))
    add(cat, f"{c1} has been experimentally validated for CO2 capture.", "application", [c1],
        [ev("trace", f"{run_ref(lea_co2[0])}", "no experimental evidence of any kind in snapshot")],
        INSUFFICIENT, "Missing-information trap: no experimental record exists to support or refute it.",
        run_ref(lea_co2[0]))
    p = data.top("q2_photocatalysis")[2]
    add(cat, f"The band gap of {p['qmof_id']} ({fmt(finite(p['band_gap']))} eV) lies within the 1.0-3.5 eV window used by the band-gap scorer.",
        "computation", [p["qmof_id"]], [ev("metadata", f"{p['qmof_id']}.band_gap", finite(p["band_gap"])),
                                        ev("code", "property_scorer.BAND_GAP_RULE", "band_gap_bin_v1: 1.0<=bg<=3.5")],
        SUPPORTED if 1.0 <= finite(p["band_gap"]) <= 3.5 else CONTRADICTED, "Value checked against the rule bounds.",
        run_ref(p))
    add(cat, f"{p['qmof_id']} is an efficient visible-light photocatalyst.", "application", [p["qmof_id"]],
        [ev("metadata", f"{p['qmof_id']}.band_gap", finite(p["band_gap"]))],
        INSUFFICIENT, "A band gap in a suitable range does not establish photocatalytic activity.", run_ref(p))
    add(cat, f"{c1} is highly porous.", "application", [c1],
        [ev("trace", f"{run_ref(lea_co2[0])}/void_fraction", {"availability": "missing"})],
        INSUFFICIENT, "Void fraction is absent for all records; porosity cannot be assessed.", run_ref(lea_co2[0]))
    w = lea_ins[0]
    add(cat, f"{w['qmof_id']} is stable in water.", "application", [w["qmof_id"]],
        [ev("trace", f"{run_ref(w)}/stability", {"evidence_type": "heuristic_proxy", "inputs": ["density"]})],
        INSUFFICIENT, "The only 'stability' signal is a density heuristic; nothing about water stability exists.",
        run_ref(w))

    return cases


BLIND_FIELDS = ["case_id", "category", "claim", "claim_type", "qmof_ids", "context", "evidence",
                "labeller_2_verdict", "labeller_2_note"]


def write_outputs(cases: list[dict], out_dir: Path = OUT_DIR) -> None:
    with (out_dir / "pilot_cases.jsonl").open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case, sort_keys=True) + "\n")
    with (out_dir / "pilot_blind.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BLIND_FIELDS)
        writer.writeheader()
        for case in cases:
            writer.writerow({
                "case_id": case["case_id"], "category": case["category"], "claim": case["claim"],
                "claim_type": case["claim_type"], "qmof_ids": ";".join(case["qmof_ids"]),
                "context": case["context"] or "", "evidence": json.dumps(case["evidence"]),
                "labeller_2_verdict": "", "labeller_2_note": "",
            })


def main() -> int:
    cases = build_cases(Data())
    write_outputs(cases)
    from collections import Counter
    print(f"{len(cases)} cases")
    print(dict(Counter(c["category"] for c in cases)))
    print(dict(Counter(c["labeller_1_verdict"] for c in cases)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
