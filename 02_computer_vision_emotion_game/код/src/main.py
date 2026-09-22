import cv2
import mediapipe as mp
import numpy as np
import random
import time
from pathlib import Path
from event_sender import send_event
from strings import EMOTION_NAMES, EMOTION_HINTS, UI
from text_render import FrameCanvas

ROOT_DIR = Path(__file__).parent.parent
FACE_MODEL = ROOT_DIR / "models" / "blaze_face_short_range.tflite"
EMOTION_MODEL = ROOT_DIR / "models" / "emotion-ferplus.onnx"

for path in (FACE_MODEL, EMOTION_MODEL):
    if not path.exists():
        raise FileNotFoundError(f"Модель не найдена: {path}")

EMOTIONS = ["neutral", "happiness", "surprise", "sadness",
            "anger", "disgust", "fear", "contempt"]

EMOTION_COLOR = {
    "happiness":  (0, 220, 0),
    "neutral":    (200, 200, 200),
    "surprise":   (0, 200, 255),
    "sadness":    (255, 100, 50),
    "anger":      (0, 0, 255),
    "disgust":    (0, 128, 128),
    "fear":       (128, 0, 255),
    "contempt":   (100, 100, 200),
}

WINDOW_NAME = "MirMe"

# --- Game constants ---
CHALLENGE_EMOTIONS    = ["happiness", "surprise", "sadness", "anger", "disgust"]
EMOTIONS_PER_SESSION  = 3
COUNTDOWN_DURATION    = 10    # seconds
MATCH_FRAMES_REQUIRED = 20    # ~1 sec at 20 fps
FEEDBACK_FRAMES       = 40    # frames for "Отлично!"
TIMEOUT_FRAMES        = 60    # frames for "Время вышло!"
SESSION_END_FRAMES    = 120   # frames for session end screen
EMOTION_TIME_DEFAULT  = 30    # seconds, default time limit per emotion
EMOTION_TIME_MIN      = 10
EMOTION_TIME_MAX      = 120
EMOTION_TIME_STEP     = 5

# --- Face detector (MediaPipe 0.10+) ---
BaseOptions = mp.tasks.BaseOptions
FaceDetector = mp.tasks.vision.FaceDetector
FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
VisionRunningMode = mp.tasks.vision.RunningMode

face_options = FaceDetectorOptions(
    base_options=BaseOptions(model_asset_path=str(FACE_MODEL)),
    running_mode=VisionRunningMode.IMAGE,
    min_detection_confidence=0.5,
)
detector = FaceDetector.create_from_options(face_options)

# --- Emotion classifier (ONNX via OpenCV DNN) ---
emotion_net = cv2.dnn.readNetFromONNX(str(EMOTION_MODEL))


def classify_emotion(bgr_frame: np.ndarray, fx: int, fy: int, fw: int, fh: int):
    """Возвращает (emotion_label, confidence) для области лица."""
    pad = int(max(fw, fh) * 0.1)
    ih, iw = bgr_frame.shape[:2]
    x1 = max(0, fx - pad)
    y1 = max(0, fy - pad)
    x2 = min(iw, fx + fw + pad)
    y2 = min(ih, fy + fh + pad)

    face_roi = bgr_frame[y1:y2, x1:x2]
    if face_roi.size == 0:
        return "neutral", 0.0

    gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
    blob = cv2.dnn.blobFromImage(gray, scalefactor=1.0, size=(64, 64),
                                 mean=(0,), swapRB=False)
    emotion_net.setInput(blob)
    scores = emotion_net.forward()[0]

    exp_scores = np.exp(scores - scores.max())
    probs = exp_scores / exp_scores.sum()

    idx = int(np.argmax(probs))
    return EMOTIONS[idx], float(probs[idx])


