#!/bin/bash

# Получаем абсолютный путь к каталогу текущего скрипта.
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly LOGS_DIRECTORY="$SCRIPT_DIR/../04"

source "$SCRIPT_DIR/validation.sh"
source "$SCRIPT_DIR/analyzer.sh"

main() {
    if ! validate_args "$@"; then
        return 1
    fi

    if ! collect_log_files "$LOGS_DIRECTORY"; then
        return 1
    fi

    case "$1" in
        1)
            print_sorted_by_code "${LOG_FILES[@]}"
            ;;
        2)
            print_unique_ips "${LOG_FILES[@]}"
            ;;
        3)
            print_error_requests "${LOG_FILES[@]}"
            ;;
        4)
            print_unique_error_ips "${LOG_FILES[@]}"
            ;;
    esac
}

main "$@"
