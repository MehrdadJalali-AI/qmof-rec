# Frontend / Backend Sync Notes

## Fixes applied

1. **`src/main.jsX` -> `src/main.jsx`**
   `index.html` references `/src/main.jsx` (lowercase), but the file was named
   `main.jsX`. This works on case-insensitive filesystems (Windows/macOS) but
   **fails the build on Linux/CI/most deploy platforms**. Renamed to match.

2. **API base URL is now environment-driven**
   - Added `.env.example` with `VITE_API_BASE_URL` and `VITE_WS_BASE_URL`.
   - `src/api/api.js` now reads `import.meta.env.VITE_API_BASE_URL`, falling
     back to `http://127.0.0.1:8000` for local dev.
   - `src/components/StructureViewer.jsx` updated similarly.
   - To point the frontend at the deployed backend, create a `.env` (or set
     the variable in your hosting provider's dashboard) with:
     ```
     VITE_API_BASE_URL=https://qmof-rec-deployment-production.up.railway.app
     ```

3. **`askChat` no longer sends an unused `top_k`**
   The backend's `ChatRequest` schema only accepts `question`; `chat_engine.ask()`
   hardcodes `top_k=5` server-side. The extra field was silently ignored by
   Pydantic but is misleading. Removed from `api.js` and `ChatWindow.jsx`.

4. **Missing `zustand` dependency added to `package.json`**
   `src/store/useAppStore.js` imports `zustand`, which wasn't declared.
   `npm install` would have left this broken at first use. Added
   `"zustand": "^5.0.14"` and regenerated `package-lock.json`.
   Note: `useAppStore` is currently not imported anywhere in the app - it's
   either for an upcoming feature or leftover scaffolding.

5. **`.gitignore` added** for `node_modules/`, `dist/`, `.env*`.

## Known issues left as-is (per your direction)

- **`src/api/websocket.js`** connects to `${WS_BASE_URL}/ws`, but the backend
  exposes no `/ws` route - this connection will fail. Made the URL
  configurable via `VITE_WS_BASE_URL` and added a code comment. If/when a
  WebSocket endpoint is added to the FastAPI backend (e.g. via
  `@app.websocket("/ws")`), this should start working without further
  frontend changes.

- **`src/components/StructureViewer.jsx`** (Mol*-based 3D viewer) is not
  imported/used anywhere - `MaterialCard.jsx` uses `MoleculeViewer.jsx`
  (3Dmol-based) instead. `molstar` is also not in `package.json`, so this
  component would fail to build if it were ever imported. Left in place,
  URL made configurable.

## Verified

- `npm install` succeeds with the corrected `package.json`.
- `npm run build` succeeds (pre-existing warnings from the `3dmol` package
  about `eval` usage and bundle size are unrelated to these changes).

## Recommended next steps

- Decide whether `StructureViewer.jsx` and `useAppStore.js` should be
  finished, or removed as dead code (mirrors the dead-code cleanup already
  done on the backend).
- If the `/ws` endpoint is wanted, add a corresponding route to
  `backend/main.py` (FastAPI supports `@app.websocket(...)`).
- Set `VITE_API_BASE_URL` in your frontend hosting provider's environment
  variables to point at the Railway backend for production builds.
- Backend CORS: make sure `CORS_ORIGINS` (set in the backend's `.env`/Railway
  variables) includes the exact origin your frontend will be served from
  (e.g. `https://your-frontend.vercel.app`), otherwise browser requests from
  the deployed frontend to the deployed backend will be blocked.
