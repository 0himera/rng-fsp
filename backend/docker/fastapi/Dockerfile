FROM python:3.11-slim AS base

ENV POETRY_VERSION=1.8.3 \
    VIRTUAL_ENV=/opt/venv \
    PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    python -m venv ${VIRTUAL_ENV} && \
    ${VIRTUAL_ENV}/bin/pip install --upgrade pip setuptools && \
    ${VIRTUAL_ENV}/bin/pip install poetry==${POETRY_VERSION}

WORKDIR /app

COPY pyproject.toml ./
COPY alembic.ini ./

RUN ${VIRTUAL_ENV}/bin/poetry install --no-root --no-interaction --no-ansi

COPY randomtrust ./randomtrust
COPY alembic ./alembic

RUN ${VIRTUAL_ENV}/bin/poetry install --only-root --no-interaction --no-ansi

EXPOSE 8000

CMD ["/opt/venv/bin/poetry", "run", "uvicorn", "randomtrust.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
