# Rollback contamination check

Obsolete comparison source: commit `79f860d5f665aa9451a7f36602f17dca2e5c806d`, `artifacts/final_masked_protocol/aggregate_metrics.csv`.

Final result: **PASS — no old-protocol assertion or primary result remains in the recovered manuscript, supplement, or response.**

## Required recovery signatures

- PASS — candidate-screening title
- PASS — four contribution items
- PASS — aligned rel_r definition
- PASS — correct LEA diversity
- PASS — matched MMR top-5
- PASS — DE portfolio
- PASS — true no-diversity
- PASS — 1,750-run sweep
- PASS — proxy framing
- PASS — auxiliary explanation
- PASS — complete response

## Structured numerical comparison

| Method | Obsolete Rel@5 / diversity / runtime ms | Recovered Rel@5 / diversity / runtime ms |
|---|---|---|
| WeightedSum | 0.8479 / 0.0000 / 0.05 | 0.8479 / 0.0187 / 0.05 |
| LEA | 0.8479 / 0.0000 / 93.68 | 0.8479 / 0.0224 / 87.26 |
| MMR | 0.8400 / 0.0400 / 1708.12 | 0.8479 / 0.0241 / 12.70 (matched top-5) |

## Prohibited old-content scan

- PASS — LEA core novelty assertion: absent
- PASS — LEA aggregate diversity 0.0000: absent
- PASS — MMR aggregate diversity 0.0400: absent
- PASS — MMR 1708 primary runtime: absent
- PASS — positive 25-fold faster assertion: absent
- PASS — GraphSAGE-only final table row: absent
- PASS — GAT-only final table row: absent
- PASS — perfect-groundedness final claim: absent
- PASS — 3.3% hallucination final evidence: absent
- PASS — balanced-discovery publication label: absent

## Context-aware retained strings

- `2209.67` — Retained only as the explicitly historical full-list MMR audit; 12.70 ms is the primary matched top-5 comparison.
- `core novelty` — Retained in negations and the verbatim Reviewer 3 quotation, not as the manuscript claim.
- `GraphSAGE only / GAT only` — Retained only in the verbatim Reviewer 3 quotation; final manuscript tables use proxy-S/proxy-A labels.
- `zero hallucination` — Retained in a negative limitation sentence stating that assigned values cannot demonstrate it.
- `25-fold` — Retained only in the response as a withdrawn historical claim and in the reviewer quotation.

The Reviewer 3 quotation is preserved verbatim by design. Its obsolete claims are reviewer text, immediately followed by corrected responses, and are not contamination.
