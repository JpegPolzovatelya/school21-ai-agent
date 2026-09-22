# Show Your Emotion!

An interactive computer vision game: the app challenges you to display a random facial emotion and awards a point when you hold it long enough.

## How It Works

1. The camera captures live video.
2. **MediaPipe** detects your face in each frame.
3. An **ONNX model** (FER+) classifies the emotion from 5 options: `happiness`, `surprise`, `sadness`, `anger`, `disgust`.
4. At startup a **setup screen** lets you choose the time limit per emotion (default 30 s, adjustable with `+` / `-`, confirmed with Enter).
5. Each session picks **3 random emotions** to challenge you with.
6. Before each emotion a 10-second countdown is shown with large hint text.
7. Hold the requested emotion for ~1 second — the progress bar and a live timer fill up.
8. On success, **Отлично!** flashes on screen and the next challenge begins with a new countdown.
9. If the time limit expires without a match, **Время вышло!** is shown and the next emotion starts.
10. After all 3 emotions the session ends with a final score screen.
11. Every session event (success or timeout) is logged to `data/events.jsonl` for analytics.

## Requirements

- macOS (tested on Apple M4)
- Python 3.12
- Built-in or external webcam

## Installation

```bash
# 1. Clone the repository
git clone <url>
cd comp_vision_env

# 2. Create virtual environment
python3.12 -m venv .
pip install -r requirements.txt

# 3. Download the face detector model
curl -L -o models/blaze_face_short_range.tflite \
  https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite

# 4. Place emotion-ferplus.onnx inside the models/ folder
#    (download separately, ~33 MB)

# 5. (Optional) Configure Telegram reporting
cp .env.example .env
# Fill in TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
```

## Running

```bash
./run.sh
```

Or directly:

```bash
./bin/python src/main.py
```

Press **Q** to quit.

## Analytics

```bash
# Generate a report and send it to Telegram
./bin/python src/analytics.py

# Generate fake event data for testing
./bin/python src/fake.py --sessions 10 --clear
```

## Tests

```bash
./bin/python -m pytest tests/ -v
```

58 tests across 5 modules: `analytics`, `event_sender`, `fake`, `strings`, `text_render`.

## Project Structure

```
comp_vision_env/
├── src/
│   ├── main.py          # game loop (camera + face detection + UI)
│   ├── strings.py       # localisation: emotion names, hints, UI strings
│   ├── text_render.py   # PIL-based Cyrillic text rendering (FrameCanvas)
│   ├── event_sender.py  # thread-safe event logging to data/events.jsonl
│   ├── analytics.py     # build ASCII report, send to Telegram
│   └── fake.py          # fake event generator for analytics development
├── tests/               # pytest suite (58 tests)
├── models/
│   ├── blaze_face_short_range.tflite  # face detector (MediaPipe)
│   └── emotion-ferplus.onnx           # emotion classifier (FER+)
├── data/
│   └── events.jsonl     # session event log (git-ignored)
├── reports/             # generated analytics reports (git-ignored)
├── .env.example         # Telegram credentials template
├── requirements.txt
└── run.sh
```

## Dependencies

| Package | Version |
|---|---|
| opencv-contrib-python | 4.11.0 |
| mediapipe | 0.10.32 |
| numpy | 1.26.4 |
| Pillow | — |

## Controls

| Key | Action |
|---|---|
| Q | Quit |

---

[Русская версия](README.ru.md)
