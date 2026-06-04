# QMOF-Rec Frontend Audit

Date: 2026-06-04

## Repository Structure

- Frontend directory: `frontend`
- Backend directory: `backend`
- Logo source used for frontend branding: `Logo/QMOF-Rec.svg`
- Bundled frontend logo copy: `frontend/src/assets/qmof-rec-logo.svg`
- Frontend framework: React 18 with Vite
- Package manager: npm (`package-lock.json` is present)
- Frontend dev command: `npm run dev -- --host 127.0.0.1`
- Frontend URL used for inspection: `http://127.0.0.1:5173/`

## Frontend Pages

The frontend is a React single-page application. It does not define URL routes; instead, `frontend/src/App.jsx` switches pages through local React state.

The visible application branding is provided by the QMOF-Rec SVG logo in the sidebar. The previous text-only `QMOF AI` sidebar title was replaced before the final screenshot pass.

- Dashboard: `frontend/src/pages/Dashboard.jsx`
- Scientific Chat: `frontend/src/pages/ChatPage.jsx`
- Research / Recommendation interface: `frontend/src/pages/ResearchPage.jsx`
- Analytics: `frontend/src/pages/AnalyticsPage.jsx`

No implemented standalone material-detail route was found. The 3D structure viewer is nested inside recommendation cards and becomes available only after live recommendation results return a material with a `qmof_id`.

No dedicated feedback page was found. The available user-facing analytics page was captured as the closest implemented feedback/analytics view.

## Frontend API Usage

The frontend API client is defined in `frontend/src/api/api.js` and uses:

- Base URL: `http://127.0.0.1:8000`
- Health check: `GET /`
- Chat: `POST /chat/`
- Recommendations: `POST /recommend/`
- Structure viewer: `GET /materials/{qmof_id}/structure`
- Prediction upload: `POST /materials/predict`

`frontend/src/api/websocket.js` also points to `ws://127.0.0.1:8000/ws`, but no matching backend websocket route was found in the inspected backend route files.

## Backend API Routes Found

The backend FastAPI app is defined in `backend/main.py`.

Routes included by the app:

- `GET /`
- `POST /chat/`
- `POST /recommend/`
- `POST /materials/predict`
- `GET /materials/{qmof_id}/structure`

No implemented `/feedback` or `/analytics` backend endpoints were found.

## Environment and Data Requirements

Backend configuration is defined in `backend/app/core/config.py`.

Environment variables used by the backend include:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `LLM_PROVIDER`
- `VECTOR_TOP_K`
- `VECTOR_DB_PATH`
- `VECTOR_DIMENSION`
- `VECTOR_INDEX_PATH`
- `VECTOR_METADATA_PATH`
- `MODEL_PATH`
- `K_NEIGHBORS`
- `QMOF_CSV_PATH`
- `CORS_ORIGINS`
- `EMBEDDING_MODEL`
- `QMOF_CIF_DIR`

Repository-local data/model artifacts found:

- `backend/vector_db/qmof.index`
- `backend/vector_db/metadata.json`

Required artifacts not found:

- `backend/app/models/material_classifier.pt` or the configured `MODEL_PATH`
- Local CIF files for `QMOF_CIF_DIR`

## Execution Status

Frontend dependencies were already installed and `npm install` completed successfully. The frontend ran locally on `http://127.0.0.1:5173/`.

Backend dependencies were installed into `backend/.venv`. Backend startup did not complete:

1. Startup without credentials failed because `OPENAI_API_KEY` was missing.
2. Startup with a dummy `OPENAI_API_KEY` progressed further but failed because `app/models/material_classifier.pt` was missing.

As a result, screenshots were captured from the real locally running frontend prototype, but live recommendation result cards, LLM answer content, and the 3D material viewer were not captured.
