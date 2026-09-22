#!/bin/bash

# Создаёт статический HTML-отчёт из всех переданных nginx-логов.
generate_report() {
    local output_file="$1"
    shift
    local -a log_files=("$@")

    if ! goaccess "${log_files[@]}" \
        --log-format=COMBINED \
        --date-format='%d/%b/%Y' \
        --time-format='%T' \
        --output="$output_file"; then
        echo "Ошибка: GoAccess не смог создать отчёт." >&2
        return 1
    fi

    printf 'HTML-отчёт создан: %s\n' "$output_file"
}
