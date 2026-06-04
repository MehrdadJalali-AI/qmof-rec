# QMOF-Rec Frontend Screenshot Report

Date: 2026-06-04

## Commands Executed

```bash
npm install
npm run build
npm run dev -- --host 127.0.0.1
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
OPENAI_API_KEY=dummy .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
node reports/frontend_screenshots/capture_screenshots.mjs
```

## URLs

- Frontend URL: `http://127.0.0.1:5173/`
- Backend URL attempted: `http://127.0.0.1:8000/`

## Backend Status

Backend APIs were unavailable for real live outputs during screenshot capture.

- Dependencies installed successfully into `backend/.venv`.
- Startup without credentials failed due to missing `OPENAI_API_KEY`.
- Startup with `OPENAI_API_KEY=dummy` failed due to missing `app/models/material_classifier.pt`.
- `QMOF_CIF_DIR` was not configured, and no repository-local CIF files were found for the material structure endpoint.
- No `/feedback`, `/analytics`, or `/ws` backend route was found in the inspected backend route files.

The screenshots therefore represent local frontend execution of the implemented prototype interface. They do not show fabricated recommendation outputs, fabricated LLM answers, or fabricated 3D material structures.

## Pages Captured

- Dashboard overview
- Scientific chat page
- Research / recommendation input interface
- Analytics page

Not captured:

- Live recommendation results, because the backend did not start successfully.
- Material detail / 3D structure viewer, because recommendation cards require backend results and CIF access.
- Feedback page, because no dedicated feedback page is implemented.

## Screenshot Files Generated

- `manuscript/figures/qmof_rec_ui_dashboard.png`
- `manuscript/figures/qmof_rec_ui_chat.png`
- `manuscript/figures/qmof_rec_ui_recommendations.png`
- `manuscript/figures/qmof_rec_ui_feedback.png`
- `manuscript/figures/qmof_rec_application_screenshots.png`

All captured page screenshots are 1440 x 900 PNG files without browser chrome. The composite manuscript figure is a 2 x 2 panel PNG with panel labels A-D.

The final screenshot pass uses the QMOF-Rec SVG logo from `Logo/QMOF-Rec.svg`, copied into `frontend/src/assets/qmof-rec-logo.svg` for Vite bundling. The old text-only sidebar title was removed from the active frontend shell.

## Capture Notes

The in-app browser displayed the app successfully but its screenshot endpoint timed out. A local headless Chrome capture script was added at `reports/frontend_screenshots/capture_screenshots.mjs` and used against the same running Vite frontend URL.

## Final Manuscript Files Added or Updated

- Added frontend audit: `reports/frontend_screenshots/frontend_audit.md`
- Added execution report: `reports/frontend_screenshots/FRONTEND_SCREENSHOT_REPORT.md`
- Added capture script: `reports/frontend_screenshots/capture_screenshots.mjs`
- Added individual screenshots under `manuscript/figures/`
- Added composite screenshot figure under `manuscript/figures/`
- Updated frontend branding to use `frontend/src/assets/qmof-rec-logo.svg`
