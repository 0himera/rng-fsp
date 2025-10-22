# RandomTrust Backend

## Overview

`randomtrust-backend` реализует FastAPI приложение и сопутствующие сервисы для гибридного генератора случайных чисел RandomTrust. MVP сосредоточен на симуляции стохастического "гула проводов", хаотической динамике (аттрактор Лоренца) и REST API для генерации/аудита последовательностей.

## Структура проекта

```text
backend/
  randomtrust/
    api/              # FastAPI роутеры и зависимости
    core/             # конфиг, соединения с БД/Redis/MinIO, логирование
    entropy/          # генерация шума и хаотической траектории
    rng/              # криптографический генератор (ChaCha20) и фабрика
    services/         # бизнес-слой (EntropyService, RNGService, AuditService)
    repositories/     # единицы работы и доступ к БД
    models/           # SQLAlchemy модели
  alembic/            # миграции БД
  docker/             # Dockerfile и инфраструктурные скрипты
```

## Конвейер генерации случайной последовательности

1. **EntropyMixer** (`randomtrust/entropy/mixer.py`) объединяет стохастический шум (`simulator.py`) и хаотическую траекторию Лоренца (`chaos.py`).
2. **EntropyService.create_entropy()** (`randomtrust/services/entropy_service.py`) вызывает миксер, сохраняет сид, метрики (`snr_db`, `spectral_deviation_percent`, `lyapunov_exponent`) и сырьё в MinIO БД.
3. **RNGService.generate()** (`randomtrust/services/rng_service.py`) получает свежий сид, создаёт `ChaCha20RNG` (`randomtrust/rng/generator.py`) и генерирует поток в формате `hex` или `ints`.
4. **Хранение и отчёты**: последовательность попадет в MinIO, хэши и метрики записываются в `rng_runs`; последующие тесты (`analysis_service.py`) используют тот же набор артефактов.

Повторный запуск с тем же `noise_seed` воспроизводит идентичный ChaCha20 поток; без seed энтропия формируется заново и последовательность уникальна.

## Быстрый старт

1. Создайте файл `.env` по шаблону `.env.example`.
2. Запустите инфраструктуру (Postgres, Redis, MinIO и FastAPI): `docker compose up --build` из директории `backend/`.
3. Примените миграции БД (внутри контейнера или локально): `docker compose run --rm fastapi-app poetry run alembic upgrade head`.
4. API будет доступен на `http://localhost:8000`.

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
