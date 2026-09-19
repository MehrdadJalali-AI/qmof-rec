# Reproducing QMOF-Rec Results

## Environment

The verified lightweight workflow uses Python 3.9 or newer with NumPy 1.26.4, SciPy 1.13.1, Matplotlib 3.9.4, and pytest 8.3.4.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Configuration

`configs/final_diversity_aware_masked_protocol.json` is the default executable configuration. It defines five query scenarios; ten seeds (42 through 51); candidate pools 50, 100, and 200 with 100 as the main pool; and `top_k = 5`.

LEA uses population 30, 60 iterations, alpha 1.0, beta 0.1, gamma 0.1, redundancy penalty 0.05, self-cleaning every 10 iterations, and cleaning fraction 0.15. MMR uses relevance weight 0.7. The hybrid representation weights are 0.55 physical, 0.30 formula, and 0.15 engineered metadata proxies, with eight formula features and masked root-mean-square Euclidean distance.

## Tests

```bash
PYTHONPATH=backend python3 -m pytest -q
```

The focused tests cover missing-value masks, masked relevance and balance, active-objective remapping, hybrid-distance invariants, deterministic seeds, top-k uniqueness, MMR termination, LEA ablations, the DE portfolio, and sensitivity-grid dimensions.

## Main benchmark

```bash
python3 scripts/run_final_diversity_aware_masked_protocol.py \
  --config configs/final_diversity_aware_masked_protocol.json
```

The command rewrites `artifacts/benchmark/`. The principal files are `aggregate_metrics.csv`, `metrics_per_query_seed.csv`, `query_stratified_results.csv`, and `rankings_all_topk.csv`.

| Method | Rel@5 | Diversity | NDCG@5 |
|---|---:|---:|---:|
| WeightedSum | 0.8479 | 0.0187 | 1.0000 |
| LEA | 0.8479 | 0.0224 | 1.0000 |
| TOPSIS | 0.8479 | 0.0187 | 1.0000 |
| ParetoCrowding | 0.8447 | 0.0263 | 0.9952 |
| MMR top-5 | 0.8479 | 0.0241 | 1.0000 |

Runtime varies by machine and is recorded in milliseconds.

## Extended evaluation

```bash
python3 scripts/run_extended_evaluation.py
```

This command checks the main benchmark at four-decimal precision, then runs the DE portfolio, ablations, descriptor checks, and runtime scaling. The DE baseline uses SciPy `differential_evolution` with `best1bin`, a 30-member explicit initial population, 59 generations, default mutation `(0.5, 1.0)`, crossover 0.7, `polish=False`, one worker, and a seed-controlled random-key encoding. Each decoded portfolio contains exactly five unique candidates.

The expected DE aggregate is Rel@5 0.8479, diversity 0.0242, and NDCG@5 1.0000.

## Sensitivity analysis

```bash
python3 scripts/run_sensitivity_analysis.py
```

The sensitivity grid contains gamma values `0`, `0.025`, `0.05`, `0.10`, `0.20`, `0.40`, `0.80` and redundancy penalties `0`, `0.025`, `0.05`, `0.10`, `0.20`. Across five scenarios and ten seeds, the output contains 1,750 runs in `artifacts/sensitivity/gamma_lambda_sensitivity.csv`.

The ablation output distinguishes the LEA baseline (gamma 0.10, penalty 0.05), gamma-only mode (gamma 0, penalty 0.05), true no-diversity mode (gamma 0, penalty 0), and disabled self-cleaning.
