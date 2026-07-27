# Runbook: Auth flow

## 1. Назначение

Этот документ описывает **канонический auth flow** в `services/api_gateway` для baseline JWT-аутентификации.

Цели документа:
- зафиксировать основные auth use cases;
- зафиксировать прохождение запроса по слоям системы;
- определить зоны ответственности модулей;
- определить trust boundaries;
- зафиксировать baseline-ограничения текущей реализации.

Документ **не** является ADR и **не** заменяет debugging runbook.

---

## 2. Контекст и границы

Текущая реализация относится к `api_gateway` и использует JWT access token authentication.

Baseline-подход:
- access token only;
- без refresh token flow;
- без token revocation / blacklist;
- без logout invalidation;
- без secret rotation process в текущем baseline;
- `sub` хранит строковое представление `user_id`, так как `users.id` имеет тип `Integer`.

JWT payload baseline:
- `sub`
- `iat`
- `exp`

Source of truth по пользователю:
- JWT используется для аутентификации запроса;
- окончательная идентификация пользователя подтверждается lookup’ом в БД.

---

## 3. Компоненты auth flow

### 3.1. API schemas
Расположение:
- `app/auth/schemas.py`

Ответственность:
- описывают входные и выходные контракты API;
- валидируют shape request/response данных;
- не содержат DB-логики и не работают с JWT напрямую.

Ожидаемые схемы:
- `RegisterRequest`
- `LoginRequest`
- `TokenResponse`
- `UserResponse`

### 3.2. Auth service
Расположение:
- `app/auth/service.py`

Ответственность:
- реализует прикладные auth use cases;
- координирует repository, password hashing, JWT issuing;
- не должен содержать HTTP wiring.

Основные use cases:
- register user
- login user

### 3.3. Auth router
Расположение:
- `app/auth/router.py`

Ответственность:
- принимает HTTP requests;
- использует request/response schemas;
- вызывает service layer;
- мапит доменные ошибки в HTTP status codes.

### 3.4. Auth dependency
Расположение:
- `app/auth/dependencies.py`

Ответственность:
- реализует `get_current_user`;
- извлекает Bearer token;
- декодирует JWT;
- получает пользователя из БД;
- возвращает 401 при отсутствии/невалидности токена или отсутствии пользователя.

### 3.5. User repository
Расположение:
- `app/repositories/users.py`

Ответственность:
- доступ к таблице `users`;
- не бросает `HTTPException`;
- не делает `commit()`;
- возвращает ORM model или `None`.

### 3.6. Password helpers
Расположение:
- `app/security/passwords.py`

Ответственность:
- `hash_password()`
- `verify_password()`

### 3.7. JWT helpers
Расположение:
- `app/security/jwt.py`

Ответственность:
- `create_access_token(user_id: int)`
- `decode_token(token: str)`

---

## 4. Use case: register

### 4.1. Вход
HTTP endpoint:
- `POST /auth/register`

Request contract:
- email
- password

### 4.2. Поток
1. Router принимает request.
2. Pydantic schema валидирует входные данные.
3. Service проверяет, существует ли пользователь с таким email.
4. Если email уже занят — регистрация отклоняется.
5. Пароль хешируется через `hash_password()`.
6. Repository создаёт пользователя.
7. Транзакция фиксируется.
8. Router возвращает `UserResponse`.

### 4.3. Инварианты
- plain password не сохраняется;
- наружу не возвращается `password_hash`;
- уникальность email проверяется до создания пользователя;
- commit не выполняется внутри repository.

---

## 5. Use case: login

### 5.1. Вход
HTTP endpoint:
- `POST /auth/login`

Request contract:
- email
- password

### 5.2. Поток
1. Router принимает request.
2. Pydantic schema валидирует входные данные.
3. Service ищет пользователя по email.
4. Service проверяет пароль через `verify_password()`.
5. При успешной проверке service выпускает JWT через `create_access_token(user.id)`.
6. Router возвращает `TokenResponse`.

### 5.3. Инварианты
- invalid email и invalid password не различаются наружу по деталям;
- access token возвращается как bearer token;
- payload токена ограничен baseline claims.

---

## 6. Use case: protected endpoint

### 6.1. Пример
Protected endpoint:
- `GET /me`

В дальнейшем тот же паттерн применяется к другим защищённым endpoint’ам.

### 6.2. Поток
1. Клиент отправляет `Authorization: Bearer <token>`.
2. Dependency `get_current_user` извлекает токен.
3. `decode_token()` проверяет подпись, структуру payload и обязательные claims.
4. Из `sub` извлекается `user_id`.
5. `UserRepository.get_by_id(user_id)` загружает пользователя из БД.
6. Если пользователь не найден — доступ отклоняется.
7. Endpoint получает объект `User` как уже аутентифицированного пользователя.
8. Router/endpoint возвращает соответствующий response.

### 6.3. Инварианты
- валидный токен без пользователя в БД не даёт доступ;
- `user_id` не берётся из query/body;
- защищённый endpoint доверяет только результату `get_current_user`.

---

## 7. Trust boundaries

### 7.1. Клиентский ввод
Не доверяются:
- request body;
- request headers;
- token string, переданный клиентом.

### 7.2. JWT payload
JWT payload не считается полным source of truth по пользователю.

Разрешается:
- использовать `sub` как идентификатор для DB lookup.

Не разрешается:
- считать claims достаточным основанием без подтверждения через БД.

### 7.3. База данных
БД является source of truth для:
- существования пользователя;
- актуального user record.

---

## 8. Error semantics

Baseline error semantics:
- invalid request body → validation error framework level;
- invalid credentials → `401 Unauthorized`;
- missing token → `401 Unauthorized`;
- malformed token → `401 Unauthorized`;
- user not found after token decode → `401 Unauthorized`;
- DB failure during auth lookup → `503 Service temporarily unavailable` (если сохраняется текущая семантика dependency).

Точная детализация ошибок наружу минимизируется.

---

## 9. Baseline limitations

Текущая реализация сознательно не покрывает:
- refresh tokens;
- logout invalidation;
- token blacklist / revocation;
- session management across devices;
- asymmetric signing;
- advanced role/permission claims;
- key rotation process.

Это baseline-ограничения текущего этапа, а не случайные пропуски.

---

## 10. Summary

Текущий auth flow в `api_gateway` основан на JWT access token authentication.

Ключевые свойства:
- минимальный payload;
- `sub = str(user_id)` для integer PK;
- БД остаётся source of truth по пользователю;
- protected endpoint’ы используют единый dependency-based auth gate.
