import json
import threading
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
EVENTS_FILE = DATA_DIR / "events.jsonl"

_lock = threading.Lock()


def send_event(payload: dict) -> None:
    """Записывает событие в data/events.jsonl (одна JSON-строка на событие)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _lock:
        with EVENTS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
