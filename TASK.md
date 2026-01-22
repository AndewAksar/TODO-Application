# Техническое задание

## Event-Driven TODO Application (Python / FastAPI / Kafka)

### 1. Цель проекта
Разработать многопользовательское TODO-приложение с REST API и SPA-клиентом, построенное по event-driven архитектуре с использованием Kafka, микросервисного подхода, JWT-аутентификации и асинхронного Python-стека.

Проект предназначен:
- для демонстрации архитектурного мышления;
- для демонстрации работы с Kafka, cron, async IO;
- как портфолио-проект уровня Middle+.

### 2. Архитектура (концептуально)
Система состоит из 5 логических компонентов:

```
Frontend (SPA, static)
        |
        | HTTP (JWT)
        v
API Service (FastAPI)
        |
        | SQL
        v
PostgreSQL  ←────────── Scheduler Service
        |                     |
        |                     | SQL
        |                     v
        |                PostgreSQL
        |
        | Kafka (events)
        v
Kafka Broker  ─────────→  Mailer Service  ─→ SMTP (Mailjet)
```

### 3. Архитектурные принципы
#### 3.1 Source of Truth
- PostgreSQL — единственный источник истины.
- Kafka НЕ используется как хранилище состояния.

#### 3.2 Event-Driven подход
- Все значимые изменения состояния порождают доменные события.
- Сервисы не вызывают друг друга напрямую.
- Внешние эффекты (email) — только через события.

#### 3.3 Weak Coupling
- API не знает, кто и как обрабатывает события.
- Mailer не знает, кто инициировал событие.
- Scheduler не отправляет письма напрямую.

### 4. Технологический стек (обязательный)
**Backend / API**
- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0 (async)
- Alembic
- PostgreSQL
- JWT (Bearer token)
- Kafka Producer

**Scheduler**
- Python
- APScheduler (cron-trigger)
- SQLAlchemy (read-only доступ к DB)
- Kafka Producer

**Mailer**
- Python
- Kafka Consumer
- SMTP (Mailjet)
- Jinja2 (email templates)

**Infrastructure**
- Kafka (+ Zookeeper или KRaft)
- Docker
- Docker Compose
- Nginx (static frontend)
- GitHub Actions (CI)

### 5. Доменные сущности (Data Model)
**User**
- `id`: UUID
- `email`: str (unique)
- `password_hash`: str
- `created_at`: datetime

**Task**
- `id`: UUID
- `user_id`: UUID (FK)
- `title`: str
- `done`: bool
- `created_at`: datetime
- `done_at`: datetime | null

**Индексы:**
- `(user_id)`
- `(user_id, done)`

### 6. Аутентификация и авторизация
**JWT**
- Stateless
- Payload:

```json
{
  "sub": "user_id",
  "iat": timestamp,
  "exp": timestamp
}
```

**Правила**
- JWT передаётся через `Authorization: Bearer <token>`.
- Все эндпоинты `/tasks/*` требуют валидного токена.
- User ID всегда извлекается из JWT, не из body/query.

### 7. REST API (контракты)
**Auth**

| Метод | Endpoint        | Назначение     |
|------:|-----------------|----------------|
| POST  | `/auth/register` | Регистрация    |
| POST  | `/auth/login`    | Получение JWT  |

**Tasks**

| Метод | Endpoint       | Описание                   |
|------:|----------------|----------------------------|
| GET   | `/tasks`        | Список задач пользователя |
| POST  | `/tasks`        | Создание задачи           |
| PATCH | `/tasks/{id}`   | Обновление (done/title)   |
| DELETE| `/tasks/{id}`   | Удаление                  |

### 8. Доменные события (Kafka)
**Общие правила**
- Все события immutable.
- Содержат `event_id` (UUID).
- Содержат `occurred_at`.
- Сериализация: JSON.
- Kafka delivery semantics: at-least-once.

#### 8.1 TaskCreated
```json
{
  "event_id": "uuid",
  "type": "task.created",
  "occurred_at": "ISO8601",
  "user_id": "uuid",
  "task_id": "uuid",
  "title": "string"
}
```

#### 8.2 TaskCompleted
```json
{
  "event_id": "uuid",
  "type": "task.completed",
  "occurred_at": "ISO8601",
  "user_id": "uuid",
  "task_id": "uuid"
}
```

#### 8.3 DailyDigestRequested
```json
{
  "event_id": "uuid",
  "type": "email.daily_digest.requested",
  "occurred_at": "ISO8601",
  "user_id": "uuid",
  "email": "string",
  "stats": {
    "total": int,
    "done": int,
    "undone": int
  },
  "undone_titles": ["string"]
}
```

### 9. Scheduler Service
**Назначение**
- Раз в сутки (00:00).
- Формирует ежедневные отчёты.

**Алгоритм**
- По cron-триггеру запускается задача.
- Получает список пользователей.
- Для каждого пользователя:
  - агрегирует задачи;
  - формирует `DailyDigestRequested`;
  - публикует событие в Kafka.
- Scheduler не отправляет email.

### 10. Mailer Service
**Назначение**
- Асинхронная обработка email-событий.

**Поведение**
- Подписывается на Kafka topic `events`.
- При получении `DailyDigestRequested`:
  - проверяет `event_id` (идемпотентность);
  - формирует письмо;
  - отправляет SMTP;
  - сохраняет `event_id` как обработанный;
  - commit offset только после успешной отправки.

### 11. Идемпотентность
**Требование**
- Повторная доставка Kafka-сообщения не должна приводить к повторной отправке email.

**Решение**
- Таблица `processed_events`:
  - `event_id` (PK)
  - `processed_at`

### 12. Frontend (SPA)
**Характеристики**
- Статический frontend.
- HTML / CSS / JS.
- Fetch / Ajax.
- JWT хранится в LocalStorage.
- Общение только через API.

### 13. Docker / Deployment
**Обязательные сервисы**
- api
- scheduler
- mailer
- postgres
- kafka
- zookeeper (если нужно)
- frontend (nginx)

**Требование**
- `docker compose up` поднимает всю систему.
- Конфигурация через `.env`.

### 14. CI/CD (минимум)
**GitHub Actions:**
- lint
- tests
- build docker images

**Тесты:**
- unit (domain logic)
- API tests (FastAPI TestClient)

### 15. Критерии готовности проекта
Проект считается завершённым, если:
- CRUD задач работает;
- JWT корректно защищает API;
- доменные события публикуются;
- scheduler ежедневно публикует digest-события;
- mailer обрабатывает события асинхронно;
- Kafka используется осмысленно, а не формально;
- вся система поднимается одной командой.
