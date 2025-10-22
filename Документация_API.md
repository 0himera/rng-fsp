# RandomTrust API: Научно-техническое описание

## 1. Общая архитектура

RandomTrust Backend предоставляет набор REST-эндпоинтов, построенных на FastAPI, обеспечивая прозрачный процесс генерации случайных последовательностей из гибридного источника энтропии. Ключевые подсистемы:

- **Entropy Service** — моделирует стохастический «гул проводов» и хаотический аттрактор Лоренца, формируя энтропийный пул.
- **RNG Service** — инициализирует поток ChaCha20 с использованием сгенерированного семени, сохраняет последовательности в MinIO и метаданные в PostgreSQL.
- **Audit Service** — принимает внешние последовательности для сравнительного анализа.
- **Analysis Service** — запускает статистические тесты (frequency, runs, chi_square) для подтверждения качества случайности.

Все сервисы работают поверх инфраструктуры: PostgreSQL (хранение данных), Redis (метаданные генераций), MinIO (артефакты).

## 2. Список эндпоинтов

### 2.1. Модуль энтропии (`/api/entropy`)

#### POST `/mix`

- **Назначение**: выполнить новую симуляцию источников энтропии.
- **Тело запроса** (`EntropyMixRequest`):
  - `noise_seed`: `int | null` — исходный seed шума.
  - `parameters`: объект с параметрами стохастической модели (`duration_ms`, `hum_amplitude`, `noise_amplitude`, `spike_density`, `spike_amplitude`).
- **Ответ** (`EntropyMixResponse`):
  - `simulation_id`: UUID.
  - `seed_hex`: шестнадцатеричное представление семени.
  - `metrics`: `snr_db`, `spectral_deviation_percent`, `lyapunov_exponent`.

##### Пример запроса: POST /api/entropy/mix

```bash
curl -X POST "http://localhost:8000/api/entropy/mix" \
  -H "Content-Type: application/json" \
  -d '{
        "noise_seed": 42,
        "parameters": {
          "duration_ms": 250,
          "hum_amplitude": 0.4,
          "noise_amplitude": 0.7,
          "spike_density": 0.05,
          "spike_amplitude": 0.2
        }
      }'
```

#### GET `/simulations`

- **Назначение**: получить список сохранённых симуляций.
- **Параметры**: `limit` (1–100), `offset` (≥0).
- **Ответ**: массив `EntropySimulationSummary` с полями `id`, `created_at`, `updated_at`, `noise_seed`, `metrics`, `seed_hex`.

##### Пример запроса: GET /api/entropy/simulations

```bash
curl "http://localhost:8000/api/entropy/simulations?limit=10&offset=0"
```

#### GET `/simulations/{id}`

- **Назначение**: подробное описание конкретной симуляции.
- **Ответ** (`EntropySimulationDetail`): включает `noise_config`, `pool_hash`, `chaos_checksum`, пути к артефактам (`noise_raw_path`, `chaos_raw_path`) и структуру `chaos_run` (конфигурация аттрактора, `lyapunov_exponent`, контрольная сумма траектории).

##### Пример запроса

```bash
curl "http://localhost:8000/api/entropy/simulations/<simulation_id>"
```

### 2.2. Генератор случайных чисел (`/api/rng`)

#### POST `/generate`

- **Назначение**: инициировать новый запуск ChaCha20.
- **Тело запроса** (`RNGGenerateRequest`):
  - `length`: количество байтов (1–1 000 000).
  - `noise_seed`: необязательный seed для энтропии.
  - `parameters`: настройки шума, аналогичные `/entropy/mix`.
- **Параметры запроса**: `format` — `hex` (по умолчанию) или `ints`.
- **Ответ** (`RNGGenerateResponse`):
  - `run_id`: UUID генерации.
  - `format`: выбранный формат данных.
  - `data`: строка hex или массив целых.
  - `entropy_metrics`: значения `snr_db`, `spectral_deviation_percent`, `lyapunov_exponent`.

**Пример запроса**

```bash
curl -X POST "http://localhost:8000/api/rng/generate?format=hex" \
  -H "Content-Type: application/json" \
  -d '{
        "length": 256,
        "noise_seed": 31415,
        "parameters": {
          "duration_ms": 180,
          "noise_amplitude": 0.65,
          "spike_density": 0.04
        }
      }'
```

#### GET `/runs`

- **Назначение**: получить историю генераций.
- **Параметры**: `limit`, `offset`.
- **Ответ**: массив `RNGRunSummary` (ID, связанная симуляция, формат, длина, метрики, `seed_hash`, путь экспорта, метки времени).

**Пример запроса**

```bash
curl "http://localhost:8000/api/rng/runs?limit=20&offset=0"
```

#### GET `/runs/{id}`

