# QMOF-Rec

AI-powered Metal-Organic Framework (MOF) discovery platform: RAG-based
scientific chat, multi-objective material recommendation, and a graph-based
material property classifier, built on the QMOF database.

## Structure

```
QMOF-Rec/
├── backend/    FastAPI app (chat, recommendation, material prediction, feedback)
├── frontend/   React + Vite UI (dashboard, chat, research, analytics)
```

See `backend/CHANGES.md` for a log of fixes/cleanup applied to the backend,
and `frontend/SYNC_NOTES.md` for frontend changes.

## Authentication & database

The backend now ships with real user accounts:

- **DB**: SQLAlchemy, defaults to a local `sqlite:///./qmof.db` file (zero
  setup). Point `DATABASE_URL` at Postgres for production, e.g.
  `postgresql+psycopg2://user:pass@host:5432/qmof`.
- **Auth**: JWT access/refresh tokens, bcrypt-hashed passwords. Refresh
  tokens are hashed and persisted (`refresh_tokens` table), so they can be
  revoked server-side — logging out, calling `/auth/logout-all`, or
  refreshing (which rotates and invalidates the old token) all work even
  before the token's natural expiry.
  Endpoints: `POST /auth/register`, `POST /auth/login`,
  `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/logout-all`,
  `GET /auth/me`.
- **Per-user data**: `GET/POST /users/me/favorites` (bookmarked materials),
  `GET /users/me/history` (saved queries) — tables: `users`, `favorites`,
  `saved_queries`, `refresh_tokens` in `app/db/models.py`.
- Set `SECRET_KEY` to a long random string before deploying
  (`python -c "import secrets; print(secrets.token_urlsafe(48))"`).

### Migrations (Alembic)

Schema changes are managed with Alembic instead of relying on
`create_all()` in production:

```bash
cd backend
alembic upgrade head                          # apply migrations
alembic revision --autogenerate -m "message"  # after changing a model
```

- In **development**, the app still auto-creates tables on startup via
  `create_all()` for convenience (`ENVIRONMENT=development`, the default).
- In **production** (`ENVIRONMENT=production`), the app does *not*
  auto-create tables — the Dockerfile runs `alembic upgrade head` before
  starting `uvicorn`, so every deploy applies pending migrations exactly
  once, in order.
- Alembic reads `DATABASE_URL` the same way the app does (env var, falling
  back to the local SQLite file), so no separate config is needed.

The frontend gates the whole app behind `/login` and `/register` via
`react-router-dom` + `AuthContext` (`src/context/AuthContext.jsx`). Tokens
are stored in `localStorage` and attached automatically by an axios
interceptor (`src/api/api.js`); a 401 response clears the session and
redirects to `/login`.

## Theme

The UI was re-themed from the previous warm/Claude-style palette to a
"materials lab" look — deep space-navy background, cyan→violet gradient
accents, a faint lattice-grid texture, and Space Grotesk/JetBrains Mono
type. All of this lives in CSS custom properties in
`frontend/src/styles/globals.css` (`:root`, `[data-theme="dark"]`,
`[data-theme="light"]`), so existing components inherit it automatically.
Auth-page-specific styles are in `frontend/src/styles/auth.css`.

## Local development

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
copy .env.example .env        # then fill in OPENAI_API_KEY, QMOF_CIF_DIR, CORS_ORIGINS
uvicorn main:app --reload
```

API docs: `http://127.0.0.1:8000/docs`
Health check: `http://127.0.0.1:8000/health`

### Frontend

```bash
cd frontend
npm install
copy .env.example .env        # set VITE_API_BASE_URL to the backend URL
npm run dev
```

Dev server: `http://localhost:5173`

**Important:** the backend's `CORS_ORIGINS` must include the frontend's
origin (e.g. `http://localhost:5173` for local dev, or your Netlify URL for
production), or browser requests will be blocked.

## Reviewer-revision reproducibility

The reviewer-revision branch `reviewer-arnd-revision` introduces explicit
descriptor availability masks for numerical reranking. Missing descriptors are
not interpreted as physical zero values. Active numerical objectives are:

- `semantic_score`
- `band_gap_score`
- `density_score`
- `stability_score`

Void fraction is unavailable for all 20,372 local metadata records and is
excluded from numerical relevance scoring, LEA candidate remapping, diversity
distance, objective-balance interpretation, radar plots, and frontend metric
plots. It remains only as unavailable metadata and as a limitation-warning
field for porosity or adsorption questions.

