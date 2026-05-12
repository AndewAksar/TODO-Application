# Runbook: JWT debugging

## 1. Назначение

Этот документ описывает **пошаговую диагностику проблем JWT/auth** в `services/api_gateway`.

Цели документа:
- быстро локализовать источник проблемы;
- разделять ошибки JWT, DB lookup, env/config и import/runtime wiring;
- дать повторяемые команды проверки для local и container-based запусков.

Документ **не** заменяет ADR и **не** описывает целевой auth flow как архитектурное решение.

---

## 2. Типовые симптомы

Наиболее вероятные симптомы:

- `POST /auth/login` не выдаёт token;
- login выдаёт token, но `GET /me` возвращает `401`;
- `GET /me` всегда возвращает `401`;
- токен декодируется с ошибкой;
- пользователь не находится после успешного decode;
- локально тесты проходят, а в контейнере падают;
- в контейнере всё работает, а локально нет;
- auth-related команды ведут себя по-разному в runtime и tooling контейнерах.

---

## 3. Быстрый checklist

Перед углублённой отладкой проверить:

1. Установлен ли `JWT_SECRET_KEY`.
2. Установлен ли `DATABASE_URL` для локальных тестов.
3. Соответствует ли Authorization header формату `Bearer <token>`.
4. Возвращает ли login непустой access token.
5. Декодируется ли token helper’ом `decode_token()`.
6. Существует ли `user_id` из `sub` в БД.
7. Используют ли local / pytest / Docker / Alembic одну и ту же import-модель.
8. Не сломана ли repository-логика lookup пользователя.

---

## 4. Диагностика login

### 4.1. Если login не выдаёт token
Проверить по порядку:

1. Существует ли пользователь с указанным email.
2. Корректен ли `password_hash` у пользователя.
3. Возвращает ли `verify_password()` значение `True` для правильного пароля.
4. Установлен ли `JWT_SECRET_KEY`.
5. Падает ли `create_access_token()` при выпуске токена.
6. Не отличаются ли settings/env между local и container run.

### 4.2. Возможные причины
- пользователь не найден;
- неверный пароль;
- битый или неожиданный `password_hash`;
- отсутствует `JWT_SECRET_KEY`;
- settings загружены не из того окружения;
- runtime и tests используют разные env values.

---

## 5. Диагностика protected endpoint (`/me`)

### 5.1. Если `/me` возвращает `401`
Проверять по порядку:

1. Есть ли header `Authorization`.
2. Используется ли схема `Bearer`.
3. Не пустой ли token.
4. Проходит ли `decode_token(token)`.
5. Не истёк ли `exp`.
6. Корректно ли извлекается `sub`.
7. Приводится ли `sub` к `int`.
8. Находит ли `UserRepository.get_by_id(user_id)` пользователя.
9. Не сломана ли логика dependency `get_current_user`.

### 5.2. Возможные причины
- отсутствует header;
- неверная схема auth;
- токен повреждён;
- токен просрочен;
- токен подписан другим секретом;
- `sub` отсутствует или невалиден;
- пользователь удалён/не существует в БД;
- ошибка в repository lookup;
- ошибка в dependency wiring.

---

## 6. Проверка JWT helper’ов

### 6.1. Что проверять
- `create_access_token()` создаёт token для integer `user_id`;
- `decode_token()` возвращает ожидаемый `user_id`;
- payload содержит `sub`, `iat`, `exp`;
- `sub` сериализуется как строка.

### 6.2. На что обратить внимание
- `users.id` в проекте — `Integer`;
- `sub` должен быть строкой integer value;
- отсутствие `sub` или невозможность привести его к `int` — ошибка токена.

---

## 7. Проверка repository lookup

### 7.1. Что проверять
- `get_by_email(email)` реально ищет по `User.email`;
- `get_by_id(user_id)` реально ищет по `User.id == user_id`;
- repository не делает `commit()`;
- repository не бросает `HTTPException`.

### 7.2. Project-specific risk
Особенно проверять ошибки вида:
- сравнение `User.id == id` вместо `user_id`;
- типовая ошибка “токен валиден, но пользователь никогда не находится”.

---

## 8. Проверка settings / env

### 8.1. Что обязательно
Для JWT/auth baseline должны быть согласованы:
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_EXPIRES_MINUTES`

Для тестов и DB lookup также критичен:
- `DATABASE_URL`

### 8.2. Типовые проблемы
- `JWT_SECRET_KEY` отсутствует;
- local и container environment используют разные значения;
- `DATABASE_URL` не выставлен для local test run;
- settings подхватываются иначе в разных режимах запуска.

---

## 9. Проверка import-root и окружения запуска

### 9.1. Что зафиксировано
Для `api_gateway` должна использоваться одна каноническая import-модель.

### 9.2. Что проверять
- одинаково ли резолвятся импорты в local test run;
- одинаково ли резолвятся импорты в tooling container;
- одинаково ли резолвятся импорты в Alembic;
- не существует ли альтернативного short import root, который случайно работает только в одном режиме.

### 9.3. Типовые симптомы import-root drift
- локально тесты проходят, а в контейнере import error;
- Alembic видит модели иначе, чем pytest;
- один и тот же модуль загружается под разными путями.

---

## 10. Docker vs local

### 10.1. Что учитывать
В проекте локальный и контейнерный запуск — это разные operational contexts.

Проверять нужно отдельно:
- local host venv;
- runtime container;
- tooling container.

### 10.2. Типовые project-specific грабли
- `python -m alembic` и `alembic` не обязаны работать одинаково;
- generated probe migration может быть создан root-owned внутри контейнера;
- root-owned file может ломать local `ruff format`;
- tooling container может иметь другой набор CLI entrypoints, чем host venv.

---

## 11. Полезные команды

### 11.1. Local
```bash
DATABASE_URL='postgresql+asyncpg://x:x@localhost:5432/x' make test-local
mypy .
ruff check .
ruff format .
