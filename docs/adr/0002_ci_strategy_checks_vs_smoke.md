# ADR-0002: CI Strategy — Code Checks vs Docker Smoke

## Status
Accepted

## Context

Проект содержит:
- Python-код (lint, types, tests)
- Docker-инфраструктуру
- Несколько сервисов с healthchecks

Один общий pipeline усложняет диагностику и смешивает разные классы ошибок.

## Decision

CI разделён на два независимых workflow:

1. ci.yml
   - ruff (lint)
   - ruff format check
   - mypy
   - pytest

2. docker-smoke.yml
   - docker compose config
   - build образов
   - запуск сервисов
   - healthchecks
   - smoke HTTP-запросы

Цель — изолировать:
- логические ошибки кода
- инфраструктурные/runtime ошибки

## Alternatives Considered

1. Один объединённый pipeline — отклонено (сложная диагностика).
2. Проверки только на уровне кода — отклонено (пропуск runtime-ошибок).
3. Проверки только Docker — отклонено (недостаточный контроль качества кода).

## Consequences

Плюсы:
- Быстрая диагностика класса проблемы.
- Чёткое разделение ответственности.
- Более предсказуемый CI.

Минусы:
- Увеличение времени CI.
- Более сложная конфигурация.
