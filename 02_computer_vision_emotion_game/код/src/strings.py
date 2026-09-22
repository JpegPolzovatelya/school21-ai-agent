import json
from pathlib import Path

_data = json.loads((Path(__file__).parent / "strings.json").read_text(encoding="utf-8"))

EMOTION_NAMES: dict[str, str]        = _data["emotion_names"]
EMOTION_HINTS: dict[str, list[str]]  = _data["emotion_hints"]
UI:            dict[str, str]        = _data["ui"]
