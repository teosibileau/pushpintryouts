# build context is the repo root so the image can carry tests/ too
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false
WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY backend/pyproject.toml backend/poetry.lock ./backend/
RUN cd backend && poetry install --no-root

COPY pytest.ini pyproject.toml ./
COPY backend ./backend
COPY tests ./tests
