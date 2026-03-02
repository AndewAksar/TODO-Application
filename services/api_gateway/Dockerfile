FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app


# curl нужен для healthcheck (и иногда для debug)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# uv для детерминированной установки
RUN pip install --no-cache-dir uv

# Копируем pyproject (source of truth для зависимостей) + lock
COPY pyproject.toml uv.lock /app/

# ---------------- runtime ----------------
FROM base AS runtime

# Ставим строго по lock только runtime extras (runtime-зависимости сервиса)
RUN uv sync --frozen --no-install-project --extra api

# В runtime тесты НЕ копируем
COPY services /app/services

EXPOSE 8000
CMD ["uvicorn", "services.api_gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------------- tooling ----------------
FROM base AS tooling

# Ставим runtime-зависимости сервиса и dev-зависимости, строго по lock: api + test + dev
RUN uv sync --frozen --no-install-project --extra api --extra test --extra dev

COPY services /app/services
COPY tests /app/tests

CMD ["python", "-m", "pytest", "-m", "not flaky"]
