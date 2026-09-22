"""Тесты для src/event_sender.py — запись событий в JSONL."""
import json
import threading
import time
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def tmp_events_file(tmp_path):
    """Перенаправляем запись в временный файл, не трогая data/events.jsonl."""
    with patch("event_sender.DATA_DIR", tmp_path), \
         patch("event_sender.EVENTS_FILE", tmp_path / "events.jsonl"):
        yield tmp_path / "events.jsonl"


from event_sender import send_event


class TestSendEvent:
    def test_creates_file_on_first_call(self, tmp_events_file):
        send_event({"event_type": "test"})
        assert tmp_events_file.exists()

    def test_event_written_as_valid_json(self, tmp_events_file):
        payload = {"session_id": "s1", "event_type": "session_start", "timestamp": 1000}
        send_event(payload)
        line = tmp_events_file.read_text(encoding="utf-8").strip()
        parsed = json.loads(line)
        assert parsed == payload

    def test_each_event_on_separate_line(self, tmp_events_file):
        send_event({"n": 1})
        send_event({"n": 2})
        send_event({"n": 3})
        lines = [l for l in tmp_events_file.read_text().splitlines() if l.strip()]
        assert len(lines) == 3

    def test_events_append_not_overwrite(self, tmp_events_file):
        send_event({"n": 1})
        send_event({"n": 2})
        events = [json.loads(l) for l in tmp_events_file.read_text().splitlines() if l]
        assert events[0]["n"] == 1
        assert events[1]["n"] == 2

    def test_unicode_preserved(self, tmp_events_file):
        send_event({"emotion": "радость", "hint": "Улыбнись широко!"})
        parsed = json.loads(tmp_events_file.read_text(encoding="utf-8").strip())
        assert parsed["emotion"] == "радость"
        assert parsed["hint"] == "Улыбнись широко!"

    def test_thread_safety(self, tmp_events_file):
        threads = [threading.Thread(target=send_event, args=({"i": i},))
                   for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        lines = [l for l in tmp_events_file.read_text().splitlines() if l.strip()]
        assert len(lines) == 20
        for line in lines:
            json.loads(line)  # каждая строка — валидный JSON

    def test_creates_data_dir_if_missing(self, tmp_path):
        nested = tmp_path / "deep" / "dir"
        events_file = nested / "events.jsonl"
        with patch("event_sender.DATA_DIR", nested), \
             patch("event_sender.EVENTS_FILE", events_file):
            send_event({"event_type": "test"})
        assert events_file.exists()
