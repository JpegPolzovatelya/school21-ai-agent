#!/bin/bash

# Creates a new empty log file.
initialize_log() {
    local log_file="$1"

    if ! : > "$log_file"; then
        echo "Ошибка: не удалось создать лог-файл $log_file." >&2
        return 1
    fi
}

# Returns the current local date and time.
current_datetime() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Writes information about a created directory.
log_directory() {
    local log_file="$1"
    local directory_path="$2"
    local creation_time

    creation_time="$(current_datetime)"

    if ! printf 'DIR  | %s | %s\n' \
        "$directory_path" "$creation_time" >> "$log_file"; then
        echo "Ошибка: не удалось записать папку в лог $log_file." >&2
        return 1
    fi
}

# Writes information about a created file.
log_file_entry() {
    local log_file="$1"
    local file_path="$2"
    local size_mb="$3"
    local creation_time

    creation_time="$(current_datetime)"

    if ! printf 'FILE | %s | %s | %s MB\n' \
        "$file_path" "$creation_time" "$size_mb" >> "$log_file"; then
        echo "Ошибка: не удалось записать файл в лог $log_file." >&2
        return 1
    fi
}

# Appends the start, end and duration values to the log.
log_runtime() {
    local log_file="$1"
    local start_time="$2"
    local end_time="$3"
    local duration_seconds="$4"

    if ! printf 'START    | %s\nEND      | %s\nDURATION | %s seconds\n' \
        "$start_time" "$end_time" "$duration_seconds" >> "$log_file"; then
        echo "Ошибка: не удалось записать время работы в лог $log_file." >&2
        return 1
    fi
}

# Prints the start, end and duration values to the terminal.
print_runtime() {
    local start_time="$1"
    local end_time="$2"
    local duration_seconds="$3"

    printf 'Время начала: %s\n' "$start_time"
    printf 'Время окончания: %s\n' "$end_time"
    printf 'Общее время работы: %s секунд\n' "$duration_seconds"
}
