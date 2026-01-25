# Bootstrap checklist

Цель bootstrap: подготовить “рельсы” разработки так, чтобы:
- локальные проверки ≈ CI,
- main защищён,
- правила качества формализованы,
- проект можно безопасно масштабировать (сервисы, контракты, инфраструктура).

---

## 0) Definition of Done (DoD) bootstrap

Bootstrap считается завершённым, если:

- [ ] Есть **CI** (lint + format-check + tests) и он зелёный на PR.
- [ ] Включён **Branch Protection / Ruleset**: PR-only merge + required checks.
- [ ] Есть **локальный цикл качества**: venv + pre-commit + команды проверки.
- [ ] Есть **минимальный smoke-тест**, чтобы CI не был пустым.
- [ ] Есть базовая **структура репо** (services/, infra/, docs/, tests/).
- [ ] Есть базовый **logging foundation** (единый формат, stdout, service, request_id заготовка).
- [ ] (event-driven) Есть **контракты**: topics + event catalog + schema правила.

---

## 1) Repo hygiene (обязательное)

### Файлы
- [ ] `.gitignore` (игнор: `.venv/`, `__pycache__/`, `.ruff_cache/`, `.pytest_cache/`, `.mypy_cache/`, `.idea/`, `node_modules/`, `dist/`, `build/`)
- [ ] `.editorconfig` (единый стиль переносов/отступов)
- [ ] `.dockerignore` (ускорение сборки docker)
- [ ] `README.md` (что это, как запускать проверки, как запускать CI)
- [ ] `LICENSE` (если нужно)
- [ ] `.python-version` (если используешь pyenv)

### Проверка
```bash
  git status
