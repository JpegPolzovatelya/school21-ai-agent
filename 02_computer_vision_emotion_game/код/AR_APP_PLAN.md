# План разработки AR-приложения с мини-игрой эмоций

## Идея

Мобильное AR-приложение: камера видит лицо пользователя, игра просит показать эмоцию,
AR-эффекты реагируют на результат. Основа — механика из `comp_vision_env`.

---

## Стек технологий

| Слой | Инструмент |
|---|---|
| Движок | Unity 2022 LTS |
| AR | AR Foundation 5.x + ARKit (iOS) / ARCore (Android) |
| ML-инференс | Unity Sentis (новое название Barracuda, Unity 2023+) |
| Модель эмоций | `emotion-ferplus.onnx` (уже есть) |
| Язык | C# |
| Сборка iOS | Xcode 15+, Apple Developer Account |
| Сборка Android | Android Studio, минимум Android 8.0 (ARCore) |

---

## Этапы разработки

### Этап 1 — Подготовка среды (1–2 дня)

- [ ] Установить Unity 2022 LTS (или 2023 LTS)
- [ ] Добавить модули: **iOS Build Support**, **Android Build Support**
- [ ] Создать новый проект: `3D (URP)` шаблон
- [ ] Установить пакеты через Package Manager:
  - `AR Foundation`
  - `Apple ARKit XR Plugin` (для iOS)
  - `Google ARCore XR Plugin` (для Android)
  - `Unity Sentis` (ML-инференс)
- [ ] Настроить Project Settings:
  - Camera Usage Description (iOS)
  - Minimum API Level 26 (Android)
  - Target Architecture: ARM64

---

### Этап 2 — AR-сцена и захват лица (3–5 дней)

- [ ] Создать AR-сцену:
  - `AR Session` — управляет AR-сессией
  - `AR Session Origin` / `XR Origin` — точка отсчёта AR
  - `AR Camera` — основная камера с AR-компонентами
- [ ] Подключить **AR Face Manager**:
  - Отслеживает лицо через ARKit / ARCore
  - Даёт меш лица и blendshapes (мимика)
- [ ] Написать скрипт `FaceCaptureController.cs`:
  - Захватывает кадр с камеры каждые N кадров
  - Конвертирует в grayscale 64×64 (под формат модели)
  - Передаёт тензор в ML-модуль

```
AR Camera → Texture2D → Resize(64x64) → Grayscale → float32[1,1,64,64]
```

---

### Этап 3 — Интеграция модели эмоций (3–4 дня)

- [ ] Скопировать `emotion-ferplus.onnx` в `Assets/StreamingAssets/Models/`
- [ ] Написать скрипт `EmotionClassifier.cs`:

```csharp
// Псевдокод
public class EmotionClassifier : MonoBehaviour
{
    ModelAsset modelAsset;
    Worker worker;

    string[] labels = { "neutral","happiness","surprise","sadness",
                         "anger","disgust","fear","contempt" };

    void Start() {
        var model = ModelLoader.Load(modelAsset);
        worker = new Worker(model, BackendType.GPUCompute);
    }

    public string Predict(Texture2D frame) {
        var tensor = TextureConverter.ToTensor(frame, 64, 64, 1);
        worker.Schedule(tensor);
        var output = worker.PeekOutput() as TensorFloat;
        output.CompleteOperationsAndDownload();
        int idx = ArgMax(output);
        tensor.Dispose();
        return labels[idx];
    }
}
```

- [ ] Протестировать инференс на реальном устройстве (не симулятор!)
- [ ] Убедиться, что FPS не проседает (запускать предсказание раз в 10–15 кадров)

---

### Этап 4 — Игровая механика (4–5 дней)

Перенос логики из `src/main.py` на C#.

