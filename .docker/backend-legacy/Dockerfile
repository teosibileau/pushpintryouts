# legacy runtime: Django 3.2 LTS on Python 3.8. Poetry 2.x cannot run
# on py3.8, so this image installs from the requirements-legacy files
# (regenerate from a py3.8 lock with: poetry show --only main/dev |
# awk '{print $1"=="$2}')
FROM python:3.8-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# backports-zoneinfo ships no arm64 wheel for cp38 and must compile
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-legacy.txt requirements-legacy-dev.txt ./
RUN pip install --no-cache-dir -r requirements-legacy.txt -r requirements-legacy-dev.txt

COPY . .
