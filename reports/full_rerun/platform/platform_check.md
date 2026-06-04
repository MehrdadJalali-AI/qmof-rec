# QMOF-Rec Platform Execution Check

Date: 2026-06-03

## Backend Import And Startup

The FastAPI backend could not be started in the active Python environment.

Command checked:

```bash
python3 -c "import fastapi, uvicorn; print('fastapi ok')"
```

Result:

```text
ModuleNotFoundError: No module named 'fastapi'
```

`uvicorn` is also missing from the active environment. Because the backend could not be imported as a running FastAPI application, no live HTTP requests were issued.

## Tests

No backend test files were found by searching for `test_*.py`, `*_test.py`, or `pytest.ini`.

## Routes Found By Static Inspection

Backend app file: `backend/main.py`

Routers included:

- `chat_router`
- `material_router`
- `recommendation_router`
- `structure_router`

Static route definitions found:

- `GET /`
- `POST /chat/`
- `POST /recommend/`
- `POST /materials/predict`
- `GET /materials/{qmof_id}/structure`

## Requested Endpoint Availability

- `/chat`: route exists as `/chat/`; not live-tested because FastAPI is missing.
- `/recommend`: route exists as `/recommend/`; not live-tested because FastAPI is missing.
- `/predict`: no flat `/predict` route found; closest route is `/materials/predict`.
- `/materials/{id}`: no exact route found; closest route is `/materials/{qmof_id}/structure`.
- `/feedback`: no included route found.
- `/analytics`: no included route found.

## Example Request/Response

No live example request/response could be produced because the backend cannot start without `fastapi` and `uvicorn`.

## Missing Environment Or Services

- `fastapi`
- `uvicorn`
- `OPENAI_API_KEY` for LLM-backed chat responses
- Offline/cached SentenceTransformer model for RAG retrieval
- Local CIF file storage for structure rendering or CIF-derived graph workflows

## Conclusion

The repository contains backend and frontend platform code, but full platform deployment was not validated in this rerun. The manuscript should describe the platform architecture and executable scripts separately from a production deployment claim.