Focused revision tests:

```bash
PYTHONPATH=backend pytest -q backend/tests/test_missing_data_masks.py
```

Manuscript builds are maintained in:

```text
/Users/mehrdadjalali/Documents/SRH_Research/QMOF-Rec/QMOF_Rec
```

Build commands from that manuscript folder:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex
```

Repository-side revision logs:

- `REVISION_CHANGELOG.md`
- `REPRODUCTION_COMMANDS.md`
- `REVIEWER_COMMENT_MATRIX.csv`
- `FINAL_REVISION_AUDIT.md`

Current send-to-Arnd manuscript files are packaged in `manuscript/`, including
the main manuscript PDF/source, supplementary PDF/source, response-to-comments
files, figures, and protocol audit artifacts.

## Deployment

### Backend -> Railway

1. Create a new Railway project, deploy from this GitHub repo.
2. Set the **root directory** to `backend/` in the service settings.
3. Railway will detect `backend/Dockerfile` and `backend/railway.json`.
4. Set environment variables in the Railway dashboard (do **not** commit a
   real `.env`):
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (optional, defaults to `gpt-4o-mini`)
   - `CORS_ORIGINS` - set to your Netlify frontend URL once deployed
     (e.g. `https://qmof-rec.netlify.app`)
   - `QMOF_CIF_DIR` - leave unset for now (structure endpoint will 404 until
     CIF data is provisioned)
   - other variables as needed - see `backend/.env.example`
5. Railway provides `$PORT` automatically; the Dockerfile already uses it.
6. After deploy, check `https://<your-app>.up.railway.app/health` -
   `settings.validate()` will report any missing configuration.

### Frontend -> Netlify

1. Create a new Netlify site, "Import from Git", select this repo.
2. Set **base directory** to `frontend/`.
3. Build command and publish directory are read from `frontend/netlify.toml`
   (`npm run build` / `dist`).
4. Set environment variable in Netlify dashboard:
   - `VITE_API_BASE_URL` = your Railway backend URL
     (e.g. `https://qmof-rec-deployment-production.up.railway.app`)
5. Deploy. Once live, copy the Netlify URL and set it as `CORS_ORIGINS` on
   Railway (step above), then redeploy the backend so CORS allows it.

## Notes

- The vector index (`backend/vector_db/`, ~37MB) and ML classifier
  (`backend/app/models/material_classifier.pt`) are committed to this repo so
  the backend works out-of-the-box without a separate data-provisioning step.

### Known limitation: 3D structure viewer

`GET /materials/{qmof_id}/structure` and the "View 3D Structure" button in
the UI require CIF files (`qmof_database/qmof_database/relaxed_structures/`,
~116MB) that are **not included in this repo** and are not provisioned on the
deployed backend.

- **Local development**: works if `QMOF_CIF_DIR` in `backend/.env` points to
  a local copy of `relaxed_structures/`.
- **Deployed (Railway)**: `QMOF_CIF_DIR` is unset. The endpoint returns an
  error, and the frontend shows an inline message ("3D structure data is not
  available on this deployment yet.") instead of breaking.
- This was deliberately deferred - chat, recommendations, and feedback (the
  core features) work without it, and 116MB of CIF data would significantly
  bloat the git repo.

To enable it later, provision the CIF data via one of:

1. A Railway Volume (mount, upload `relaxed_structures/` once, set
   `QMOF_CIF_DIR` to the mount path)
2. External object storage (S3/R2) with download-on-startup
3. Git LFS (adds the data to the repo with separate storage)

then set `QMOF_CIF_DIR` accordingly in Railway's environment variables.

## Final Mask-Aware Manuscript Rerun

The final manuscript rerun is reproducible from the repository root:

```bash
PYTHONPATH=backend pytest -q backend/tests/test_missing_data_masks.py
python scripts/run_final_mask_aware_protocol.py \
  --config configs/final_mask_aware_protocol.json
```

Outputs are written to `artifacts/final_masked_protocol/`, with historical comparisons in `artifacts/protocol_comparison/` and preserved historical files in `artifacts/historical_protocol/`. The final rerun uses explicit descriptor masks and excludes void fraction from every numerical ranking calculation because void fraction is unavailable for all 20,372 local metadata records.
