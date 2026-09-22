#!/bin/bash

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/data.sh"
source "$SCRIPT_DIR/generator.sh"
source "$SCRIPT_DIR/logger.sh"

readonly LOG_DAYS=5

# Проверяет аргументы и создаёт логи за последние пять дней.
main() {
    if (( $# != 0 )); then
        echo "Ошибка: скрипт запускается без аргументов." >&2
        return 1
    fi

    local offset
    local log_day
    local output_file

    for ((offset = LOG_DAYS - 1; offset >= 0; offset--)); do
        log_day="$(date -d "$offset days ago" '+%Y-%m-%d')"
        output_file="$SCRIPT_DIR/nginx_${log_day}.log"

        if ! generate_daily_log "$log_day" "$output_file"; then
            return 1
        fi
    done

    echo "Генерация логов завершена."
}

main "$@"
