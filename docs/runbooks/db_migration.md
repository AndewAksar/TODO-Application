# Runbook: DB migrations (Alembic) in Docker Compose

## 1. Назначение
Этот runbook описывает **строгую последовательность проверки работоспособности системы миграций Alembic** в Docker Compose.
Цель runbook:

- подтвердить, что контейнерная инфраструктура для миграций работает корректно;
- подтвердить, что `api-tooling` является основным рабочим контейнером для миграций;
- проверить, что существующие миграции применяются без ошибок;
- проверить, что новая ревизия миграции создаётся корректно;
- проверить, что файл новой миграции появляется **в рабочем дереве хоста**, а не только внутри контейнера;
- зафиксировать ожидаемую инженерную последовательность действий для разработчика.

---

## 2. Базовые инварианты
В текущей архитектуре приняты следующие правила:
- контейнер `api` — это **runtime-контейнер** приложения;
- контейнер `api-tooling` — это **основной migration/tooling workspace**;
- миграции должны запускаться **через `api-tooling`**;
- генерация новых migration-файлов должна приводить к появлению файлов **на хосте**, в git-tracked рабочем дереве;
- миграции **не должны** выполняться автоматически при старте `api`.

---

## 3. Предварительные условия
Перед началом проверки предполагается, что:

- используется Docker Compose;
- в `docker-compose.yml` существуют сервисы:
  - `api`
  - `api-tooling`
  - `postgres`
- Alembic config внутри контейнера доступен по пути:
  - `/app/services/api_gateway/alembic.ini`
- каталог миграций расположен по пути:
  - `/app/services/api_gateway/migrations`
- `api-tooling` имеет все необходимые зависимости для запуска:
  - `python`
  - `alembic`
  - runtime-зависимости API-сервиса

---

## 4. Этап 1. Поднять инфраструктуру
### 4.1. Полностью пересобрать и поднять контейнеры
```bash
  docker compose down -v
  docker compose up -d --build
```
### 4.2. Проверить состояние контейнеров
```bash
  docker compose ps
```
### 4.3. Убедиться, что Postgres healthy
Проверить, что у контейнера postgres статус `healthy`.
Если контейнер не `healthy`, дальнейшая проверка миграций бессмысленна.

### 4.4. При необходимости посмотреть логи Postgres и API
```bash
  docker compose logs -n 100 postgres
  docker compose logs -n 100 api
```

---

## 5. Этап 2. Проверить, где реально доступен Alembic
### 5.1. Проверить Alembic внутри runtime-контейнера `api`
```bash
  docker compose exec api sh -lc 'which alembic || true; python -m alembic --version || true'
```
### 5.2. Проверить Alembic внутри tooling-контейнера `api-tooling`
```bash
  docker compose --profile test run --rm api-tooling sh -lc 'which alembic || true; python -m alembic --version || true'
```
### 5.3. Ожидаемый результат
Нормальное целевое состояние:
- Alembic доступен в api-tooling;
- migration workflow выполняется через api-tooling;
- api не используется как основное рабочее место для миграций.
- Если Alembic отсутствует в api-tooling, migration workflow считается сломанным.
---

## 6. Этап 3. Проверить базовую конфигурацию migration workspace
### 6.1. Проверить рабочую директорию и переменные окружения внутри `api-tooling`
```bash
  docker compose --profile test run --rm api-tooling sh -lc 'pwd; ls -la; echo "ALEMBIC_CONFIG=$ALEMBIC_CONFIG"'
```
### 6.2. Что нужно подтвердить
Нужно подтвердить, что:
- контейнер запускается корректно;
- Alembic config указывает на ожидаемый путь;
- файловая структура API-сервиса доступна внутри контейнера;
- контейнер действительно видит migration-дерево.
---

