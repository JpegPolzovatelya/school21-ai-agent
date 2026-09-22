# Покажи эмоцию!

Интерактивная игра на базе компьютерного зрения: программа просит вас изобразить случайную эмоцию и засчитывает очко, если вы удержали её достаточно долго.

## Как это работает

1. Камера захватывает видео в реальном времени.
2. **MediaPipe** находит лицо на кадре.
3. **ONNX-модель** (FER+) определяет эмоцию из 5 возможных: `happiness`, `surprise`, `sadness`, `anger`, `disgust`.
4. При запуске появляется **экран настройки**: выберите время на каждую эмоцию (по умолчанию 30 с, изменяется клавишами `+` / `-`, подтверждается Enter).
5. Каждая сессия выбирает **3 случайные эмоции** из набора.
6. Перед каждой эмоцией показывается 10-секундный отсчёт с крупными подсказками.
7. Удерживайте нужную эмоцию ~1 секунду — прогресс-бар и таймер заполняются.
8. После успеха появляется **Отлично!** и начинается следующее задание с новым отсчётом.
9. Если время истекло — показывается **Время вышло!** и переключается следующая эмоция.
10. После всех 3 эмоций сессия завершается экраном с итоговым счётом.
11. Каждое событие (успех или таймаут) записывается в `data/events.jsonl` для аналитики.

## Требования

- macOS (тестировалось на Apple M4)
- Python 3.12
- Встроенная или внешняя веб-камера

## Установка

```bash
# 1. Клонируйте репозиторий
git clone <url>
cd comp_vision_env

# 2. Создайте виртуальное окружение
python3.12 -m venv .
pip install -r requirements.txt

# 3. Скачайте модель детектора лиц
curl -L -o models/blaze_face_short_range.tflite \
  https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite

# 4. Положите emotion-ferplus.onnx в папку models/
#    (файл нужно скачать отдельно, ~33 МБ)

# 5. (Опционально) Настройте отправку в Telegram
cp .env.example .env
# Заполните TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID
```

## Запуск

```bash
./run.sh
```

Или напрямую:

```bash
./bin/python src/main.py
```

Нажмите **Q**, чтобы выйти.

## Аналитика

```bash
# Сформировать отчёт и отправить в Telegram
./bin/python src/analytics.py

# Сгенерировать тестовые данные
./bin/python src/fake.py --sessions 10 --clear
```

## Тесты

```bash
./bin/python -m pytest tests/ -v
```

58 тестов по 5 модулям: `analytics`, `event_sender`, `fake`, `strings`, `text_render`.

## Структура проекта

```
comp_vision_env/
├── src/
│   ├── main.py          # игровой цикл (камера + детекция лица + UI)
│   ├── strings.py       # локализация: названия эмоций, подсказки, UI
│   ├── text_render.py   # рендеринг кириллицы через PIL (FrameCanvas)
│   ├── event_sender.py  # потокобезопасная запись событий в events.jsonl
│   ├── analytics.py     # формирование ASCII-отчёта, отправка в Telegram
│   └── fake.py          # генератор тестовых событий
├── tests/               # тесты pytest (58 штук)
├── models/
│   ├── blaze_face_short_range.tflite  # детектор лиц (MediaPipe)
│   └── emotion-ferplus.onnx           # классификатор эмоций (FER+)
├── data/
│   └── events.jsonl     # лог событий сессий (в .gitignore)
├── reports/             # сгенерированные отчёты (в .gitignore)
├── .env.example         # шаблон настроек Telegram
├── requirements.txt
└── run.sh
```

## Зависимости

| Пакет | Версия |
|---|---|
| opencv-contrib-python | 4.11.0 |
| mediapipe | 0.10.32 |
| numpy | 1.26.4 |
| Pillow | — |

## Управление

| Клавиша | Действие |
|---|---|
| Q | Выход |
