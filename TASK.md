# Техническое задание

## Статус документа

Это исходная продуктовая спецификация и описание целевого направления. Она не
является источником истины для текущего runtime. Текущая архитектура описана в
`docs/architecture/`, HTTP-контракт — в FastAPI OpenAPI, а принятые решения — в
`docs/adr/`.

На текущем этапе реализованы JWT-аутентификация и синхронный user-owned Tasks
CRUD внутри единого `services/api_gateway`. Kafka publishing, outbox,
операционные scheduler/mailer flows и frontend остаются целевыми этапами.

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
**User (текущая модель; ADR 0004)**
- `id`: integer
- `email`: str (unique)
- `username`: str | null (unique)
- `password_hash`: str
- `created_at`: datetime

**Task (текущая модель; ADR 0004)**
- `id`: integer
- `user_id`: integer (FK)
- `title`: str
- `description`: str | null
- `is_done`: bool
- `created_at`: datetime
- `done_at`: datetime | null
- `due_at`: datetime | null
- `updated_at`: datetime


**Индексы:**
- `(user_id)`

Идентификаторы будущих событий могут оставаться UUID; это не меняет integer
primary-key strategy доменных сущностей.

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
| GET   | `/tasks/{id}`   | Получение задачи          |
| PATCH | `/tasks/{id}`   | Обновление (done/title)   |
| DELETE| `/tasks/{id}`   | Удаление                  |

### 8. Планируемые доменные события (Kafka)

**Status: Planned.** Следующие контракты описывают целевое направление; текущий
Tasks CRUD не публикует события.

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
  "user_id": 123,
  "task_id": 456,
  "title": "string"
}
```

#### 8.2 TaskCompleted
```json
{
  "event_id": "uuid",
  "type": "task.completed",
  "occurred_at": "ISO8601",
  "user_id": 123,
  "task_id": 456
}
```

#### 8.3 DailyDigestRequested
```json
{
  "event_id": "uuid",
  "type": "email.daily_digest.requested",
  "occurred_at": "ISO8601",
  "user_id": 123,
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
