# CAVI Async Calculator Service

Асинхронный сервис для расчёта индекса CAVI (Cardio-Ankle Vascular Index).

## Описание

Сервис принимает запросы на расчёт CAVI индекса, выполняет расчёт с задержкой 5-10 секунд (имитация длительной операции), и отправляет результаты обратно в основной Go бекенд.

## API Endpoints

### POST /api/calculate

Запуск асинхронного расчёта CAVI.

**Request:**
```json
{
    "calculation_id": 1,
    "systolic_pressure": 120,
    "diastolic_pressure": 80,
    "pulse_wave_velocity": 8.5,
    "groups": [
        {
            "group_id": 1,
            "age_group": "young",
            "disease_type": null
        },
        {
            "group_id": 2,
            "age_group": "elderly",
            "disease_type": "hypertension"
        }
    ]
}
```

**Response (202 Accepted):**
```json
{
    "status": "accepted",
    "message": "Calculation started",
    "calculation_id": 1,
    "groups_count": 2
}
```

### GET /api/health

Проверка работоспособности сервиса.

**Response:**
```json
{
    "status": "ok",
    "service": "cavi-async-calculator",
    "version": "1.0.0"
}
```

## Формула CAVI

```
CAVI = M × (2ρ / ΔP) × ln(Ps/Pd) × PWV² + A
```

Где:
- M - коэффициент возрастной группы (young=0.9, middle=1.0, elderly=1.1)
- ρ - плотность крови (1.05 г/мл)
- ΔP - разница давлений (Ps - Pd)
- Ps - систолическое давление
- Pd - диастолическое давление
- PWV - скорость пульсовой волны
- A - коэффициент заболевания (diabetes=1.2, hypertension=1.0, none=1.0)

## Запуск

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python manage.py runserver 0.0.0.0:8001
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| DJANGO_SECRET_KEY | Секретный ключ Django | - |
| DEBUG | Режим отладки | True |
| GO_BACKEND_URL | URL основного Go бекенда | http://localhost:8080 |
| GO_BACKEND_TOKEN | Токен для авторизации в Go бекенде | cavi-async-secret-token-8bytes |
| CALCULATION_DELAY_MIN | Минимальная задержка расчёта (сек) | 5 |
| CALCULATION_DELAY_MAX | Максимальная задержка расчёта (сек) | 10 |

## Взаимодействие с Go бекендом

После расчёта сервис отправляет PUT запрос на:
```
PUT {GO_BACKEND_URL}/api/cavi-calculations/{calculation_id}/async-result
```

**Payload:**
```json
{
    "token": "cavi-async-secret-token-8bytes",
    "results": [
        {"group_id": 1, "cavi_index": 7.234},
        {"group_id": 2, "cavi_index": 8.567}
    ]
}
```

Go бекенд проверяет токен и обновляет поля cavi_index в таблице cavi_calculation_groups.

## Тестирование через Insomnia/Postman

### 1. Запуск расчёта (POST к Django сервису)

```bash
curl -X POST http://localhost:8001/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "calculation_id": 1,
    "systolic_pressure": 120,
    "diastolic_pressure": 80,
    "pulse_wave_velocity": 8.5,
    "groups": [
      {"group_id": 1, "age_group": "young", "disease_type": null},
      {"group_id": 2, "age_group": "elderly", "disease_type": "hypertension"}
    ]
  }'
```

### 2. Проверка результатов (GET к Go бекенду)

```bash
curl http://localhost:8080/api/cavi-calculations/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Ручное обновление результата (PUT к Go бекенду)

```bash
curl -X PUT http://localhost:8080/api/cavi-calculations/1/async-result \
  -H "Content-Type: application/json" \
  -d '{
    "token": "cavi-async-secret-token-8bytes",
    "results": [{"group_id": 1, "cavi_index": 7.5}]
  }'
```

## Архитектура

```
┌─────────────────┐     POST /api/calculate      ┌─────────────────┐
│                 │ ──────────────────────────▶  │                 │
│   Go Backend    │                              │  Django Async   │
│   (port 8080)   │  ◀──────────────────────────  │  (port 8001)    │
│                 │   PUT /api/.../async-result  │                 │
└─────────────────┘                              └─────────────────┘
        │                                                │
        │                                                │
        ▼                                                │
┌─────────────────┐                                      │
│   PostgreSQL    │                                      │
│   (port 5432)   │ ◀────────────────────────────────────┘
└─────────────────┘        (через Go Backend)
```
