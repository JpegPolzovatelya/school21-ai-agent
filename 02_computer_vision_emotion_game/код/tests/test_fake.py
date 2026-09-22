"""Тесты для src/fake.py — корректность генерации событий."""
import json
import pytest
from unittest.mock import patch

import fake


VALID_EMOTIONS = {"happiness", "surprise", "sadness", "anger", "disgust"}


class TestFakeSession:
    def test_starts_with_session_start(self):
        events = fake.fake_session(1, 1000)
        assert events[0]["event_type"] == "session_start"

    def test_ends_with_session_end(self):
        events = fake.fake_session(1, 1000)
        assert events[-1]["event_type"] == "session_end"

    def test_contains_emotion_tasks(self):
        events = fake.fake_session(1, 1000)
        tasks = [e for e in events if e["event_type"] == "emotion_task"]
        assert len(tasks) >= 1

    def test_task_count_in_range(self):
        for i in range(20):
            events = fake.fake_session(i, i * 1000)
            tasks = [e for e in events if e["event_type"] == "emotion_task"]
            assert 4 <= len(tasks) <= 12

    def test_all_events_have_session_id(self):
        events = fake.fake_session(5, 5000)
        for e in events:
            assert "session_id" in e and e["session_id"]

    def test_all_events_have_timestamp(self):
        events = fake.fake_session(1, 1000)
        for e in events:
            assert "timestamp" in e and isinstance(e["timestamp"], int)

    def test_timestamps_are_non_decreasing(self):
        events = fake.fake_session(1, 1000)
        timestamps = [e["timestamp"] for e in events]
        assert timestamps == sorted(timestamps)

    def test_emotion_task_fields(self):
        events = fake.fake_session(1, 1000)
        for e in [e for e in events if e["event_type"] == "emotion_task"]:
            assert "target_emotion"   in e
            assert "detected_emotion" in e
            assert "confidence"       in e
            assert "success"          in e
            assert isinstance(e["success"], bool)
            assert isinstance(e["confidence"], float)

    def test_target_emotion_is_valid(self):
        events = fake.fake_session(1, 1000)
        for e in [e for e in events if e["event_type"] == "emotion_task"]:
            assert e["target_emotion"] in VALID_EMOTIONS

    def test_success_consistency(self):
        """Если success=True, detected == target."""
        events = fake.fake_session(1, 1000)
        for e in [e for e in events if e["event_type"] == "emotion_task"]:
            if e["success"]:
                assert e["detected_emotion"] == e["target_emotion"]

    def test_session_end_has_score(self):
        events = fake.fake_session(1, 1000)
        end = events[-1]
        assert "score" in end
        assert isinstance(end["score"], int)
        assert end["score"] >= 0

    def test_score_equals_successes(self):
        events = fake.fake_session(1, 1000)
        tasks = [e for e in events if e["event_type"] == "emotion_task"]
        expected_score = sum(1 for t in tasks if t["success"])
        assert events[-1]["score"] == expected_score


class TestFakeMain:
    def test_writes_to_file(self, tmp_path):
        events_file = tmp_path / "events.jsonl"
        with patch.object(fake, "DATA_DIR", tmp_path), \
             patch.object(fake, "EVENTS_FILE", events_file):
            fake.main.__globals__["DATA_DIR"] = tmp_path
            fake.main.__globals__["EVENTS_FILE"] = events_file

            import sys
            with patch("sys.argv", ["fake.py", "--sessions", "3"]):
                fake.main()

        lines = [l for l in events_file.read_text().splitlines() if l.strip()]
        assert len(lines) > 0
        for line in lines:
            json.loads(line)  # все строки — валидный JSON

    def test_clear_flag_removes_old_data(self, tmp_path):
        events_file = tmp_path / "events.jsonl"
        events_file.write_text('{"old": true}\n', encoding="utf-8")

        with patch.object(fake, "DATA_DIR", tmp_path), \
             patch.object(fake, "EVENTS_FILE", events_file):
            import sys
            with patch("sys.argv", ["fake.py", "--sessions", "2", "--clear"]):
                fake.main()

        lines = [l for l in events_file.read_text().splitlines() if l.strip()]
        parsed = [json.loads(l) for l in lines]
        assert not any(p.get("old") for p in parsed)
