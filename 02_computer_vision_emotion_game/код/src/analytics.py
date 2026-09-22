"""
Запуск: ./bin/python src/analytics.py
Читает data/events.jsonl, выводит отчёт в консоль,
сохраняет в reports/ и отправляет в Telegram.
"""
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT_DIR    = Path(__file__).parent.parent
DATA_FILE   = ROOT_DIR / "data" / "events.jsonl"
REPORTS_DIR = ROOT_DIR / "reports"
ENV_FILE    = ROOT_DIR / ".env"

EMOTION_ORDER = ["happiness", "surprise", "sadness", "anger", "disgust"]
EMOTION_NAMES_RU = {
    "happiness": "Радость",
    "surprise":  "Удивление",
    "sadness":   "Грусть",
    "anger":     "Злость",
    "disgust":   "Отвращение",
}


# ── .env ──────────────────────────────────────────────────────────────────────

def load_env() -> dict[str, str]:
    """Читает .env из корня проекта, возвращает dict ключ→значение."""
    env: dict[str, str] = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


# ── Telegram ───────────────────────────────────────────────────────────────────

def send_telegram(token: str, chat_id: str, text: str) -> None:
    """Отправляет сообщение через Telegram Bot API (без сторонних библиотек)."""
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps({
        "chat_id":    chat_id,
        "text":       f"```\n{text}\n```",
        "parse_mode": "MarkdownV2",
    }).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print("  Отчёт отправлен в Telegram.")
            else:
                print(f"  Telegram вернул ошибку: {result.get('description')}")
    except urllib.error.URLError as e:
        print(f"  Не удалось отправить в Telegram: {e}")


# ── Данные ────────────────────────────────────────────────────────────────────

def load_events() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    events = []
    with DATA_FILE.open(encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  [предупреждение] строка {i} пропущена: {e}")
    return events


def _sessions_progress(events: list[dict], n: int = 5) -> list[str]:
    """Возвращает строки прогресса по последним n сессиям (✓/✗ на эмоцию)."""
    tasks_by_session: dict[str, list[dict]] = defaultdict(list)
    start_by_session: dict[str, int] = {}

    for e in events:
        etype = e.get("event_type")
        if etype == "emotion_task":
            tasks_by_session[e["session_id"]].append(e)
        elif etype == "session_start":
            start_by_session[e["session_id"]] = e.get("timestamp", 0)

    # берём последние n сессий по времени старта
    session_ids = sorted(start_by_session, key=lambda s: start_by_session[s])[-n:]

    lines = []
    for sid in session_ids:
        tasks = sorted(tasks_by_session.get(sid, []), key=lambda t: t.get("timestamp", 0))
        if not tasks:
            continue
        ts = start_by_session.get(sid, 0)
        dt = datetime.fromtimestamp(ts).strftime("%d.%m %H:%M") if ts else "???"
        ok = sum(1 for t in tasks if t.get("success"))
        parts = []
        for t in tasks:
            name = EMOTION_NAMES_RU.get(t.get("target_emotion", ""), "?")
            mark = "✓" if t.get("success") else "✗"
            parts.append(f"{mark} {name}")
        lines.append(f"  {dt}  {'  '.join(parts)}  →  {ok}/{len(tasks)}")

    return lines


def build_report(events: list[dict]) -> str:
    tasks    = [e for e in events if e.get("event_type") == "emotion_task"]
    sessions = {e["session_id"] for e in events
                if e.get("event_type") in ("session_start", "emotion_task")}

    total         = len(tasks)
    success_total = sum(1 for t in tasks if t.get("success"))

    per_emotion: dict[str, dict] = defaultdict(lambda: {"total": 0, "success": 0})
    for t in tasks:
        em = t.get("target_emotion", "unknown")
        per_emotion[em]["total"] += 1
        if t.get("success"):
            per_emotion[em]["success"] += 1

    W   = 46
    sep = "=" * W
    lines = [
        sep,
        "Отчёт по сессиям MirMe".center(W),
        f"Дата: {datetime.now().strftime('%d.%m.%Y  %H:%M')}".center(W),
        sep,
        "",
        f"  Всего сессий:  {len(sessions)}",
        f"  Всего заданий: {total}",
    ]

    if total > 0:
        pct = round(success_total / total * 100)
        lines.append(f"  Общий успех:   {pct}%  ({success_total}/{total})")

    lines += ["", "  По эмоциям:", ""]

    for em_key in EMOTION_ORDER:
        d = per_emotion.get(em_key)
        if not d or d["total"] == 0:
            continue
        pct    = round(d["success"] / d["total"] * 100)
        filled = pct // 10
        bar    = "█" * filled + "░" * (10 - filled)
        name   = EMOTION_NAMES_RU.get(em_key, em_key).ljust(11)
        lines.append(f"  {name}  {bar}  {pct:3d}%  ({d['success']}/{d['total']})")

    progress = _sessions_progress(events)
    if progress:
        lines += ["", "  Прогресс (последние сессии):", ""]
        lines += progress

    lines += ["", sep]
    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    events = load_events()
    if not events:
        print("Нет данных: файл data/events.jsonl пуст или не существует.")
        print("Запустите игру хотя бы один раз.")
        return

    report = build_report(events)
    print(report)

    # Сохранить в файл
    REPORTS_DIR.mkdir(exist_ok=True)
    filename = REPORTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filename.write_text(report, encoding="utf-8")
    print(f"\n  Отчёт сохранён: {filename.relative_to(ROOT_DIR)}")

    # Отправить в Telegram
    env = load_env()
    token   = env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = env.get("TELEGRAM_CHAT_ID", "")
    if token and chat_id and "your_" not in token:
        send_telegram(token, chat_id, report)
    else:
        print("  Telegram не настроен — заполните .env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).")


if __name__ == "__main__":
    main()
