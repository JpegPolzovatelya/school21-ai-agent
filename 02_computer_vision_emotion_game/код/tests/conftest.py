import sys
from pathlib import Path

# Добавляем src/ в путь, чтобы тесты могли импортировать модули
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
