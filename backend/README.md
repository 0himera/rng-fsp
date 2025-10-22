# RandomTrust Backend

## Overview

`randomtrust-backend` реализует FastAPI приложение и сопутствующие сервисы для гибридного генератора случайных чисел RandomTrust. MVP сосредоточен на симуляции стохастического "гула проводов", хаотической динамике (аттрактор Лоренца) и REST API для генерации/аудита последовательностей.

## Структура проекта

```text
backend/
  pyproject.toml
  README.md
  docker-compose.yml
  .env.example
  randomtrust/
    __init__.py
    app.py
    core/
      config.py
      database.py
      logging.py
      redis.py
      storage.py
    api/
      __init__.py
      dependencies.py
      routers/
        __init__.py
        entropy.py
        rng.py
        audit.py
    entropy/
      simulator.py
      chaos.py
      mixer.py
    rng/
      generator.py
    models/
      __init__.py
      base.py
      entropy.py
      rng_run.py
      test_report.py
      audit.py
    repositories/
      __init__.py
      entropy.py
      rng.py
      test_report.py
      audit.py
    services/
      __init__.py
      unit_of_work.py
      entropy_service.py
      rng_service.py
      audit_service.py

  alembic/
    env.py
    versions/
      20241022_0001_initial_schema.py

  docker/
    fastapi/Dockerfile
```

## Быстрый старт

1. Установите Poetry 1.8+ в классическом режиме.
2. Выполните `poetry install` из директории `backend/`.
3. Создайте файл `.env` по шаблону `.env.example`.
4. Запустите инфраструктуру (Postgres, Redis, MinIO и FastAPI): `docker compose up --build`.
5. Примените миграции БД (внутри контейнера или локально): `docker compose run --rm fastapi-app poetry run alembic upgrade head`.
6. API будет доступен на `http://localhost:8000`.

### Основные эндпоинты

- `POST /api/entropy/mix` — запускает симуляцию шума + хаоса и сохраняет результат.
- `GET /api/entropy/simulations`, `GET /api/entropy/simulations/{id}` — перечисление и детальный просмотр сохранённых энтропийных прогонов.
- `POST /api/rng/generate` — генерирует последовательность (hex/ints) на базе свежей энтропии.
- `GET /api/rng/runs`, `GET /api/rng/runs/{id}` — доступ к истории генераций и привязанным отчётам.
- `GET /api/rng/runs/{id}/export` — выгрузка текстового файла ≥1 000 000 бит для статистических тестов.
- `POST /api/audit/upload` — сохраняет предоставленную hex-последовательность для аудита.
- `POST /api/analysis/runs/{id}` — запускает набор статистических тестов над сохранённой генерацией.
- `POST /api/analysis/audits/{id}` — анализирует загруженную внешнюю последовательность.
- `GET /api/analysis/tests` — возвращает перечень доступных тестов (frequency, runs, chi_square).

### Проверка работы

```bash
curl -X POST http://localhost:8000/api/rng/generate \
  -H "Content-Type: application/json" \
  -d '{"length": 64, "noise_seed": 42, "parameters": {"duration_ms": 200}}'

curl -X POST http://localhost:8000/api/audit/upload \
  -H "Content-Type: application/json" \
  -d '{"name": "demo", "data": "deadbeef"}'

curl -X POST http://localhost:8000/api/analysis/runs/<run_id> \
  -H "Content-Type: application/json" \
  -d '{}'

curl -OJ "http://localhost:8000/api/rng/runs/<run_id>/export?min_bits=1000000"
```

## Кодстайл

- Формат и статический анализ: `ruff`, `mypy`.
- Тесты: `pytest`, `pytest-asyncio`.
- Логирование структурировано через `structlog`.

## Лицензирование

Используем только открытые зависимости; проприетарные решения запрещены согласно требованиям.
