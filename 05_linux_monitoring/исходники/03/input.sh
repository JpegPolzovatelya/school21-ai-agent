#!/bin/bash

# Loads validation functions when this module is tested separately.
if ! declare -F validate_log_file >/dev/null; then
    source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/validation.sh"
fi

# Prompts until a valid log-file path is entered.
prompt_log_file() {
    local log_file

    while true; do
        printf 'Введите полный путь к лог-файлу части 2: ' >&2

        if ! IFS= read -r log_file; then
            validation_error "не удалось прочитать путь к лог-файлу."
            return 1
        fi

        if validate_log_file "$log_file"; then
            printf '%s' "$log_file"
            return 0
        fi
    done
}

# Prompts until a valid chronological date range is entered.
prompt_datetime_range() {
    local start_time
    local end_time

    while true; do
        printf 'Введите начало периода (YYYY-MM-DD HH:MM): ' >&2

        if ! IFS= read -r start_time; then
            validation_error "не удалось прочитать начало периода."
            return 1
        fi

        printf 'Введите конец периода (YYYY-MM-DD HH:MM): ' >&2

        if ! IFS= read -r end_time; then
            validation_error "не удалось прочитать конец периода."
            return 1
        fi

        if validate_datetime_range "$start_time" "$end_time"; then
            printf '%s\n%s\n' "$start_time" "$end_time"
            return 0
        fi
    done
}

# Prompts until a valid letters_DDMMYY mask is entered.
prompt_name_mask() {
    local mask

    while true; do
        printf 'Введите маску в формате letters_DDMMYY: ' >&2

        if ! IFS= read -r mask; then
            validation_error "не удалось прочитать маску."
            return 1
        fi

        if validate_name_mask "$mask"; then
            printf '%s' "$mask"
            return 0
        fi
    done
}

# Requests explicit confirmation before deletion.
request_confirmation() {
    local answer

    printf 'Подтвердить удаление? [y/N]: ' >&2

    if ! IFS= read -r answer; then
        validation_error "не удалось прочитать подтверждение."
        return 1
    fi

    case "$answer" in
        y | Y | yes | YES | Yes | д | Д | да | ДА | Да)
            return 0
            ;;
        *)
            echo "Очистка отменена." >&2
            return 1
            ;;
    esac
}
