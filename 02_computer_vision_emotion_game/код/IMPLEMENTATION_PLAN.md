# План реализации: Big Data-инфраструктура для MirMe

> Документ описывает конкретные технические шаги реализации этапов из `mirme_ROADMAP.md`.
> Основан на существующей кодовой базе: `src/main.py` (игра «Покажи эмоцию», OpenCV + MediaPipe + FER+).

---

## Архитектура системы (целевая)

```
[XR-приложение / src/main.py]
        |
        | POST JSON (emotion_task events)
        v
   [n8n Webhook]
        |
        | сохранение
        v
[Cloud.ru Object Storage]   <-- сырые данные (JSON-файлы)
        |
        | чтение (boto3/s3)
        v
  [Python ETL-скрипт]
        |
        | агрегированные метрики
        v
  [Metabase / HTML Dashboard]
        |
        | (Этап 4, опционально)
        v
  [ML-модель → адаптация сложности]
```

---

## Этап 1: Pipeline сбора данных

### 1.1 Cloud.ru Object Storage

1. Зарегистрироваться на [Cloud.ru](https://cloud.ru) и создать проект.
2. Перейти в **Object Storage** → создать бакет `mirme-events` с приватным доступом.
3. Создать сервисного пользователя → скопировать **Access Key** и **Secret Key**.
4. Сохранить ключи в `.env` (добавить в `.gitignore`):

```env
S3_ENDPOINT=https://s3.cloud.ru
S3_BUCKET=mirme-events
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

### 1.2 Запуск n8n через Docker

```bash
# Запуск локально (данные сохраняются в ./n8n-data)
mkdir n8n-data
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v $(pwd)/n8n-data:/home/node/.n8n \
  n8nio/n8n
```

Открыть http://localhost:5678, создать аккаунт.

### 1.3 n8n Workflow «Receive → Save to S3»

Создать workflow из двух нод:

| Нода | Тип | Конфигурация |
|------|-----|--------------|
| Trigger | Webhook | POST, path: `/mirme-event`, respond: immediately |
| Save | AWS S3 | Operation: Upload, Bucket: `mirme-events`, Key: `{{$json.session_id}}/{{$json.timestamp}}.json` |

Webhook URL: `http://localhost:5678/webhook/mirme-event`

### 1.4 Проверка

```bash
curl -X POST http://localhost:5678/webhook/mirme-event \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_001",
    "event_type": "session_start",
    "timestamp": 1708348800
  }'
```

Убедиться, что файл появился в бакете S3.

---

## Этап 2: Интеграция эмоций в pipeline

### 2.1 Модуль отправки событий

Создать файл `src/event_sender.py`:

```python
import json
import time
import threading
import urllib.request
import urllib.error

WEBHOOK_URL = "http://localhost:5678/webhook/mirme-event"

def send_event(payload: dict):
    """Отправляет событие в n8n асинхронно, чтобы не блокировать UI."""
    def _post():
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                WEBHOOK_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=3)
        except urllib.error.URLError as e:
            print(f"[event_sender] Ошибка отправки: {e}")

    threading.Thread(target=_post, daemon=True).start()
```

### 2.2 Структура события `emotion_task`

```json
{
  "session_id": "child_042_20260307",
  "event_type": "emotion_task",
  "target_emotion": "happiness",
  "detected_emotion": "happiness",
  "confidence": 0.87,
  "success": true,
  "duration_frames": 20,
  "timestamp": 1708348820,
  "app_version": "0.1.0"
}
```

### 2.3 Доработка `src/main.py`

В цикл игры добавить вызов `send_event()` в момент засчитывания очка (`score += 1`):

```python
from event_sender import send_event
import time

# В блоке "Game logic", при успехе:
if match_streak >= MATCH_FRAMES_REQUIRED:
    score += 1
    feedback_timer = FEEDBACK_FRAMES

    send_event({
        "session_id": SESSION_ID,          # генерировать при старте: f"session_{int(time.time())}"
        "event_type": "emotion_task",
        "target_emotion": target_emotion,
        "detected_emotion": emotion,
        "confidence": round(emo_conf, 3),
        "success": True,
        "duration_frames": MATCH_FRAMES_REQUIRED,
        "timestamp": int(time.time()),
        "app_version": "0.1.0",
    })
```

Также отправлять `session_start` при запуске и `session_end` при выходе.

### 2.4 Согласие родителя

Перед первым запуском с камерой показывать отдельный экран в OpenCV или простое диалоговое окно через `tkinter`:

```python
import tkinter as tk
from tkinter import messagebox

def request_consent() -> bool:
    root = tk.Tk()
    root.withdraw()
    text = (
        "Приложение использует камеру для распознавания эмоций ребёнка.\n\n"
        "• Видеозапись не сохраняется.\n"
        "• Собираются только результаты упражнений (эмоция, успех/неуспех).\n"
        "• Данные используются для отслеживания прогресса.\n\n"
        "Вы согласны на использование камеры?"
    )
    result = messagebox.askyesno("Согласие на использование камеры", text)
    root.destroy()
    return result
```

Результат согласия записывать в лог и отправлять событием `consent_granted` / `consent_denied`.

---

## Этап 3: Аналитика и визуализация

### 3.1 ETL-скрипт `src/analytics.py`

```python
import boto3, json, os
from collections import defaultdict

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["S3_ENDPOINT"],
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
)

def load_events(bucket: str) -> list[dict]:
    events = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            body = s3.get_object(Bucket=bucket, Key=obj["Key"])["Body"].read()
            events.append(json.loads(body))
    return events

def aggregate(events: list[dict]) -> dict:
    by_session = defaultdict(list)
    for e in events:
        if e.get("event_type") == "emotion_task":
            by_session[e["session_id"]].append(e)

    stats = {}
    for sid, tasks in by_session.items():
        total = len(tasks)
        success = sum(1 for t in tasks if t.get("success"))
        per_emotion = defaultdict(lambda: {"total": 0, "success": 0})
        for t in tasks:
            em = t["target_emotion"]
            per_emotion[em]["total"] += 1
            if t.get("success"):
                per_emotion[em]["success"] += 1
        stats[sid] = {
            "total_tasks": total,
            "success_rate": round(success / total, 3) if total else 0,
            "per_emotion": dict(per_emotion),
        }
    return stats
```

### 3.2 Дашборд — Metabase на VM

1. Развернуть VM на Cloud.ru (минимум 2 CPU / 4 GB RAM).
2. Установить PostgreSQL — туда ETL-скрипт будет писать агрегированные метрики.
3. Запустить Metabase через Docker:

```bash
docker run -d -p 3000:3000 \
  -e MB_DB_TYPE=postgres \
  -e MB_DB_DBNAME=metabase \
  -e MB_DB_PORT=5432 \
  -e MB_DB_USER=metabase \
  -e MB_DB_PASS=... \
  -e MB_DB_HOST=localhost \
  metabase/metabase
```

4. Создать вопросы в Metabase:
   - % успеха по эмоциям (bar chart)
   - Прогресс по сессиям (line chart)
   - Тепловая карта: эмоция × успех

### 3.3 Автоматическое обновление (n8n cron)

В n8n создать второй workflow:

- **Trigger**: Schedule (каждый день в 03:00)
- **Action**: Execute Command → `./bin/python src/analytics.py`
- **Action**: Write результат в PostgreSQL (нода Postgres)

---

## Этап 4: ML — персонализация (после накопления ≥50 сессий)

### 4.1 Подготовка датасета

Из PostgreSQL/S3 собрать датасет с признаками:

| feature | описание |
|---------|----------|
| `age_group` | возрастная группа (заполняется при регистрации) |
| `emotion` | целевая эмоция (one-hot) |
| `prev_success_rate` | % успехов за прошлые 5 сессий |
| `session_number` | порядковый номер сессии |
| `time_of_day` | утро / день / вечер |

Целевая переменная: `success` (0/1).

### 4.2 Обучение модели

```python
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score
import joblib

model = DecisionTreeClassifier(max_depth=4, random_state=42)
scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")
print(f"ROC-AUC: {scores.mean():.3f} ± {scores.std():.3f}")

model.fit(X, y)
joblib.dump(model, "models/difficulty_predictor.pkl")
```

### 4.3 Интеграция рекомендаций

Inference-сервис (`src/predictor.py`) — REST API на Flask/FastAPI:

```python
@app.post("/predict")
def predict(features: Features):
    prob = model.predict_proba([features.to_array()])[0][1]
    if prob < 0.4:
        return {"recommendation": "упростить", "confidence": prob}
    elif prob > 0.75:
        return {"recommendation": "усложнить", "confidence": prob}
    else:
        return {"recommendation": "оставить", "confidence": prob}
```

`main.py` запрашивает рекомендацию после каждой 5-й задачи и корректирует набор эмоций в `CHALLENGE_EMOTIONS`.

---

## Структура файлов (целевая)

```
comp_vision_env/
├── src/
│   ├── main.py              # существующий — игра (доработать)
│   ├── event_sender.py      # НОВЫЙ — отправка событий в n8n
│   ├── consent.py           # НОВЫЙ — экран согласия родителя
│   ├── analytics.py         # НОВЫЙ — ETL из S3 → PostgreSQL
│   └── predictor.py         # НОВЫЙ (Этап 4) — ML inference API
├── models/
│   ├── blaze_face_short_range.tflite
│   ├── emotion-ferplus.onnx
│   └── difficulty_predictor.pkl  # (Этап 4)
├── docker-compose.yml       # НОВЫЙ — n8n + PostgreSQL + Metabase
├── .env                     # НОВЫЙ — ключи S3 (не в git)
├── .env.example             # НОВЫЙ — шаблон без секретов
├── requirements.txt         # дополнить: boto3, flask, scikit-learn, joblib
└── run.sh
```

---

## Зависимости по этапам

| Пакет | Этап | Назначение |
|-------|------|------------|
| `boto3` | 1, 3 | Работа с S3-совместимым Object Storage |
| `python-dotenv` | 1+ | Загрузка `.env` |
| `flask` или `fastapi` | 4 | ML inference API |
| `scikit-learn` | 4 | Обучение модели |
| `joblib` | 4 | Сериализация модели |
| `psycopg2` | 3 | Запись метрик в PostgreSQL |

Установка для Этапов 1–3:
```bash
./bin/pip install boto3 python-dotenv psycopg2-binary
```

---

## Чеклист готовности к каждому этапу

- **Этап 1 готов**, когда: curl-запрос → файл появляется в S3-бакете.
- **Этап 2 готов**, когда: игра отправляет `emotion_task` события автоматически при каждом успехе.
- **Этап 3 готов**, когда: дашборд Metabase обновляется ежедневно без ручного вмешательства.
- **Этап 4 готов**, когда: приложение автоматически меняет сложность на основе предсказания модели.