def draw_setup(frame: np.ndarray, time_limit: int) -> None:
    """Экран настройки: выбор времени на эмоцию перед сессией."""
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    with FrameCanvas(frame) as c:
        c.text_center("Настройка сессии",
                      y=h // 2 - 140, size=38, color_bgr=(200, 200, 200), bold=True)
        c.text_center("Время на каждую эмоцию:",
                      y=h // 2 - 80, size=26, color_bgr=(180, 180, 180))
        c.text_center_shadow(f"{time_limit} сек",
                             y=h // 2 - 40, size=80,
                             color_bgr=(0, 220, 220), shadow_bgr=(0, 60, 60))
        c.text_center("+ / −   изменить",
                      y=h // 2 + 58, size=24, color_bgr=(160, 160, 160))
        c.text_center("Enter / Пробел   начать",
                      y=h // 2 + 92, size=24, color_bgr=(160, 160, 160))
        c.text_center(UI["hint_quit"], y=h - 28, size=16, color_bgr=(130, 130, 130))


def draw_countdown(frame: np.ndarray, target: str, seconds: int) -> None:
    """Экран подготовки: затемнение + эмоция + подсказки (крупно) + обратный отсчёт."""
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    cv2.line(frame, (w // 4, 150), (w * 3 // 4, 150), (70, 70, 70), 1)

    target_ru = EMOTION_NAMES.get(target, target)
    num_color = (0, 200, 80) if seconds > 3 else (0, 200, 255)

    with FrameCanvas(frame) as c:
        c.text_center("Приготовься!",        y=18,  size=34, color_bgr=(200, 200, 200))
        c.text_center(target_ru.upper(),      y=68,  size=52, color_bgr=(0, 220, 220), bold=True)
        hints = EMOTION_HINTS.get(target, [])
        hint_y = 162
        for line in hints:
            c.text_center(line, y=hint_y, size=36, color_bgr=(240, 200, 80))  # крупный шрифт
            hint_y += 46
        c.text_center_shadow(str(seconds), y=h - 120, size=110,
                             color_bgr=num_color, shadow_bgr=(0, 50, 0))


def draw_hud(frame: np.ndarray, target: str, streak: int,
             score: int, feedback_timer: int, timeout_timer: int,
             emotion_index: int, time_left: int, emotion_time_limit: int,
             face_labels: list | None = None) -> None:
    """Рисует игровой HUD поверх кадра."""
    h, w = frame.shape[:2]

    # --- Прогресс-бар (OpenCV) ---
    bar_w = 260
    bar_x = (w - bar_w) // 2
    bar_y = 68
    bar_h = 16
    filled = int(streak / MATCH_FRAMES_REQUIRED * bar_w)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
    if filled > 0:
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled, bar_y + bar_h), (0, 210, 100), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (160, 160, 160), 1)

    # --- Таймер (OpenCV, справа от прогресс-бара) ---
    timer_color = (0, 200, 80)
    if feedback_timer == 0 and timeout_timer == 0:
        ratio = time_left / emotion_time_limit
        if ratio > 0.5:
            timer_color = (0, 200, 80)
        elif ratio > 0.25:
            timer_color = (0, 200, 255)
        else:
            timer_color = (0, 0, 255)
        timer_x = bar_x + bar_w + 14
        timer_y_top = bar_y
        timer_y_bot = bar_y + bar_h
        timer_filled = int(ratio * bar_h)
        cv2.rectangle(frame, (timer_x, timer_y_top), (timer_x + 8, timer_y_bot), (50, 50, 50), -1)
        if timer_filled > 0:
            cv2.rectangle(frame, (timer_x, timer_y_bot - timer_filled),
                          (timer_x + 8, timer_y_bot), timer_color, -1)
        cv2.rectangle(frame, (timer_x, timer_y_top), (timer_x + 8, timer_y_bot), (120, 120, 120), 1)

    target_ru = EMOTION_NAMES.get(target, target)

    with FrameCanvas(frame) as c:
        # Название эмоции
        c.text_center(f"{UI['challenge_prefix']} {target_ru.upper()}",
                      y=18, size=38, color_bgr=(0, 220, 220), bold=True)
        # Подсказки под прогресс-баром (мелкий шрифт)
        hints = EMOTION_HINTS.get(target, [])
        hint_y = bar_y + bar_h + 10
        for line in hints:
            c.text_center(line, y=hint_y, size=16, color_bgr=(240, 200, 80))
            hint_y += 20
        # Счёт (top right)
        c.text_right(f"{UI['score_label']} {score}",
                     y=18, size=28, color_bgr=(255, 255, 255), bold=True)
        # Счётчик эмоций (top left)
        c.text_at(f"{emotion_index + 1} / {EMOTIONS_PER_SESSION}",
                  x=12, y=18, size=24, color_bgr=(180, 180, 180))
        # Оставшееся время (цифры)
        if feedback_timer == 0 and timeout_timer == 0:
            tl_color = timer_color  # type: ignore[assignment]
            c.text_right(f"{max(time_left, 0)} сек",
                         y=bar_y - 2, size=18, color_bgr=tl_color, margin=14)
        # Фидбек успеха
        if feedback_timer > 0:
            c.text_center_shadow(UI["feedback_success"],
                                 y=h // 2 - 40, size=72,
                                 color_bgr=(0, 255, 80), shadow_bgr=(0, 70, 0))
        # Фидбек таймаута
        if timeout_timer > 0:
            c.text_center_shadow("Время вышло!",
                                 y=h // 2 - 40, size=60,
                                 color_bgr=(0, 0, 255), shadow_bgr=(0, 0, 80))
        # Метки над боксами лиц
        if face_labels:
            for lx, ly, ltext, lcolor in face_labels:
                c.text_at(ltext, x=lx, y=max(ly - 26, 2), size=18, color_bgr=lcolor)
        # Кнопка выхода
        c.text_center(UI["hint_quit"], y=h - 28, size=16, color_bgr=(130, 130, 130))


def draw_session_end(frame: np.ndarray, score: int) -> None:
    """Экран завершения сессии с итоговым счётом."""
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.70, frame, 0.30, 0, frame)

    with FrameCanvas(frame) as c:
        c.text_center("Сессия завершена!",
                      y=h // 2 - 90, size=48, color_bgr=(0, 220, 220), bold=True)
        c.text_center_shadow(f"{score} / {EMOTIONS_PER_SESSION}",
                             y=h // 2 - 20, size=90,
                             color_bgr=(0, 255, 80), shadow_bgr=(0, 70, 0))
        c.text_center("эмоций угадано",
                      y=h // 2 + 80, size=30, color_bgr=(200, 200, 200))


# --- Webcam ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError(UI["camera_error"])

# --- Экран настройки ---
emotion_time_limit = EMOTION_TIME_DEFAULT
while True:
    ret, frame = cap.read()
    if not ret:
        break
    draw_setup(frame, emotion_time_limit)
    cv2.imshow(WINDOW_NAME, frame)
    key = cv2.waitKey(30) & 0xFF
    if key == ord("q"):
        detector.close()
        cap.release()
        cv2.destroyAllWindows()
        raise SystemExit
    elif key in (ord("+"), ord("=")):
        emotion_time_limit = min(EMOTION_TIME_MAX, emotion_time_limit + EMOTION_TIME_STEP)
    elif key == ord("-"):
        emotion_time_limit = max(EMOTION_TIME_MIN, emotion_time_limit - EMOTION_TIME_STEP)
    elif key in (13, 32):  # Enter или Пробел
        break

# --- Session ---
SESSION_ID = f"session_{int(time.time())}"

# --- Game state ---
session_emotions    = random.sample(CHALLENGE_EMOTIONS, EMOTIONS_PER_SESSION)
emotion_index       = 0
target_emotion      = session_emotions[0]
match_streak        = 0
score               = 0
feedback_timer      = 0
timeout_timer       = 0
frame_count         = 0
cached_detections   = []
in_countdown        = True
countdown_start     = time.time()
emotion_start_time  = 0.0
session_end_timer   = 0

send_event({
    "session_id":        SESSION_ID,
    "event_type":        "session_start",
    "time_limit":        emotion_time_limit,
    "timestamp":         int(time.time()),
})
print(UI["start_msg"])

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print(UI["frame_error"])
        break

    # --- Экран завершения сессии ---
    if session_end_timer > 0:
        draw_session_end(frame, score)
        cv2.imshow(WINDOW_NAME, frame)
        if cv2.waitKey(5) & 0xFF == ord("q"):
            break
        session_end_timer -= 1
        if session_end_timer == 0:
            break
        continue

    # --- Экран обратного отсчёта ---
    if in_countdown:
        seconds_left = COUNTDOWN_DURATION - int(time.time() - countdown_start)
        if seconds_left <= 0:
            in_countdown = False
            emotion_start_time = time.time()
        else:
            draw_countdown(frame, target_emotion, seconds_left)
            cv2.imshow(WINDOW_NAME, frame)
            if cv2.waitKey(5) & 0xFF == ord("q"):
                detector.close()
                cap.release()
                cv2.destroyAllWindows()
                raise SystemExit
            continue

    # Оставшееся время на эмоцию
    time_left = emotion_time_limit - int(time.time() - emotion_start_time)

    # Детекция лиц — каждые 2 кадра
    frame_count += 1
    if frame_count % 2 == 0:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,
                            data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cached_detections = detector.detect(mp_image).detections

    # Рисуем боксы и собираем метки
    emotion     = None
    emo_conf    = 0.0
    face_labels = []
    for i, detection in enumerate(cached_detections):
        bbox = detection.bounding_box
        x, y, bw, bh = bbox.origin_x, bbox.origin_y, bbox.width, bbox.height

        det_emotion, det_conf = classify_emotion(frame, x, y, bw, bh)
        color = EMOTION_COLOR.get(det_emotion, (200, 200, 200))

        cv2.rectangle(frame, (x, y), (x + bw, y + bh), color, 2)
        face_labels.append((x, y, f"{EMOTION_NAMES.get(det_emotion, det_emotion)} {det_conf:.0%}", color))

        if i == 0:
            emotion  = det_emotion
            emo_conf = det_conf

    # --- Game logic ---
    def _advance_emotion():
        """Переходит к следующей эмоции или завершает сессию."""
        global emotion_index, target_emotion, match_streak, in_countdown
        global countdown_start, session_end_timer
        emotion_index += 1
        if emotion_index >= EMOTIONS_PER_SESSION:
            session_end_timer = SESSION_END_FRAMES
        else:
            target_emotion = session_emotions[emotion_index]
            match_streak = 0
            in_countdown = True
            countdown_start = time.time()

    if timeout_timer > 0:
        timeout_timer -= 1
        if timeout_timer == 0:
            _advance_emotion()
    elif feedback_timer > 0:
        feedback_timer -= 1
        if feedback_timer == 0:
            _advance_emotion()
    else:
        # Проверяем таймаут
        if time_left <= 0:
            send_event({
                "session_id":       SESSION_ID,
                "event_type":       "emotion_task",
                "target_emotion":   target_emotion,
                "detected_emotion": emotion,
                "confidence":       round(emo_conf, 3) if emo_conf else 0.0,
                "success":          False,
                "timeout":          True,
                "timestamp":        int(time.time()),
            })
            match_streak = 0
            timeout_timer = TIMEOUT_FRAMES
        # Проверяем совпадение эмоции
        elif emotion == target_emotion and emo_conf > 0.55:
            match_streak += 1
            if match_streak >= MATCH_FRAMES_REQUIRED:
                score += 1
                feedback_timer = FEEDBACK_FRAMES
                send_event({
                    "session_id":       SESSION_ID,
                    "event_type":       "emotion_task",
                    "target_emotion":   target_emotion,
                    "detected_emotion": emotion,
                    "confidence":       round(emo_conf, 3),
                    "success":          True,
                    "timeout":          False,
                    "timestamp":        int(time.time()),
                })
        else:
            match_streak = 0

    # --- HUD ---
    draw_hud(frame, target_emotion, match_streak, score,
             feedback_timer, timeout_timer, emotion_index,
             time_left, emotion_time_limit, face_labels)

    cv2.imshow(WINDOW_NAME, frame)
    if cv2.waitKey(5) & 0xFF == ord("q"):
        break

detector.close()
cap.release()
cv2.destroyAllWindows()
send_event({"session_id": SESSION_ID, "event_type": "session_end",
            "score": score, "timestamp": int(time.time())})
print(UI["exit_msg"])
