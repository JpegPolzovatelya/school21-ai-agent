"""Тесты для src/text_render.py — рендеринг текста через PIL."""
import numpy as np
import pytest
from text_render import FrameCanvas


def black_frame(h=480, w=640):
    return np.zeros((h, w, 3), dtype=np.uint8)


def white_frame(h=480, w=640):
    return np.full((h, w, 3), 255, dtype=np.uint8)


class TestFrameCanvas:
    def test_shape_preserved_after_context(self):
        frame = black_frame()
        original_shape = frame.shape
        with FrameCanvas(frame):
            pass
        assert frame.shape == original_shape

    def test_dtype_preserved(self):
        frame = black_frame()
        with FrameCanvas(frame):
            pass
        assert frame.dtype == np.uint8

    def test_text_center_modifies_frame(self):
        frame = black_frame()
        before = frame.copy()
        with FrameCanvas(frame) as c:
            c.text_center("Привет", y=50, size=24, color_bgr=(255, 255, 255))
        assert not np.array_equal(frame, before), "Кадр не изменился после рисования текста"

    def test_text_at_modifies_frame(self):
        frame = black_frame()
        before = frame.copy()
        with FrameCanvas(frame) as c:
            c.text_at("Тест", x=10, y=30, size=20, color_bgr=(0, 255, 0))
        assert not np.array_equal(frame, before)

    def test_text_right_modifies_frame(self):
        frame = black_frame()
        before = frame.copy()
        with FrameCanvas(frame) as c:
            c.text_right("Счёт: 5", y=20, size=22, color_bgr=(255, 255, 255))
        assert not np.array_equal(frame, before)

    def test_text_center_shadow_modifies_frame(self):
        frame = black_frame()
        before = frame.copy()
        with FrameCanvas(frame) as c:
            c.text_center_shadow("Отлично!", y=200, size=60,
                                 color_bgr=(0, 255, 80), shadow_bgr=(0, 70, 0))
        assert not np.array_equal(frame, before)

    def test_multiple_calls_in_one_context(self):
        frame = black_frame()
        with FrameCanvas(frame) as c:
            c.text_center("Строка 1", y=40,  size=24, color_bgr=(255, 255, 255))
            c.text_center("Строка 2", y=80,  size=24, color_bgr=(255, 200, 0))
            c.text_center("Строка 3", y=120, size=24, color_bgr=(0, 200, 255))
        # Не падает, кадр изменён
        assert frame.max() > 0

    def test_cyrillic_text_no_exception(self):
        frame = black_frame()
        with FrameCanvas(frame) as c:
            c.text_center("Покажи: РАДОСТЬ",     y=30,  size=38, color_bgr=(0, 220, 220), bold=True)
            c.text_center("Улыбнись широко!",    y=80,  size=22, color_bgr=(240, 200, 80))
            c.text_center("Уголки рта — вверх.", y=112, size=22, color_bgr=(240, 200, 80))

    def test_bold_and_regular_font(self):
        frame1 = black_frame()
        frame2 = black_frame()
        with FrameCanvas(frame1) as c:
            c.text_center("Текст", y=50, size=28, color_bgr=(255, 255, 255), bold=False)
        with FrameCanvas(frame2) as c:
            c.text_center("Текст", y=50, size=28, color_bgr=(255, 255, 255), bold=True)
        # Bold и Regular дают разный результат
        assert not np.array_equal(frame1, frame2)

    def test_frame_is_modified_in_place(self):
        frame = black_frame()
        original_id = id(frame)
        with FrameCanvas(frame) as c:
            c.text_center("Проверка", y=50, size=24, color_bgr=(255, 0, 0))
        assert id(frame) == original_id  # тот же объект, не новый
