FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app


# curl нужен только для docker healthcheck
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# 1. Копируем pyproject (source of truth для зависимостей)
COPY pyproject.toml /app/

# 2. Устанавливаем зависимости api-сервиса (включая alembic)
RUN pip install --no-cache-dir ".[api,test]"

# 3. Копируем код api-сервиса
COPY services /app/services

# 4. Копируем тесты
COPY tests /app/tests

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
