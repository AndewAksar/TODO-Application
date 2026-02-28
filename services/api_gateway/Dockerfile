FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app


# curl нужен для healthcheck (и иногда для debug)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем pyproject (source of truth для зависимостей)
COPY pyproject.toml /app/

# ---------------- runtime ----------------
FROM base AS runtime

# Ставим только runtime-зависимости сервиса
RUN pip install --no-cache-dir ".[api]"

# В runtime тесты НЕ копируем
COPY services /app/services

EXPOSE 8000
CMD ["uvicorn", "services.api_gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------------- tooling ----------------
FROM base AS tooling

# Ставим только runtime-зависимости сервиса и dev-зависимости
RUN pip install --no-cache-dir ".[api,test]" ruff mypy

COPY services /app/services
COPY tests /app/tests

CMD ["python", "-m", "pytest", "-m", "not flaky"]
