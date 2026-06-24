# Backend Cleanup Notes

This document summarizes the changes made to prepare the backend for production.

## 1. Secrets & configuration

- **Removed `.env` from the project entirely.** It contained a live OpenAI API key.
  **You must rotate this key in the OpenAI dashboard immediately** if you haven't
  already, and scrub it from git history (see "Git history" below).
- Added `.env.example` documenting every required/optional variable with no real
  secrets.
- Added `.gitignore` covering `.env`, `__pycache__`, build artifacts, and large
  generated files (vector index, model weights, reports, uploads).
- Rewrote `app/core/config.py`:
  - `CORS_ORIGINS` is now parsed into a list and `"*"` is treated as "no origins"
    (since `*` + `allow_credentials=True` is invalid/unsafe).
  - Added `settings.validate()`, which returns a list of configuration warnings
    (missing API key, missing CORS origins, missing/invalid `QMOF_CIF_DIR`,
    missing vector index in production). This is logged at startup and exposed
    via `GET /health`.
  - Added `ENVIRONMENT` / `is_production` for environment-aware checks.

## 2. Security fixes

- **Path traversal fix** in `app/api/routes/structure_routes.py`:
  - `qmof_id` is now validated against a strict pattern (`app/core/security.py:
    is_valid_qmof_id`) before being used to build a file path.
  - Added `safe_join()`, which resolves the final path and verifies it is still
    inside `QMOF_CIF_DIR`, raising if not.
- **CORS**: `main.py` now uses `settings.CORS_ORIGINS` (an explicit allowlist)
  instead of a hardcoded `["*"]`.
- **File upload validation** in `app/api/routes/material_routes.py`:
  - Validates the uploaded file extension against `SUPPORTED_FILE_TYPES`
    (previously defined but unused).
  - Enforces a 10 MB max upload size and rejects empty files.
  - Wraps prediction in try/except, returning a 422 with a clear message instead
    of a raw 500/stack trace on malformed CIFs.

## 3. Bug fixes

- `app/rag/knowledge_base.py` was **dead code with broken calls**
  (`embedding_engine.generate_embedding(...)` doesn't exist as a method, and
  `vector_store.add_doccument(...)` was a typo for `add_document`). It was not
  referenced anywhere and has been **removed**. The actual index builder is
  `scripts/build_vector_index.py`.
- `scripts/build_vector_index.py` had the same `generate_embedding` typo/issue —
  fixed to call `embedding_engine.encode(text)`.
- `app/llm/llm_client.py`: the OpenAI client is now constructed lazily and raises
  a clear `RuntimeError` if `OPENAI_API_KEY` is missing, instead of failing
  confusingly at import time. API errors during generation are now caught and
  return a friendly fallback message instead of propagating a raw exception.
- `app/ml/interface/predictor.py`: the GraphSAGE model is now loaded lazily on
  first prediction request rather than at import time. Previously, if
  `MODEL_PATH` didn't exist, **the entire app would fail to start** (since
  `material_service.py` instantiates `MaterialPredictor()` at import).
- `app/rag/embedding_engine.py`: the SentenceTransformer model is now loaded
  lazily on first use, avoiding slow/blocking import-time model downloads.
- Replaced bare `except:` clauses with `except (TypeError, ValueError):` in
  `feedback_engine.py`, `property_scorer.py`, and `json_utils.py`.
- Replaced `print()` statements with proper `logging` calls in `vector_store.py`
  and `main.py`.

## 4. Dead code removed

The following files were unused (not imported by `main.py` or any active code
path) and have been deleted:

- `app/services/recommendation_service.py`
- `app/llm/recommendation_agent.py`
- `app/recommendation/objective_engine.py`
- `app/recommendation/pareto_optimizer.py`
- `app/recommendation/diversity_ranker.py` (empty)
- `app/recommendation/graph_embedding_engine.py` (empty)
- `app/recommendation/graph_ranker.py` (empty)
- `app/recommendation/graph_similarity_engine.py` (empty)
- `app/recommendation/schemas.py` (empty)
- `app/llm/memory.py` (empty)
- `app/api/schemas/material_schema.py` (empty)
- `app/api/routes/graph_routes.py` (empty)
- `app/rag/knowledge_base.py` (broken, see above)

The active recommendation flow is:
`recommendation_routes.py` -> `recommendation_pipeline.py` -> (`dynamic_weight_engine`,
`hybrid_ranker`, `material_similarity`, `lea_optimizer`, `novelty_ranker`,
`feedback_ranker`).

Note: `app/graph/graph_loader.py`, `app/visualization/*`, and
`app/ml/training/*` are also currently empty but were left in place as they
look like planned-but-not-yet-implemented features (training scripts,
dashboard/visualization endpoints) rather than refactor leftovers. Remove or
implement these as appropriate.

## 5. Schema cleanup

- `app/api/schemas/recommendation_schema.py` previously defined a
  `RecommendationRequest` that didn't match the one actually used in
  `recommendation_routes.py`. It is now the single source of truth, with a
  `resolved_query()` helper and `top_k` bounded between 1 and 50.
- `app/api/schemas/chat_schema.py`'s `ChatResponse` now matches what
  `chat_engine.ask()` actually returns (`question`, `answer`, `retrieved_count`,
  `retrieved_materials`), and the chat route declares `response_model=ChatResponse`.

## 6. Formatting

- Ran `black` across `app/`, `main.py`, and `scripts/` for consistent,
  PEP 8-compliant formatting (collapses the previous one-argument-per-line
  style into normal Python formatting).

## Remaining recommendations (not changed in this pass)

- **Git history**: if `.env` was ever committed, deleting it now is not enough.
  Scrub it from history with `git filter-repo` or BFG Repo-Cleaner, then force-push.
- **RAG hallucination guard**: the chat/recommendation prompts should explicitly
  instruct the LLM not to introduce materials that aren't in the retrieved
  context, and to refuse/redirect when retrieval returns nothing. See the
  evaluation report in `reports/rag_llm_evaluation/` (50% hallucination rate on
  the benchmark set).
- **Rate limiting**: no endpoint has rate limiting; `/chat/` and `/recommend/`
  call the OpenAI API on every request with no caps.
- **Authentication**: all endpoints are currently open/unauthenticated.
