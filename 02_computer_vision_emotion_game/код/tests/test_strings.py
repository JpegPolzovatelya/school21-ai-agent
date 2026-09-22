"""Тесты для src/strings.py — полнота локализации."""
import pytest
from strings import EMOTION_NAMES, EMOTION_HINTS, UI

GAME_EMOTIONS = ["happiness", "surprise", "sadness", "anger", "disgust"]
REQUIRED_UI_KEYS = [
    "challenge_prefix", "score_label", "feedback_success",
    "hint_quit", "hint_label", "camera_error", "frame_error",
    "exit_msg", "start_msg",
]


class TestEmotionNames:
    def test_all_game_emotions_have_russian_name(self):
        for em in GAME_EMOTIONS:
            assert em in EMOTION_NAMES, f"Нет русского названия для '{em}'"

    def test_names_are_non_empty_strings(self):
        for key, name in EMOTION_NAMES.items():
            assert isinstance(name, str) and name.strip(), \
                f"Пустое название для '{key}'"

    def test_fear_has_name(self):
        # fear есть в модели, должен оставаться в словаре
        assert "fear" in EMOTION_NAMES

    def test_no_english_in_names(self):
        # Русские названия не должны содержать латинских букв
        import re
        for key, name in EMOTION_NAMES.items():
            assert not re.search(r"[a-zA-Z]", name), \
                f"Название '{name}' для '{key}' содержит латиницу"


class TestEmotionHints:
    def test_all_game_emotions_have_hints(self):
        for em in GAME_EMOTIONS:
            assert em in EMOTION_HINTS, f"Нет подсказки для '{em}'"

    def test_hints_are_list_of_strings(self):
        for key, hints in EMOTION_HINTS.items():
            assert isinstance(hints, list), f"Подсказки для '{key}' не список"
            for line in hints:
                assert isinstance(line, str) and line.strip(), \
                    f"Пустая строка в подсказках для '{key}'"

    def test_hints_have_at_least_one_line(self):
        for key, hints in EMOTION_HINTS.items():
            assert len(hints) >= 1, f"Пустой список подсказок для '{key}'"

    def test_hints_max_two_lines(self):
        # Больше двух строк не поместятся на экране
        for key, hints in EMOTION_HINTS.items():
            assert len(hints) <= 2, \
                f"Слишком много строк подсказки для '{key}': {len(hints)}"


class TestUI:
    def test_all_required_keys_present(self):
        for key in REQUIRED_UI_KEYS:
            assert key in UI, f"Отсутствует ключ UI: '{key}'"

    def test_values_are_non_empty_strings(self):
        for key, val in UI.items():
            assert isinstance(val, str) and val.strip(), \
                f"Пустое значение UI для '{key}'"
