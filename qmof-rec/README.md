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
