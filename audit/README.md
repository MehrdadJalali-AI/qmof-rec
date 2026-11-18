# QMOF-Audit

Provenance-aware verification of claims in QMOF-Rec explanations. This folder
only reads QMOF-Rec outputs; it never changes rankings.

Status: **Phase B, steps 1 and 3 started** — schema (v1), a graph builder that
turns execution traces into a validated provenance graph, and the 40-case
pilot set awaiting its second labeller. Verifier, claim extraction and LLM
conditions are not implemented yet.

## Layout

```text
audit/
  schema/qmof_audit.ttl     vocabulary (PROV-O + QUDT + QMOF-Audit terms)
  schema/shapes.ttl         SHACL validation rules
  graph/build_graph.py      traces.jsonl -> RDF graph, validated with SHACL
  pilot/build_pilot_set.py  regenerates the 40-case pilot set from frozen results
  pilot/pilot_cases.jsonl   cases, evidence pointers, labeller-1 draft verdicts
  pilot/pilot_blind.csv     the same cases without verdicts, for labeller 2
  pilot/agreement.py        Cohen's kappa and adjudication sheet
  tests/                    schema, graph and pilot tests
```

Extra dependencies: `rdflib`, `pyshacl`, `pymatgen` (see `audit/requirements.txt`).

## Schema mapping

| Expose node | Implemented as | Reused vocabulary |
| --- | --- | --- |
| Material | `qa:Material` | `prov:Entity` |
| PropertyObservation | `qa:PropertyObservation` (one per material and property, shared across runs) | `prov:Entity` |
| Value + Unit | `qa:hasValue` → `qudt:QuantityValue` with `qudt:numericValue`, `qudt:unit` | QUDT (`unit:EV`, `unit:GM-PER-CentiM3`) |
| EvidenceType | `qa:Computed`, `qa:Predicted`, `qa:HeuristicProxy`, `qa:Experimental` | SKOS concepts |
| AvailabilityStatus | `qa:Observed`, `qa:Missing`, `qa:Masked` — separate from evidence type | SKOS concepts |
| Source | `qa:Source` (metadata snapshot, identified by SHA-256), attributed to the QMOF database agent | `prov:Entity`, `prov:wasAttributedTo`, `prov:Agent` |
| Transformation | `qa:Transformation` with `qa:rule`, `prov:used`; output `qa:Score` via `prov:wasGeneratedBy` | `prov:Activity` |
| MissingInputStatus + FallbackPolicy | `qa:missingInput`, `qa:fallbackPolicy` on the transformation, not on the value | — |
| RecommendationRun | `qa:RecommendationRun` (query, seed, method, code version, config hash); `qa:Selection` per rank | `prov:Activity`, `prov:wasAssociatedWith` |
| Claim | `qa:Claim` with `qa:claimType` (computation / property / application) | `prov:Entity` |
| VerificationResult | `qa:VerificationResult` with verdict, reason, inspected evidence, rule version, graph snapshot hash | `prov:Entity` |

## Validation rules (shapes.ttl)

- A missing property must not carry a value — a fallback zero can never be stored as a calculated zero.
- An observed property must carry a value with a unit.
- A transformation with a missing input must declare its fallback policy, and the input must really be missing.
- A heuristic-proxy score must say what it stands in for (e.g. stability).
- Claims never carry verdicts; verdicts live on `VerificationResult`, which must cite inspected evidence when it is supported or contradicted.

## Build a graph

```bash
# after running the protocol, which writes execution_traces/traces.jsonl
python3 audit/graph/build_graph.py OUTPUT_DIR/benchmark/execution_traces/traces.jsonl \
    /tmp/graph_lea42.ttl --method LEA --seed 42
```

The graph is written only if it passes SHACL validation; the command prints
its snapshot hash, which a `VerificationResult` records for replay.

## Pilot set and labelling protocol

40 cases, 8 per category (expose Section 7): `missing_inputs_fallbacks`,
`evidence_type`, `numerical_comparison`, `record_conflicts`,
`unsupported_application`. Every claim names real QMOF IDs and points to the
evidence needed to judge it (trace record, metadata field, CIF file, ranking
row or code location).

1. Labeller 1 has drafted a verdict and rationale for each case (`pilot_cases.jsonl`).
2. **Labeller 2** fills `labeller_2_verdict` in a copy of `pilot_blind.csv` without
   seeing labeller 1's verdicts. Allowed values: `supported`, `contradicted`,
   `insufficient_evidence`.
3. Run `python3 audit/pilot/agreement.py FILLED.csv --write-adjudication adjudication.csv`
   for Cohen's kappa and the disagreements.
4. Disagreements are adjudicated; only then is `expected_verdict` filled in.

Verdict definitions:

| Verdict | Use when |
| --- | --- |
| supported | the cited records establish the claim |
| contradicted | the cited records establish the opposite (e.g. a documented fallback where the claim says "observed") |
| insufficient_evidence | nothing in the snapshot can establish or refute the claim (e.g. any uptake or application claim) |

Note on record conflicts: metadata density and density recomputed from the
relaxed CIF agree for all 20,372 records (largest relative difference about
5e-9), because both come from the same relaxed structure. The CIF check is
therefore a consistency check, not fully independent evidence. Different QMOF
IDs with the same formula are distinct structures, so different values for
them are not a conflict.
