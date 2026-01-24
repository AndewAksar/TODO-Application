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

## Локальный запуск проверок

Минимальный набор перед PR:

```bash
  # линтер + форматирование
ruff check .
ruff format .

# типы (если включены)
mypy .

# тесты
pytest -q
```

Установить хуки:

```bash
  pre-commit install
