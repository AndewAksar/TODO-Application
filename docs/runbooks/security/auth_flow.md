# Auth Flow — Security Runbook

## 1. Назначение

Описывает эталонный поток аутентификации / авторизации
и точки контроля безопасности в API Gateway.

---

## 2. Область применения

- эндпоинты:
  - `/auth/register`
  - `/auth/login`
- защищённые эндпоинты (например: `/me`, `/tasks/*`)
- dependency `get_current_user`
- JWT encode / decode
- `UserRepository` + DB

---

## 3. Инварианты (обязательные)

### 3.1 Общие правила

- **По умолчанию всё закрыто**: защищённые эндпоинты группируются в router с глобальной dependency:
  `APIRouter(dependencies=[Depends(get_current_user)])`

- `get_current_user`:
  - не возвращает `None`;
  - только:
    - `return user`, либо
    - `raise HTTPException(401)`.

- **Источник истины о пользователе — БД**:
  - токен не заменяет запрос пользователя из БД.

- **Ошибка аутентификации всегда выглядит одинаково наружу**:
  - `401 Unauthorized`;
  - без раскрытия причин.

### 3.2 Запрещено

- принимать токен не из `Authorization: Bearer <token>`;
- отключать проверку `exp` / `iat` «в dev» (любые bypass должны быть отдельным, явно запрещённым режимом с ADR и дедлайном).

---

## 4. Потоки

### 4.1 Register

**Цель:** создать пользователя и сохранить `password_hash`.

**Шаги:**

1. Валидация входных данных (Pydantic).
2. `repo.get_by_email(email)`:
   - если есть → `409 Conflict`.
3. `hash_password(password)` → `password_hash`.
4. `repo.create_user(email, password_hash, username=None)`.
5. `session.commit()`.
6. Вернуть `UserResponse` (без `password_hash`).

**Контроль:**

- уникальность email;
- отсутствие утечек пароля / хеша:
  - в ответе;
  - в логах.

---

### 4.2 Login

**Цель:** выдать access token.

**Шаги:**

1. Валидация входных данных.
2. `repo.get_by_email(email)`:
   - если нет → `401 Unauthorized`.
3. `verify_password(plain, user.password_hash)`:
   - если `false` → `401 Unauthorized`.
4. `create_access_token(user.id)` → `TokenResponse(token_type="bearer")`.

**Контроль:**

- одинаковая реакция на неверный email / пароль (без раскрытия причины);
- токен не логируется.

---

### 4.3 Access protected endpoint (пример: `/me`)

**Цель:** отдать ресурс только аутентифицированному пользователю.

**Шаги:**

1. FastAPI вызывает `get_current_user`.
2. Dependency:
   - читает `Authorization`;
   - проверяет `Bearer`;
   - вызывает `decode_token()`.
3. `repo.get_by_id(decoded.user_id)`:
   - если пользователь отсутствует → `401 Unauthorized`;
   - иначе → `return user`.
4. Эндпоинт получает `User` и возвращает `UserResponse`.

**Контроль:**

- `/me` без токена → `401`;
- токен мусор → `401`;
- `exp` в прошлом → `401`;
- `sub` валидный, но пользователь отсутствует → `401`;
- валидный токен + пользователь существует → `200`.

---

## 5. Типовые dependency bugs и последствия

**Категория:** логическая ошибка связки `dependency → проверка → решение`.

### 5.1 Ошибки

- забыли повесить `Depends(get_current_user)` → публичный доступ;
- приняли пустой токен как «аноним» → обход auth;
- поймали исключение и вернули `None` → роут продолжил работу;
- раскрыли детали (`user not found` vs `bad token`) → утечка информации;
- доверили payload (например `is_admin`) без сверки с БД → escalation.

### 5.2 Последствия

- полный обход авторизации;
- в продакшене — инцидент уровня **P0**.

---

## 6. Checklist перед мерджем (Definition of Done для auth-flow)

- защищённые роуты собраны в router с глобальной dependency;
- `get_current_user` не возвращает `None`;
- негативные тесты на `401` написаны и проходят;
- токены / пароли / секреты не логируются;
- CI — зелёный.
