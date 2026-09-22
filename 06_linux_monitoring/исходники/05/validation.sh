#!/bin/bash

# Выводит сообщение об ошибке в stderr и возвращает код 1.
validation_error() {
    echo "Ошибка: $1" >&2
    return 1
}

# Проверяет единственный аргумент — режим анализа от 1 до 4.
validate_args() {
    if [[ $# -ne 1 ]]; then
        validation_error "ожидался 1 аргумент, получено $#."
        return 1
    fi

    if [[ ! "$1" =~ ^[1-4]$ ]]; then
        validation_error "режим должен иметь значение 1, 2, 3 или 4."
        return 1
    fi

    return 0
}

# Находит непустые логи, созданные частью 4.
# Результат сохраняется в глобальном массиве LOG_FILES.
collect_log_files() {
    local logs_directory="$1"
    local file

    LOG_FILES=()

    # nullglob превращает отсутствующую маску в пустой список.
    shopt -s nullglob
    for file in "$logs_directory"/nginx_*.log; do
        if [[ -f "$file" && -s "$file" && -r "$file" ]]; then
            LOG_FILES+=("$file")
        fi
    done
    shopt -u nullglob

    if (( ${#LOG_FILES[@]} == 0 )); then
        validation_error "в каталоге $logs_directory не найдены непустые nginx-логи."
        return 1
    fi

    return 0
}