- **Назначение**: детальная информация о генерации.
- **Ответ** (`RNGRunDetail`): расширяет сводку, добавляя `run_checksum` (hex) и массив `test_reports` с результатами статистических тестов (название, статус, статистика, дополнительные метрики).

**Пример запроса**

```bash
curl "http://localhost:8000/api/rng/runs/<run_id>"
```

#### GET `/runs/{id}/export`

- **Назначение**: выгрузить сохранённую последовательность в виде текстового файла битовой строки.
- **Параметры**: `min_bits` (по умолчанию 1 000 000). Если фактическая длина меньше, возвращается HTTP 422 с деталями (`available_bits`, `required_bits`).
- **Ответ**: поток `text/plain` с `Content-Disposition: attachment`.

**Пример запроса**

```bash
curl -OJ "http://localhost:8000/api/rng/runs/<run_id>/export?min_bits=1000000"
```

### 2.3. Аудит (`/api/audit`)

#### POST `/upload`

- **Назначение**: загрузить внешнюю последовательность для проверки.
- **Тело запроса** (`AuditSequenceRequest`):
  - `name`: строка (3–255 символов).
  - `description`: опциональная строка.
  - `data`: hex-представление последовательности.
- **Ответ** (`AuditSequenceResponse`): `audit_id`, `status` (`stored`).

**Пример запроса**

```bash
curl -X POST "http://localhost:8000/api/audit/upload" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "external-sample",
        "description": "Проверка внешнего генератора",
        "data": "deadbeefcafebabe"
      }'
```

### 2.4. Статистический анализ (`/api/analysis`)

#### GET `/tests`

- **Назначение**: перечень доступных тестов (`frequency`, `runs`, `chi_square`).

**Пример запроса**

```bash
curl "http://localhost:8000/api/analysis/tests"
```

#### POST `/runs/{id}`

- **Назначение**: запустить выбранные тесты над сохранённой генерацией.
- **Тело** (`AnalysisRequest`): `tests` — список названий тестов или `null` для полного набора.
- **Ответ** (`RunAnalysisResponse`): `run_id`, `export_path`, `outcomes` — массив `TestOutcomeView` (`name`, `passed`, `statistic`, `threshold`, `details`). Результаты дополнительно сохраняются в таблицу `test_reports` и доступны через `GET /api/rng/runs/{id}`.

**Пример запроса**

```bash
curl -X POST "http://localhost:8000/api/analysis/runs/<run_id>" \
  -H "Content-Type: application/json" \
  -d '{
        "tests": ["frequency", "runs"]
      }'
```

#### POST `/audits/{id}`

- **Назначение**: проанализировать загруженную внешнюю последовательность.
- **Тело**: аналогично `AnalysisRequest`.
- **Ответ** (`AuditAnalysisResponse`): `audit_id`, `data_hash`, `outcomes`.

**Пример запроса**

```bash
curl -X POST "http://localhost:8000/api/analysis/audits/<audit_id>" \
  -H "Content-Type: application/json" \
  -d '{
        "tests": null
      }'
```

## 3. Ошибки и коды ответов

- **422** — некорректные параметры (например, `length > 1_000_000`, `min_bits` превышает фактическую длину).
- **404** — объект не найден (симуляция, генерация, аудит).
- **409** — не используется в текущей версии, зарезервирован под конфликты состояния.
- **500** — внутренняя ошибка (например, недоступность MinIO или БД).

## 4. Хранилище данных и артефактов

- **PostgreSQL**: таблицы `entropy_simulations`, `chaos_runs`, `rng_runs`, `audit_uploads`, `test_reports`.
- **MinIO**: бинарные артефакты шумов, хаотических траекторий и генераций (`runs/<run_id>/sequence.bin`).
- **Redis**: метаданные ChaCha20 (seed/nonce, счётчик блоков).

## 5. Процесс верификации тиража

1. Вызов `POST /api/rng/generate` фиксирует энтропию, ChaCha20 seed, хеши и сохраняет бинарный файл последовательности.
2. Через `POST /api/analysis/runs/{id}` выполняются статистические тесты; результаты сохраняются в `test_reports`.
3. При необходимости выгружается битовый файл (`GET /api/rng/runs/{id}/export`) для сторонних тестовых батарей (NIST STS, Dieharder).
4. Аудиторы загружают собственные выборки (`POST /api/audit/upload`) и проводят анализ (`POST /api/analysis/audits/{id}`).

## 6. Пример сценария (лотерейный тираж)

1. Оператор вызывает `POST /api/rng/generate` с параметрами длины и seed.
2. Отображает пользователям метрики энтропии (`entropy_metrics` в ответе).
3. Запускает аналитические тесты `POST /api/analysis/runs/{run_id}` и визуализирует результаты.
4. Предоставляет ссылку на выгрузку битового файла для независимой проверки.
5. Сохраняет отчёты (`test_reports`) и метаданные для постериорной верификации.
