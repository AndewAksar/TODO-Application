# TODO Application

Учебное TODO-приложение в production-style: асинхронный Python API, PostgreSQL,
контейнерное окружение и проверяемые границы между HTTP, бизнес-логикой и
доступом к данным.

---

## Текущее состояние

Реализовано:

- единый FastAPI-сервис `services/api_gateway`;
- JWT-аутентификация: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`;
- повторная проверка пользователя из JWT по PostgreSQL;
- защищённый user-owned Tasks CRUD: `POST/GET /tasks` и
  `GET/PATCH/DELETE /tasks/{task_id}`;
- PostgreSQL, SQLAlchemy 2.0 async, asyncpg и Alembic;
- unit-, HTTP contract- и реальные PostgreSQL integration-тесты;
- Docker Compose окружение, отдельная тестовая БД и tooling-контейнер;
- GitHub Actions для текущих code checks, Docker checks и проверки миграций.

Kafka, task-domain events, outbox, рабочие scheduler/mailer flows и полноценный
frontend **запланированы**, но ещё не являются реализованным поведением продукта.
Наличие Kafka, scheduler и mailer контейнеров не означает, что Tasks CRUD уже
работает событийно.

## Текущая архитектура

Планируется:

```text
client / Swagger
       |
       v
Nginx -> services/api_gateway
         ├── auth
         ├── tasks
         ├── repositories
         ├── models.py
         ├── db.py
         └── Alembic migrations
                    |
                    v
               PostgreSQL
```

Backend намеренно не разделён на отдельные auth/todo микросервисы. Возможная
дальнейшая декомпозиция относится к будущей архитектуре и должна иметь
конкретную эксплуатационную причину.

## Стек

- Python 3.12, FastAPI, Pydantic v2;
- SQLAlchemy 2.0 async, asyncpg, PostgreSQL 16, Alembic;
- JWT Bearer authentication;
- pytest, pytest-asyncio, HTTPX, Ruff, mypy;
- Docker Compose, Nginx, GitHub Actions;
- Kafka/Zookeeper как инфраструктурная основа для будущих этапов.

## Быстрый старт

Требуются Git, Make, Docker и Docker Compose. Скопируйте `.env.example` в `.env`
и замените development-секреты при необходимости:

```bash
cp .env.example .env
make up
make migrate
```

После запуска:

- frontend placeholder / Nginx: <http://localhost:8080/>;
- Swagger: <http://localhost:8080/docs>;
- API напрямую: <http://localhost:8008/>.

`make down` останавливает окружение **и удаляет Compose volumes**.

## Основные команды

```bash
make up                 # запустить runtime-окружение
make down               # остановить окружение и удалить volumes
make migrate            # применить Alembic к development DB
make test-unit          # DB-independent unit tests
make test-contract      # DB-independent HTTP contract tests
make test-integration   # real PostgreSQL integration tests
make test               # полный non-flaky набор, включая integration
make lint               # Ruff в api-tooling
make typecheck          # mypy в api-tooling
```

`make test-integration` и `make test` сами поднимают `postgres-test` и применяют
к `todo_test` миграции. Подробности: [локальная разработка](docs/architecture/local-development.md)
и [integration runbook](docs/runbooks/testing/integration_tests.md).

## Тестовые слои

- **Unit:** изолированная бизнес-логика без сети, БД и брокера.
- **HTTP contract:** FastAPI routing, validation и error mapping с заменёнными
  инфраструктурными зависимостями.
- **Integration:** `TaskService` и `TaskRepository` через SQLAlchemy/asyncpg с
  реальным изолированным PostgreSQL.

Выделенный CI job для PostgreSQL integration-тестов запланирован, но текущие
workflow ещё не реализуют это разделение корректно.

## Документация

- [Центральный индекс](docs/README.md)
- [Текущая архитектура](docs/architecture/overview.md)
- [Семантика Tasks API](docs/api/tasks.md)
- [История Task 060](docs/tasks/060_user_owned_tasks_crud.md)
- [ADRs](docs/adr/)
- [Roadmap будущих этапов](ROADMAP.md)
- [Исходное техническое задание и его текущие уточнения](TASK.md)
