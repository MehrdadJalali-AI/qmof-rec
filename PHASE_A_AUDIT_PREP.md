# QMOF-Audit Phase A: audit-prep changes to QMOF-Rec

Goal: make QMOF-Rec record *how* every value behind a recommendation was
produced, without changing any ranking result. Built against the current
frozen protocol (`configs/final_scenario_rules.json`).

## Changed files

| File | Change |
| --- | --- |
| `backend/scripts/build_vector_index.py` | Missing values in the index text are written as `unavailable` instead of `nan`. Adds `band_gap_source` and a separate `band_gap_pbe` field. |
| `backend/app/recommendation/property_scorer.py` | New `score_*_with_status()` methods return `(score, "observed" \| "missing_fallback_zero")`. Original methods unchanged. Rule identifiers added. |
| `backend/app/recommendation/hybrid_ranker.py` | Records `stability_source` (`measured`, `density_proxy`, `missing`) and a `provenance` dict. `final_score` unchanged. |
| `backend/app/recommendation/objective_utils.py` | New `masked_distance_with_support()` also returns the number of jointly observed dimensions (0 = no-evidence fallback, not "identical"). |
| `backend/app/recommendation/trace_logger.py` | **New.** Per-candidate, per-property trace records (JSONL), with overrides for scenario rules. |
| `scripts/run_final_diversity_aware_masked_protocol.py` | Writes `<output-dir>/execution_traces/traces.jsonl`; traces Proxy S/A fallbacks and the insulating wide-gap rule; adds a `scoring_note` column and README to the RAG outputs. |
| `scripts/check_ranking_invariance.py` | **New.** Compares two artifact folders, ignoring timing values. |
| `backend/tests/test_provenance_traces.py` | **New.** 11 tests. |

## Not changed

Ranking logic, scenario rules, weights, LEA, candidate pools, metrics,
`metadata.json` and `qmof.index`. The existing `evaluation_status` values are
kept so earlier outputs stay comparable. The shipped index still contains
`Band Gap: nan` until it is rebuilt from the QMOF CSV:

```bash
cd backend && python -m scripts.build_vector_index
```

## How to verify

```bash
PYTHONPATH=backend python3 -m pytest -q        # 51 tests; 1 pre-existing failure, see below
git worktree add ../qmof-rec-base <commit-before-patch>
(cd ../qmof-rec-base && python3 scripts/run_final_diversity_aware_masked_protocol.py \
   --config configs/final_scenario_rules.json \
   --output-dir /tmp/base/benchmark --analysis-dir /tmp/base/analysis)
python3 scripts/run_final_diversity_aware_masked_protocol.py \
   --config configs/final_scenario_rules.json \
   --output-dir /tmp/new/benchmark --analysis-dir /tmp/new/analysis
python3 scripts/check_ranking_invariance.py /tmp/base/benchmark /tmp/new/benchmark
```

## Pre-existing test failure (not caused by this patch)

`backend/tests/test_scenario_rules.py::test_all_frozen_queries` compares
floating-point weights with `==` and fails on 0.33333333333337 vs
0.33333333333333. Comparing with `pytest.approx` would fix it.

## Findings recorded while doing this

- Stability is a density proxy for every recommended candidate.
- `metadata_proxy()` replaces a missing band gap with 0.0 (Proxy A) and a
  missing density with 2.0 (Proxy S and A). Both are traced as fallbacks.
- `run_rag_evaluation()` uses a template response; metadata and explanation
  scores and all flags are constants, groundedness and limitation scores are
  keyword checks on the template.

## Correction (18 Nov 2026)

The semantic-relevance trace flagged "band-gap bonus not applied" for every
missing band gap, but the lightweight-storage rule (`q3`) never reads band gap.
The flag is now limited to queries whose semantic rule uses band gap
(`SEMANTIC_BAND_GAP_QUERIES`). All 130 missing-band-gap slots are in `q3`, so
no semantic record carries this fallback any more. Rankings are unchanged.
