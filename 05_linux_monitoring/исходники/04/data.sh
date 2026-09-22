#!/bin/bash

readonly -a HTTP_METHODS=(GET POST PUT PATCH DELETE)

# Коды ответа HTTP (их расшифровка требуется по условию задания):
# 200 — запрос успешно выполнен.
# 201 — ресурс успешно создан.
# 400 — клиент отправил некорректный запрос.
# 401 — для доступа требуется аутентификация.
# 403 — доступ к ресурсу запрещён.
# 404 — запрошенный ресурс не найден.
# 500 — внутренняя ошибка сервера.
# 501 — сервер не поддерживает запрошенный метод.
# 502 — от вышестоящего сервера получен некорректный ответ.
# 503 — сервис временно недоступен.
readonly -a HTTP_CODES=(200 201 400 401 403 404 500 501 502 503)

readonly -a URLS=(
    /
    /index.html
    /about
    /contacts
    /products
    /api/v1/users
    /api/v1/orders
    /images/logo.png
    /static/style.css
    /login
)

readonly -a REFERERS=(
    -
    https://example.com/
    https://example.com/products
    https://www.google.com/
    https://www.bing.com/
)

readonly -a USER_AGENTS=(
    "Mozilla/5.0"
    "Google Chrome/126.0"
    "Opera/111.0"
    "Safari/17.5"
    "Internet Explorer/11.0"
    "Microsoft Edge/126.0"
    "Crawler and bot/1.0"
    "Library and net tool/1.0"
)
