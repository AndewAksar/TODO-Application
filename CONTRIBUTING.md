# Contributing

Этот репозиторий — учебный проект, но процессы максимально приближены к индустриальным.

## Ветки и flow

### Основная ветка
- `main` — всегда стабильная. В `main` попадает только то, что прошло CI.

Прямые push в `main` запрещены. Любые изменения — только через Pull Request.

### Ветки под работу (одна задача = одна ветка)
Используем префиксы:

- `feature/<short-name>` — новая функциональность
- `fix/<short-name>` — исправления багов
- `refactor/<short-name>` — рефакторинг без изменения поведения
- `chore/<short-name>` — инфраструктура, сборка, CI, зависимости
- `docs/<short-name>` — документация
- `exp/<short-name>` или `spike/<short-name>` — эксперименты/прототипы

Рекомендуемый стиль: `feature/12-auth-jwt` (где `12` — номер GitHub Issue).

## Pull Request

### Обязательные требования перед merge
- CI зелёный (линтер/форматтер/типы/тесты).
- PR небольшой и сфокусированный: одна тема, один результат.
- Описано, что сделано и зачем (а не “обновил”).
- Если меняется API — обновлён OpenAPI/Swagger и/или контракты.

### Рекомендуемая стратегия merge
- **Squash and merge** (один коммит в `main` на одну задачу).

## Коммиты (Conventional Commits)

Формат:
`<type>(<scope>): <subject>`

Где:
- `type`: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `build`, `ci`
- `scope`: компонент/сервис, например `auth`, `todo`, `gateway`, `infra`
- `subject`: коротко, в настоящем времени, без точки

Примеры:
- `feat(auth): add jwt access/refresh flow`
- `fix(todo): validate due_date timezone`
- `chore(ci): add github actions workflow`
- `docs(readme): describe local run`

## Коммиты (Conventional Commits)

В проекте используется стиль **Conventional Commits**.

Формат коммита:

`<type>(<scope>): <subject>`

### Поля коммита

#### type — тип изменения

Обязательное поле:

- `feat` — новая функциональность
- `fix` — исправление бага
- `refactor` — рефакторинг без изменения поведения
- `chore` — инфраструктура, сборка, CI, зависимости
- `docs` — документация
- `test` — добавление или исправление тестов
- `build` — Dockerfile, сборка образов
- `ci` — CI/CD конфигурация

#### scope — область изменения (желательно)

Показывает **где именно** произошло изменение:

- сервис: `api`, `scheduler`, `mailer`
- инфраструктура: `infra`, `docker`, `nginx`, `compose`
- домен: `auth`, `todo`, `users`
- инструменты: `ci`, `github`, `pre-commit`

Примеры:
- `fix(infra): ...`
- `feat(api): ...`
- `chore(ci): ...`

#### subject — суть изменения

Краткое описание:

- в настоящем времени (`add`, `fix`, `remove`, `update`);
- до ~72 символов;
- без точки в конце;
- отвечает на вопрос: **«что делает этот коммит?»**

---

# Проверки качества кода

В проекте используются два режима проверки:
1. **Host environment** — быстрые проверки в локальном `.venv`
2. **Docker tooling environment** — проверки в контейнере `api-tooling`

Docker-режим максимально приближен к CI.

---

## Быстрые проверки на хосте

Используются для быстрого цикла разработки.
Требуется активированное виртуальное окружение:

```bash
  source .venv/bin/activate
```
Линтер:
```bash
  make lint-local
```
```bash
  ruff check .
```
Форматирование:
```bash
  make format-local
```
```bash
  ruff format .
```
Проверка типов:
```bash
  make typecheck-local
```
```bash
  mypy .
```
Запуск тестов (требуется переменная окружения `DATABASE_URL`).

Пример:
```bash
  DATABASE_URL='postgresql+asyncpg://x:x@localhost:5432/x' make test-local
```
```bash
  make test-local-unit
  make test-local-contract
  make test-local-integration
```

---

## Полная проверка в Docker
Этот режим максимально близок к CI.
Он использует контейнер api-tooling.
Контейнер содержит:
- pytest
- ruff
- mypy
- Alembic
- dev/test зависимости

Линтер
```bash
  make lint
```
Форматирование
```bash
  make format
```
Проверка типов
```bash
  make typecheck
```
Тесты
```bash
  make test
```

---

## Минимальный набор перед Pull Request

Перед созданием PR рекомендуется выполнить:
```bash
  make lint
  make typecheck
  make test
```
или локально:
```bash
  make check-local
```

---

## Проверка структуры тестов

Проверить сбор тестов:
```bash
  docker compose --profile test run --rm api-tooling python -m pytest --collect-only -q
```
---
