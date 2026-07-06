FROM python:3.11

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Railway injects $PORT at runtime; default to 8000 for local docker runs.
# Migrations run on every boot - alembic is idempotent (no-ops if already
# at head), which is safe for a single-instance deploy like this one.
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}