- [ ] Написать `GameManager.cs`:
  - Список эмоций для показа: `happiness, surprise, sadness, anger, disgust`
  - Выбор случайной эмоции → показ задания
  - Счётчик совпадающих кадров (аналог `MATCH_FRAMES_REQUIRED = 20`)
  - Начисление очков при успехе
  - Переход к следующей эмоции

- [ ] Написать `HintSystem.cs`:
  - Подсказки из `strings.json` (перенести в `hints.json` для Unity)
  - Показывать текст подсказки под заданием

- [ ] Логика состояний:
```
IDLE → SHOW_CHALLENGE → WAITING_FOR_EMOTION → SUCCESS → NEXT_CHALLENGE
```

---

### Этап 5 — AR-эффекты (3–5 дней)

- [ ] **Маска на лицо** — AR Face Mesh:
  - Наложить полупрозрачный меш на лицо
  - Менять цвет/текстуру в зависимости от текущей эмоции

- [ ] **Эффект успеха**:
  - Партиклы (конфетти, звёздочки) при правильной эмоции
  - Анимация шкалы прогресса (аналог `MATCH_FRAMES_REQUIRED`)

- [ ] **UI поверх AR**:
  - Canvas в режиме `Screen Space — Overlay`
  - Задание (ПОКАЖИ: Радость)
  - Подсказка
  - Счёт
  - Прогресс-бар (сколько кадров засчитано)

---

### Этап 6 — Аналитика и сохранение (1–2 дня)

- [ ] Сохранение счёта локально (`PlayerPrefs` или JSON)
- [ ] Опционально: отправка событий на сервер (порт логики `event_sender.py`)
- [ ] Таблица рекордов (локальная)

---

### Этап 7 — Полировка и сборка (3–4 дня)

- [ ] Оптимизация производительности:
  - Инференс модели в фоновом потоке или через корутину
  - Ограничить захват кадров (не каждый кадр)
- [ ] Звуки: успех, неудача, фоновая музыка
- [ ] Иконка приложения, сплеш-скрин
- [ ] Сборка и тест на реальном устройстве
- [ ] Исправление багов

---

## Структура проекта Unity

```
Assets/
├── Scripts/
│   ├── AR/
│   │   └── FaceCaptureController.cs
│   ├── ML/
│   │   └── EmotionClassifier.cs
│   ├── Game/
│   │   ├── GameManager.cs
│   │   └── HintSystem.cs
│   └── UI/
│       └── HUDController.cs
├── StreamingAssets/
│   └── Models/
│       └── emotion-ferplus.onnx
├── Resources/
│   └── hints.json
├── Scenes/
│   └── MainScene.unity
├── Prefabs/
│   ├── ConfettiEffect.prefab
│   └── FaceMask.prefab
└── UI/
    └── HUD.prefab
```

---

## Потенциальные сложности

| Проблема | Решение |
|---|---|
| FPS просадки из-за ML | Инференс раз в 10–15 кадров, фоновый поток |
| Формат входа модели (1×1×64×64) | Написать кастомный препроцессинг в `TextureConverter` |
| ARKit только на реальном iPhone | Тестировать на устройстве, не в симуляторе |
| AR Face Tracking — нужен TrueDepth (Face ID) | На Android — ARCore Face Mesh, менее точный |
| App Store / Google Play требования | AR Foundation покрывает требования к разрешениям |

---

## Примерные сроки

| Этап | Время |
|---|---|
| Подготовка среды | 1–2 дня |
| AR-сцена и захват лица | 3–5 дней |
| Интеграция модели | 3–4 дня |
| Игровая механика | 4–5 дней |
| AR-эффекты | 3–5 дней |
| Аналитика | 1–2 дня |
| Полировка и сборка | 3–4 дня |
| **Итого** | **~3–4 недели** |

---

## Следующий шаг

Начать с **Этапа 1** — установить Unity и создать пустую AR-сцену с отслеживанием лица.
Это даст понять, как ведёт себя AR на конкретном устройстве, до написания игровой логики.