## 7. Этап 4. Проверить применение существующих миграций
### 7.1. Канонический способ
```bash
  make migrate
```
### 7.2. Эквивалентная прямая команда
```bash
  docker compose --profile test run --rm api-tooling alembic upgrade head
```
### 7.3. Проверить текущую ревизию
```bash
  docker compose --profile test run --rm api-tooling alembic current
```
### 7.4. Ожидаемый результат
Нужно подтвердить, что:
- команда upgrade head завершается без ошибок;
- база доходит до актуального head revision;
- Alembic не падает на конфигурации, импортах или подключении к БД.
- Если upgrade head не работает, система миграций считается неработоспособной.
---

## 8. Этап 5. Проверить факт применения схемы к базе
### 8.1. Посмотреть список таблиц в Postgres
```bash
  docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
```
### 8.2. Если переменные неизвестны — посмотреть их в контейнере
```bash
  docker compose exec postgres env | grep POSTGRES
```
### 8.3. Проверить зарегистрированные таблицы SQLAlchemy metadata
```bash
  docker compose --profile test run --rm api-tooling python -c "import app.models; from app.db import Base; print(sorted(Base.metadata.tables.keys()))"
```
### 8.4. Что проверяем
Нужно сопоставить:
- что ожидается по metadata;
- что реально создано в БД.

Это не абсолютно исчерпывающая проверка, но это хороший smoke-level контроль согласованности модели и схемы.

---

## 9. Этап 6. Проверить генерацию новой миграции
### 9.1. Цель проверки
На этом этапе нужно доказать, что:
- alembic revision -m "..." работает через api-tooling;
- новый migration-файл создаётся;
- файл появляется на хосте, а не только внутри контейнера.

### 9.2. Создать probe-ревизию
```bash
  docker compose --profile test run --rm api-tooling alembic revision -m "migration_tooling_probe"
```
### 9.3. Проверить наличие файла на хосте
```bash
  find . -type f | grep "migration_tooling_probe" || true
  git status
```
### 9.4. Проверить наличие файла внутри контейнера
```bash
  docker compose --profile test run --rm api-tooling sh -lc 'find /app -type f | grep "migration_tooling_probe" || true'
```
### 9.5. Ожидаемый результат
Правильное состояние:
- probe-файл виден на хосте;
- git status показывает новый migration-файл;
- файл существует не только в контейнере, но и в рабочем дереве разработчика.

Неправильное состояние:
- файл создаётся только внутри контейнера;
- git status на хосте ничего не показывает;
- после завершения контейнера файл исчезает.

Если файл не появляется на хосте, migration workflow считается архитектурно неверным для разработки.

---

## 10. Этап 7. Очистить probe-ревизию
### 10.1. Удалить тестовый migration-файл на хосте
Удалить созданный probe-файл вручную из каталога migrations/versions.

### 10.2. Проверить, что рабочее дерево снова чистое
```bash
  git status
```
### 10.3. Зачем это нужно
Probe-ревизия нужна только для верификации migration workflow.
Её нельзя оставлять в репозитории, потому что это:
- мусорная ревизия;
- ложная история схемы;
- источник будущих конфликтов.

## 11. Этап 8. Дополнительные команды диагностики
### 11.1. Посмотреть историю миграций
```bash
  docker compose --profile test run --rm api-tooling alembic history --verbose
```
### 11.2. Посмотреть текущий head
```bash
  docker compose --profile test run --rm api-tooling alembic heads
```
### 11.3. Проверить структуру migration-дерева
```bash
  docker compose --profile test run --rm api-tooling sh -lc 'ls -R /app/services/api_gateway/migrations'
```

---

## 12. Критерии исправной системы миграций
Система миграций считается работоспособной, если одновременно выполняются все условия:
- postgres успешно поднимается и становится healthy;
- api-tooling запускается без ошибок;
- Alembic доступен внутри api-tooling;
- alembic upgrade head выполняется без ошибок;
- схема реально применяется к БД;
- alembic revision -m "..." создаёт новый migration-файл;
- новый migration-файл появляется в рабочем дереве хоста;
- probe-файл можно удалить без побочных эффектов;
- git status после cleanup возвращается в чистое состояние.

---

## 13. Канонический повседневный сценарий

При изменении модели, рабочая последовательность должна быть такой:
```commandline
docker compose up -d --build
make makemigration M="describe change"
make migrate
git status
```
