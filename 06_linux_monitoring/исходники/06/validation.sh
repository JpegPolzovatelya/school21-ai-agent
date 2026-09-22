#!/bin/bash

validation_error() {
    echo "Ошибка: $1" >&2
    return 1
}

# Проверяет, что пользователь не передал лишние аргументы.
validate_args() {
    if [[ $# -ne 0 ]]; then
        validation_error "скрипт запускается без аргументов."
        return 1
    fi
}

# Проверяет наличие программ, необходимых для отчёта и веб-сервера.
validate_dependencies() {
    if ! command -v goaccess >/dev/null 2>&1; then
        validation_error "GoAccess не установлен. Выполните: sudo apt install goaccess"
        return 1
    fi

    if ! command -v python3 >/dev/null 2>&1; then
        validation_error "Python 3 не установлен. Выполните: sudo apt install python3"
        return 1
    fi
}

# Находит непустые логи, созданные частью 4.
collect_log_files() {
    local logs_directory="$1"
    local file

    LOG_FILES=()
    shopt -s nullglob

    for file in "$logs_directory"/nginx_*.log; do
        if [[ -f "$file" && -s "$file" && -r "$file" ]]; then
            LOG_FILES+=("$file")
        fi
    done

    shopt -u nullglob

    if (( ${#LOG_FILES[@]} == 0 )); then
        validation_error "в $logs_directory не найдены непустые nginx-логи."
        return 1
    fi
}
