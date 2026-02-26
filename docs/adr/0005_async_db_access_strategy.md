# ADR-0005: Async Database Access Strategy

## Status
Accepted

## Context

Проект построен на FastAPI (async-first framework).
Необходимо выбрать модель доступа к базе данных.

## Decision

Используется:

- SQLAlchemy 2.0
- Async engine
- async_sessionmaker
- Dependency injection через get_session
- Явные транзакционные границы

## Alternatives Considered

1. Синхронный SQLAlchemy — отклонено (блокировка event loop).
2. Полностью ORM-free подход — отклонено (низкий уровень абстракции).
3. Другие ORM — отклонено (меньшая зрелость/экосистема).

## Consequences

Плюсы:
- Консистентность с async-архитектурой.
- Предсказуемый lifecycle сессий.
- Хорошая масштабируемость.

Минусы:
- Более высокая сложность.
- Требует дисциплины при работе с транзакциями.
