#!/bin/bash

# Prints a validation error to stderr.
validation_error() {
    echo "Ошибка: $1" >&2
    return 1
}

# Checks that exactly one cleanup mode (1, 2 or 3) was supplied.
validate_mode() {
    if [[ $# -ne 1 ]]; then
        validation_error "ожидался 1 аргумент, получено $#."
        return 1
    fi

    if [[ ! "$1" =~ ^[1-3]$ ]]; then
        validation_error "режим очистки должен иметь значение 1, 2 или 3."
        return 1
    fi

    return 0
}

# Checks that a readable regular log file exists.
validate_log_file() {
    local log_file="$1"

    if [[ -z "$log_file" ]]; then
        validation_error "путь к лог-файлу не может быть пустым."
        return 1
    fi

    if [[ ! -f "$log_file" ]]; then
        validation_error "лог-файл не найден: $log_file."
        return 1
    fi

    if [[ ! -r "$log_file" ]]; then
        validation_error "лог-файл недоступен для чтения: $log_file."
        return 1
    fi

    if ! grep -qE '^(FILE \| /|DIR  \| /)' "$log_file"; then
        validation_error "лог-файл не содержит записей FILE или DIR."
        return 1
    fi

    return 0
}

# Checks one date and time in the format YYYY-MM-DD HH:MM.
validate_datetime() {
    local value="$1"
    local normalized

    if [[ ! "$value" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}[[:space:]][0-9]{2}:[0-9]{2}$ ]]; then
        validation_error "дата и время должны иметь формат YYYY-MM-DD HH:MM."
        return 1
    fi

    normalized="$(date -d "$value" '+%Y-%m-%d %H:%M' 2>/dev/null)"

    if [[ "$normalized" != "$value" ]]; then
        validation_error "указана несуществующая дата или время: $value."
        return 1
    fi

    return 0
}

# Checks two date values and their chronological order.
validate_datetime_range() {
    local start_time="$1"
    local end_time="$2"
    local start_seconds
    local end_seconds

    validate_datetime "$start_time" || return 1
    validate_datetime "$end_time" || return 1

    start_seconds="$(date -d "$start_time" +%s)"
    end_seconds="$(date -d "$end_time" +%s)"

    if (( start_seconds > end_seconds )); then
        validation_error "начальное время не может быть позже конечного."
        return 1
    fi

    return 0
}

# Checks a cleanup mask in the form letters_DDMMYY.
validate_name_mask() {
    local mask="$1"
    local mask_date
    local day
    local month
    local year
    local normalized

    if [[ ! "$mask" =~ ^[A-Za-z]{1,7}_[0-9]{6}$ ]]; then
        validation_error "маска должна иметь формат letters_DDMMYY."
        return 1
    fi

    mask_date="${mask##*_}"
    day="${mask_date:0:2}"
    month="${mask_date:2:2}"
    year="${mask_date:4:2}"
    normalized="$(date -d "20${year}-${month}-${day}" '+%d%m%y' 2>/dev/null)"

    if [[ "$normalized" != "$mask_date" ]]; then
        validation_error "маска содержит несуществующую дату: $mask_date."
        return 1
    fi

    return 0
}

# Checks that a deletion target is an absolute, non-system path.
validate_target_path() {
    local path="$1"

    if [[ "$path" != /* ]]; then
        validation_error "путь удаления должен быть абсолютным: $path."
        return 1
    fi

    case "$path" in
        / | *bin* | /proc | /proc/* | /sys | /sys/* | /dev | /dev/* | \
        /run | /run/*)
            validation_error "запрещённый путь удаления: $path."
            return 1
            ;;
    esac

    return 0
}

# Runs only the mode check when this file is executed directly.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    validate_mode "$@"
fi
