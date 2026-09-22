"""
Генерация фейкового лога для тестирования аналитики.
Запуск: ./bin/python src/fake.py
        ./bin/python src/fake.py --sessions 10 --clear
"""
import json
import random
import time
import argparse
from pathlib import Path

DATA_DIR   = Path(__file__).parent.parent / "data"
EVENTS_FILE = DATA_DIR / "events.jsonl"

EMOTIONS = ["happiness", "surprise", "sadness", "anger", "disgust"]

# Вероятность успеха по эмоциям (имитирует реальный прогресс ребёнка)
SUCCESS_RATE = {
    "happiness": 0.80,
    "surprise":  0.60,
    "sadness":   0.55,
    "anger":     0.65,
    "disgust":   0.45,
}


def fake_session(session_num: int, base_time: int) -> list[dict]:
    session_id = f"fake_{session_num:03d}_{base_time}"
    events: list[dict] = []
    t = base_time

    events.append({
        "session_id": session_id,
        "event_type": "session_start",
        "timestamp":  t,
    })

    num_tasks = random.randint(4, 12)
    score = 0

    for _ in range(num_tasks):
        t += random.randint(5, 30)
        target   = random.choice(EMOTIONS)
        success  = random.random() < SUCCESS_RATE[target]
        detected = target if success else random.choice(EMOTIONS)
        conf     = round(random.uniform(0.56, 0.95) if success else random.uniform(0.30, 0.70), 3)

        events.append({
            "session_id":      session_id,
            "event_type":      "emotion_task",
            "target_emotion":  target,
            "detected_emotion": detected,
            "confidence":      conf,
            "success":         success,
            "timestamp":       t,
        })

        if success:
            score += 1

    t += random.randint(2, 10)
    events.append({
        "session_id": session_id,
        "event_type": "session_end",
        "score":      score,
        "timestamp":  t,
    })

    return events


def main() -> None:
    parser = argparse.ArgumentParser(description="Генератор фейкового лога MirMe")
    parser.add_argument("--sessions", type=int, default=5,
                        help="Количество сессий (по умолчанию: 5)")
    parser.add_argument("--clear", action="store_true",
                        help="Очистить существующий лог перед записью")
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)

    if args.clear and EVENTS_FILE.exists():
        EVENTS_FILE.unlink()
        print(f"  Лог очищен: {EVENTS_FILE.name}")

    # Генерируем сессии в прошлом (по одной в день)
    now = int(time.time())
    all_events: list[dict] = []
    for i in range(args.sessions):
        base_time = now - (args.sessions - i) * 86400 + random.randint(0, 3600)
        all_events.extend(fake_session(i + 1, base_time))

    with EVENTS_FILE.open("a", encoding="utf-8") as f:
        for event in all_events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    tasks = sum(1 for e in all_events if e["event_type"] == "emotion_task")
    print(f"  Записано {args.sessions} сессий, {tasks} заданий → {EVENTS_FILE}")


if __name__ == "__main__":
    main()
