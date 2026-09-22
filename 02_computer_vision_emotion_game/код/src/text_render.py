"""
Рендеринг текста с поддержкой кириллицы через Pillow.
Все цвета принимаются в формате BGR (как в OpenCV).
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
_FONT_BOLD    = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

_cache: dict = {}


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, bold)
    if key not in _cache:
        path = _FONT_BOLD if bold else _FONT_REGULAR
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def _bgr_to_rgb(color: tuple) -> tuple:
    return (color[2], color[1], color[0])


class FrameCanvas:
    """Контекстный менеджер: одна конвертация BGR→PIL при входе, PIL→BGR при выходе."""

    def __init__(self, frame: np.ndarray):
        self._frame = frame
        self.pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        self.draw = ImageDraw.Draw(self.pil)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self._frame[:] = cv2.cvtColor(np.array(self.pil), cv2.COLOR_RGB2BGR)

    # ------------------------------------------------------------------ helpers

    def text_center(self, text: str, y: int, size: int, color_bgr: tuple,
                    bold: bool = False) -> None:
        font = _font(size, bold)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (self.pil.width - tw) // 2
        self.draw.text((x, y), text, font=font, fill=_bgr_to_rgb(color_bgr))

    def text_at(self, text: str, x: int, y: int, size: int, color_bgr: tuple,
                bold: bool = False) -> None:
        font = _font(size, bold)
        self.draw.text((x, y), text, font=font, fill=_bgr_to_rgb(color_bgr))

    def text_right(self, text: str, y: int, size: int, color_bgr: tuple,
                   margin: int = 15, bold: bool = False) -> None:
        font = _font(size, bold)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = self.pil.width - tw - margin
        self.draw.text((x, y), text, font=font, fill=_bgr_to_rgb(color_bgr))

    def text_shadow(self, text: str, x: int, y: int, size: int,
                    color_bgr: tuple, shadow_bgr: tuple,
                    bold: bool = True, offset: int = 3) -> None:
        font = _font(size, bold)
        self.draw.text((x + offset, y + offset), text, font=font,
                       fill=_bgr_to_rgb(shadow_bgr))
        self.draw.text((x, y), text, font=font, fill=_bgr_to_rgb(color_bgr))

    def text_center_shadow(self, text: str, y: int, size: int,
                           color_bgr: tuple, shadow_bgr: tuple,
                           bold: bool = True, offset: int = 3) -> None:
        font = _font(size, bold)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (self.pil.width - tw) // 2
        self.draw.text((x + offset, y + offset), text, font=font,
                       fill=_bgr_to_rgb(shadow_bgr))
        self.draw.text((x, y), text, font=font, fill=_bgr_to_rgb(color_bgr))
