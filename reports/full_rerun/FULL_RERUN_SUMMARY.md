# Full Rerun Summary

Date: 2026-06-03

## Commands Executed

```bash
PYTHONPATH=backend python3 backend/scripts/evaluate_lea_recommender.py --metadata backend/vector_db/metadata.json --out-dir reports/full_rerun/lea_evaluation --candidate-pool-size 100 --top-k 5 --seed 42
PYTHONPATH=backend python3 backend/scripts/evaluate_lea_ablation.py --metadata backend/vector_db/metadata.json --out-dir reports/full_rerun/ablation --top-k 5 --seeds 10 --seed-start 42
PYTHONPATH=backend python3 backend/scripts/evaluate_gnn_property_prediction.py --metadata backend/vector_db/metadata.json --out-dir reports/full_rerun/gnn --graph-out-dir reports/full_rerun/graph --k 8 --hidden-dim 32 --epochs 40 --seeds 42 43 44 --lr 0.01
PYTHONPATH=backend python3 backend/scripts/evaluate_graph_aware_recommendation.py --metadata backend/vector_db/metadata.json --gnn-dir reports/full_rerun/gnn --out-dir reports/full_rerun/graph_recommendation --candidate-pool-size 100 --top-k 5 --seeds 42 43 44
PYTHONPATH=backend python3 backend/scripts/evaluate_rag_assistant.py --out-dir reports/full_rerun/rag_llm --top-k 5
PYTHONPATH=backend python3 backend/scripts/statistical_tests.py --ablation-metrics reports/full_rerun/ablation/ablation_metrics.csv --out-dir reports/full_rerun/statistics --metric mean_relevance
python3 -c "import fastapi, uvicorn; print('fastapi ok')"
```

## Experiments Completed

- LEA recommender evaluation across five query scenarios with SemanticOnly, WeightedSum, TOPSIS, ParetoCrowding, Random, and LEA.
- LEA robustness and ablation experiments with 10 seeds and 50 query/seed observations per variant.
- MMR baseline from available objective vectors.
- Formula-derived QMOF k-nearest-neighbor graph construction.
- GraphSAGE/GAT property prediction for band gap and density.
- Graph-aware recommendation variants using GraphSAGE/GAT embeddings.
- Wilcoxon signed-rank tests and Friedman test for repeated relevance outputs.

## Experiments Failed Or Skipped

- RAG retrieval: not executable because the configured SentenceTransformer attempted blocked Hugging Face network access.
- LLM answer-quality evaluation: not executable because `OPENAI_API_KEY` is not configured.
- FastAPI platform live check: not executable because `fastapi` and `uvicorn` are missing.
- CIF-derived graph construction: not executable because CIF files are not present locally.
- Adsorption/porosity-specific evaluation: not executable because void fraction and adsorption descriptors are absent.
- NSGA-II, PSO, GA, and Bayesian optimization baselines: skipped because no executable repository implementations were found.

## Output Files Generated

- `reports/full_rerun/repository_audit.md`
- `reports/full_rerun/platform/platform_check.md`
- `reports/full_rerun/lea_evaluation/aggregate_metrics.csv`
- `reports/full_rerun/lea_evaluation/summary_metrics.csv`
- `reports/full_rerun/lea_evaluation/top_rankings.csv`
- `reports/full_rerun/lea_evaluation/lea_convergence.csv`
- `reports/full_rerun/lea_evaluation/figure_1_data_coverage.png`
- `reports/full_rerun/lea_evaluation/figure_2_metric_comparison.png`
- `reports/full_rerun/lea_evaluation/figure_3_runtime.png`
- `reports/full_rerun/lea_evaluation/figure_4_lea_convergence.png`
- `reports/full_rerun/lea_evaluation/figure_5_objective_radar.png`
- `reports/full_rerun/ablation/ablation_metrics.csv`
- `reports/full_rerun/ablation/ablation_summary.csv`
- `reports/full_rerun/ablation/ablation_runtime.csv`
- `reports/full_rerun/graph/qmof_graph_summary.json`
- `reports/full_rerun/gnn/gnn_property_prediction_metrics.csv`
- `reports/full_rerun/gnn/gnn_property_prediction_summary.csv`
- `reports/full_rerun/gnn/gnn_training_log.md`
- `reports/full_rerun/gnn/graphsage_band_gap_embeddings.npy`
- `reports/full_rerun/gnn/gat_band_gap_embeddings.npy`
- `reports/full_rerun/graph_recommendation/graph_recommendation_metrics.csv`
- `reports/full_rerun/graph_recommendation/graph_recommendation_summary.csv`
- `reports/full_rerun/rag_llm/rag_llm_status.json`
- `reports/full_rerun/rag_llm/rag_retrieval_metrics.csv`
- `reports/full_rerun/rag_llm/llm_assistant_eval.csv`
- `reports/full_rerun/rag_llm/example_outputs.md`
- `reports/full_rerun/statistics/statistical_tests.csv`
- `reports/full_rerun/statistics/statistical_summary.md`

## Tables Updated

- Table 1: updated to full rerun aggregate metrics and runtime values.
- Table 2: replaced TODO rows with reproduced GraphSAGE/GAT property-prediction results.
- Table 3: replaced TODO rows with reproduced ablation and graph-aware recommendation results.

## Manuscript Changes

- Revised abstract to mention reproduced graph-learning baselines and non-executable RAG/LLM evaluation.
- Updated platform section to distinguish implemented routes from design-target endpoints.
- Updated graph-learning section to report the formula-derived graph construction and GNN results.
- Added statistical-test interpretation.
- Replaced experimental TODO tables with real reproduced values.
- Replaced raw RAG/LLM TODO text with a clear non-executable note.
- Revised limitations, future work, conclusion, and declarations.

## Remaining Author/Admin Items

- Author name, email, and affiliation.
- Final author contribution statement.
- Final archival DOI or release tag for code and processed artifacts before submission.

## Final Quality Notes

- No fabricated results were added.
- GraphSAGE/GAT results are reported only for the reproduced formula-derived metadata graph.
- LLM and RAG results are not reported because the corresponding evaluation was not executable.
- Hypervolume remains labeled as a proxy.
- LEA is described as a post-retrieval portfolio optimizer, not as a universal winner over all baselines.
