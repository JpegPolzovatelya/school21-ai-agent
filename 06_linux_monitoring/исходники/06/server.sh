#!/bin/bash

# Запускает простой HTTP-сервер для просмотра отчёта в браузере.
serve_report() {
    local directory="$1"
    local port="$2"

    printf 'Откройте в браузере: http://localhost:%s/report.html\n' "$port"
    printf 'Для остановки сервера нажмите Ctrl+C.\n'

    python3 -m http.server "$port" --bind 0.0.0.0 --directory "$directory"
}
