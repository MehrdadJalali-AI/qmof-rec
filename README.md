# QMOF-Rec

QMOF-Rec is a query-driven, multi-objective recommender for screening existing QMOF material records when physical metadata are incomplete. It combines deterministic candidate generation, mask-aware utility scoring, and diversity-aware reranking.

## Features

- deterministic candidate generation for five material-screening scenarios with exact metadata-text token overlap;
- explicit availability masks for band gap, density, and stability-related scores;
- no physical zero imputation for missing descriptors;
- WeightedSum, TOPSIS, ParetoCrowding, MMR top-5, LEA, and Differential Evolution portfolio baselines;
- full-precision hybrid material distance over observed physical descriptors, eight formula features, and engineered metadata proxies S and A;
- gamma and redundancy-penalty sensitivity analysis;
- ablation, runtime scaling, and descriptor-level screening diagnostics;
- FastAPI backend and React frontend with an auxiliary explanation interface.

## Installation

The reproducibility workflow targets Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Install `backend/requirements.txt` as well when running the complete API or web application.

## Data

The benchmark reads `backend/vector_db/metadata.json`, which contains 20,372 local material records. Density is available for every local record, band gap is partially available, and void fraction is unavailable. Missing values remain masked throughout scoring and distance calculations. See `data/README.md` for the data contract.

## Quick start

```bash
PYTHONPATH=backend python3 -m pytest -q
python3 scripts/run_final_diversity_aware_masked_protocol.py \
  --output-dir artifacts/corrected_co2/benchmark \
  --analysis-dir artifacts/corrected_co2/representation_analysis
python3 scripts/run_extended_evaluation.py \
  --benchmark-dir artifacts/corrected_co2/benchmark \
  --output-root artifacts/corrected_co2 --skip-regression-gate
```

The default configuration is `configs/final_diversity_aware_masked_protocol.json`. `artifacts/benchmark/` retains the historical substring-matching run. Corrected outputs are isolated under `artifacts/corrected_co2/`; the explicit output arguments prevent accidental overwrite.

## Methods

Relevance and balance operate only on available objectives. LEA remaps evolving candidates in the active masked objective space. Reported diversity, MMR redundancy, Pareto crowding, and the DE portfolio objective use a separate hybrid material representation at full precision.

Proxy S and proxy A are engineered metadata proxies. They are deterministic functions of formula-derived features and available scalar metadata; they are not trained atomistic representations.

The offline semantic proxy case-folds and tokenizes metadata text with the alphanumeric pattern `[a-z0-9]+`; formulas are excluded from query-token overlap. This prevents a `CO2` query from matching cobalt stoichiometry such as `Co2`. The live SentenceTransformer/FAISS retrieval path is separate from this offline proxy benchmark.

MMR stops after `top_k` unique selections. The DE baseline uses SciPy's seeded `differential_evolution` with a random-key representation that decodes to exactly `top_k` unique candidates.

## Repository structure

```text
backend/       API, recommendation components, metadata, and tests
configs/       executable benchmark configuration
scripts/       benchmark and extended-evaluation entry points
artifacts/     machine-readable reference outputs
docs/          software reproducibility documentation
data/          data-contract documentation
frontend/      web interface
```

## Reproducing benchmarks

See [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for environment details, expected regression values, output files, and individual commands.

## Web demo

[https://qmofrecsystem.netlify.app/](https://qmofrecsystem.netlify.app/)


## Frozen application-scenario protocol

The current five-scenario experiment uses `configs/final_scenario_rules.json` and `artifacts/final_scenario_rules/`. Earlier `artifacts/benchmark/` and `artifacts/corrected_co2/` results are historical and remain unchanged. The rules were frozen before inspecting new outcomes. The protocol supports controlled token/phrase variants, excludes formulas from application-text overlap, distinguishes CO2 from Co2, increases photocatalysis band-gap weight, and gives insulating queries a wide-gap utility. Exact strings, activated rules, normalized weights, and heuristic limitations are in the configuration. These are preliminary metadata preferences, not measured adsorption or catalytic performance.

```sh
PYTHONPATH=backend python3 -m pytest -q
python3 scripts/run_final_diversity_aware_masked_protocol.py --config configs/final_scenario_rules.json --output-dir artifacts/final_scenario_rules/benchmark --analysis-dir artifacts/final_scenario_rules/representation_analysis
python3 scripts/run_extended_evaluation.py --config configs/final_scenario_rules.json --benchmark-dir artifacts/final_scenario_rules/benchmark --output-root artifacts/final_scenario_rules --skip-regression-gate
```

Use fresh explicit output directories when reproducing. The skip flag bypasses the obsolete historical numeric gate, not tests. `protocol_freeze.json` predates outcome inspection; `source_manifest.json` hashes the evaluated uncommitted implementation and metadata. A Git HEAD alone does not identify these working-tree changes. `smoke_test.json` verifies all five rules and candidate-pool descriptor constraints; `scenario_overlap.csv` quantifies pool and shortlist overlap. Repeated recommendations and null effects must not be interpreted as failures to optimize and must not trigger outcome-driven weight tuning.
