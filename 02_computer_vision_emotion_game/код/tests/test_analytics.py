"""Тесты для src/analytics.py — загрузка данных, отчёт, .env, Telegram."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import analytics


# ── Фикстуры ──────────────────────────────────────────────────────────────────

def make_events(sessions=2, tasks_per_session=5, success_rate=0.6):
    events = []
    for s in range(sessions):
        sid = f"session_{s}"
        events.append({"session_id": sid, "event_type": "session_start", "timestamp": s * 1000})
        for t in range(tasks_per_session):
            em = ["happiness", "surprise", "sadness", "anger", "disgust"][t % 5]
            success = t / tasks_per_session < success_rate
            events.append({
                "session_id":       sid,
                "event_type":       "emotion_task",
                "target_emotion":   em,
                "detected_emotion": em if success else "neutral",
                "confidence":       0.8 if success else 0.4,
                "success":          success,
                "timestamp":        s * 1000 + t * 10,
            })
        events.append({"session_id": sid, "event_type": "session_end",
                        "score": 3, "timestamp": s * 1000 + 999})
    return events


def write_jsonl(path: Path, events: list) -> None:
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")


# ── load_events ────────────────────────────────────────────────────────────────

class TestLoadEvents:
    def test_returns_empty_for_missing_file(self, tmp_path):
        with patch.object(analytics, "DATA_FILE", tmp_path / "missing.jsonl"):
            assert analytics.load_events() == []

    def test_returns_empty_for_empty_file(self, tmp_path):
        f = tmp_path / "events.jsonl"
        f.write_text("", encoding="utf-8")
        with patch.object(analytics, "DATA_FILE", f):
            assert analytics.load_events() == []

    def test_parses_valid_events(self, tmp_path):
        f = tmp_path / "events.jsonl"
        events = make_events(sessions=1, tasks_per_session=3)
        write_jsonl(f, events)
        with patch.object(analytics, "DATA_FILE", f):
            loaded = analytics.load_events()
        assert len(loaded) == len(events)

    def test_skips_invalid_json_lines(self, tmp_path, capsys):
        f = tmp_path / "events.jsonl"
        f.write_text(
            '{"event_type": "session_start"}\n'
            'NOT_JSON{{{\n'
            '{"event_type": "session_end"}\n',
            encoding="utf-8",
        )
        with patch.object(analytics, "DATA_FILE", f):
            loaded = analytics.load_events()
        assert len(loaded) == 2
        assert "предупреждение" in capsys.readouterr().out

    def test_skips_blank_lines(self, tmp_path):
        f = tmp_path / "events.jsonl"
        f.write_text('{"n": 1}\n\n{"n": 2}\n\n', encoding="utf-8")
        with patch.object(analytics, "DATA_FILE", f):
            loaded = analytics.load_events()
        assert len(loaded) == 2


# ── build_report ───────────────────────────────────────────────────────────────

class TestBuildReport:
    def test_no_crash_on_empty(self):
        report = analytics.build_report([])
        assert isinstance(report, str)

    def test_contains_session_count(self):
        events = make_events(sessions=3)
        report = analytics.build_report(events)
        assert "3" in report

    def test_success_rate_calculation(self):
        # 10 заданий, все успешные → 100%
        events = [
            {"event_type": "emotion_task", "session_id": "s1",
             "target_emotion": "happiness", "success": True}
        ] * 10
        report = analytics.build_report(events)
        assert "100" in report

    def test_partial_success_rate(self):
        # 4 из 10 успешных → 40%
        events = (
            [{"event_type": "emotion_task", "session_id": "s1",
              "target_emotion": "happiness", "success": True}] * 4 +
            [{"event_type": "emotion_task", "session_id": "s1",
              "target_emotion": "happiness", "success": False}] * 6
        )
        report = analytics.build_report(events)
        assert "40" in report

    def test_contains_russian_emotion_names(self):
        events = [{"event_type": "emotion_task", "session_id": "s1",
                   "target_emotion": "happiness", "success": True}]
        report = analytics.build_report(events)
        assert "Радость" in report

    def test_ignores_non_task_events(self):
        events = [
            {"event_type": "session_start", "session_id": "s1"},
            {"event_type": "session_end",   "session_id": "s1", "score": 0},
        ]
        report = analytics.build_report(events)
        assert "0" in report  # 0 заданий, не падает


# ── load_env ──────────────────────────────────────────────────────────────────

class TestLoadEnv:
    def test_returns_empty_for_missing_file(self, tmp_path):
        with patch.object(analytics, "ENV_FILE", tmp_path / ".env"):
            assert analytics.load_env() == {}

    def test_parses_key_value(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("FOO=bar\nBAZ=qux\n", encoding="utf-8")
        with patch.object(analytics, "ENV_FILE", f):
            env = analytics.load_env()
        assert env == {"FOO": "bar", "BAZ": "qux"}

    def test_ignores_comments_and_blank_lines(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("# comment\n\nKEY=value\n", encoding="utf-8")
        with patch.object(analytics, "ENV_FILE", f):
            env = analytics.load_env()
        assert env == {"KEY": "value"}

    def test_value_with_equals_sign(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("TOKEN=abc=def=ghi\n", encoding="utf-8")
        with patch.object(analytics, "ENV_FILE", f):
            env = analytics.load_env()
        assert env["TOKEN"] == "abc=def=ghi"


# ── send_telegram ─────────────────────────────────────────────────────────────

class TestSendTelegram:
    def test_calls_telegram_api(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"ok": true}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            analytics.send_telegram("TOKEN", "CHAT", "report text")

        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        body = json.loads(req.data)
        assert body["chat_id"] == "CHAT"
        assert "report text" in body["text"]

    def test_handles_network_error(self, capsys):
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
            analytics.send_telegram("TOKEN", "CHAT", "report")
        assert "Telegram" in capsys.readouterr().out
