# SPDX-FileCopyrightText: Magenta ApS
# SPDX-License-Identifier: MPL-2.0

FROM python:3.12
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Keep Poetry in sync with the version that generated poetry.lock.
ARG POETRY_VERSION=2.5.1
RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

# Dependency layer: only invalidated when pyproject.toml or poetry.lock change.
FROM base AS dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-directory

# Development image: adds the dev/test groups, used by docker-compose and the
# integration tests.
FROM dependencies AS dev
COPY ./os2sync_export ./os2sync_export
COPY ./tests ./tests
RUN poetry install

# Production image: runtime dependencies only (default build target).
FROM dependencies AS runtime
COPY ./os2sync_export ./os2sync_export
RUN poetry install --only main

EXPOSE 8000
CMD ["uvicorn", "--factory", "os2sync_export.main:create_app", "--host", "0.0.0.0"]
