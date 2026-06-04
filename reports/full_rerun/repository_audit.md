# QMOF-Rec Repository Audit

Date: 2026-06-03

Working directory: `/Users/mehrdadjalali/Documents/SRH_Research/QMOF-Rec/qmof-rec`

## Scripts Found

- LEA recommender evaluation: `backend/scripts/evaluate_lea_recommender.py`
- LEA ablation evaluation: `backend/scripts/evaluate_lea_ablation.py`
- Graph/GNN property prediction: `backend/scripts/evaluate_gnn_property_prediction.py`
- Graph-aware recommendation: `backend/scripts/evaluate_graph_aware_recommendation.py`
- RAG/LLM executable-status check: `backend/scripts/evaluate_rag_assistant.py`
- Statistical tests: `backend/scripts/statistical_tests.py`
- LEA optimizer implementation: `backend/app/recommendation/lea_optimizer.py`
- Ranking baselines and metrics: `backend/app/evaluation/baselines.py`, `backend/app/evaluation/metrics.py`, `backend/app/evaluation/query_suite.py`
- Graph modules: `backend/app/graph/*`
- Existing ML model modules: `backend/app/ml/models/graphsage.py`, `backend/app/ml/models/gat.py`
- RAG/LLM modules: `backend/app/rag/*`, `backend/app/llm/*`, `backend/app/services/chat_service.py`
- Platform backend: `backend/main.py`, `backend/app/api/routes/*`
- Frontend: `frontend/*`
- Manuscript source: `manuscript/main.tex`, `manuscript/references.bib`

## Data Files Found

- QMOF vector metadata: `backend/vector_db/metadata.json`
- FAISS index: `backend/vector_db/qmof.index`
- Metadata records: 20,372
- Metadata keys sampled: `qmof_id`, `formula`, `text`, `band_gap`, `density`, `void_fraction`
- Density finite coverage: 20,372 / 20,372
- Band-gap finite coverage: 10,810 / 20,372
- Void-fraction finite coverage: 0 / 20,372
- Existing generated manuscript figures: `manuscript/figures/*`
- New rerun outputs: `reports/full_rerun/*`

## Missing Files Or Data

- No local QMOF CSV descriptor table was found.
- No local CIF files were found in the repository audit.
- No full descriptor matrix with void fraction or adsorption descriptors was found.
- No trained, repository-packaged LLM answer-quality evaluator was found.
- No local cached SentenceTransformer model was available for offline RAG retrieval.
- No executable NSGA-II, PSO, GA, or Bayesian optimization recommender baseline was found in the repository.

## Dependency Findings

Available:

- `numpy` 1.26.4
- `pandas` 2.2.3
- `sklearn`
- `scipy` 1.13.1
- `torch` 2.4.0
- `torch_geometric` 2.6.1
- `faiss` 1.13.0
- `sentence_transformers` 5.1.2
- `openai` 1.64.0

Missing in the active Python environment:

- `fastapi`
- `uvicorn`

Environment notes:

- `python` is not available, but `python3` is available.
- PyTorch Geometric imports with warnings because optional `pyg-lib` and `torch-sparse` shared libraries reference a missing Python framework path. The GNN rerun still completed.
- RAG retrieval attempted to download or inspect the Hugging Face model `sentence-transformers/all-MiniLM-L6-v2`; network access was unavailable.
- `OPENAI_API_KEY` was not configured, so LLM answer-quality evaluation was not executable.

## Executable Experiments

- LEA recommender evaluation across five query scenarios and six rankers.
- LEA ablations with 10 seeds and 50 query/seed observations per variant.
- Metadata-derived QMOF k-nearest-neighbor graph construction.
- GraphSAGE/GAT property prediction using formula-derived graph features.
- Graph-aware recommendation using reproduced GraphSAGE/GAT embeddings.
- Wilcoxon signed-rank and Friedman statistical tests over repeated ablation outputs.

## Non-Executable Or Partially Executable Modules

- FastAPI platform execution: not executable because `fastapi` and `uvicorn` are missing.
- RAG retrieval: not executable offline because the configured embedding model attempted blocked Hugging Face network access.
- LLM answer-quality evaluation: not executable because `OPENAI_API_KEY` is not set.
- CIF-derived graph learning: not executable because CIF/structure files are not present locally.
- Adsorption/porosity-specific evaluation: not executable because void fraction and adsorption descriptors are absent from the local metadata.
- NSGA-II, PSO, GA, and Bayesian optimization baselines: not executed because no repository implementations were found.

## Manuscript TODOs Addressed

- Table 1 updated to full rerun values.
- Table 2 replaced with reproduced GraphSAGE/GAT property-prediction results.
- Table 3 replaced with reproduced ablation and graph-aware recommendation results.
- RAG/LLM TODO table language removed and replaced with a not-executable explanation.
- Experimental TODO comments removed from main result tables.
- Data, code, competing interests, funding, and acknowledgements declarations revised.

## Remaining Manuscript Placeholders

- Author name, email, affiliation, and final author contributions remain author/admin-only placeholders.
