#!/bin/bash

# Creates or clears the log file before generation starts.
initialize_log() {
    local log_file="$1"

    if ! : > "$log_file"; then
        echo "Ошибка: не удалось создать лог-файл $log_file." >&2
        return 1
    fi
}

# Returns the current date and time in a readable format.
current_datetime() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Writes information about a created directory to the log.
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

# Writes information about a created file to the log.
log_file_entry() {
    local log_file="$1"
    local file_path="$2"
    local size_kb="$3"
    local creation_time

    creation_time="$(current_datetime)"

    if ! printf 'FILE | %s | %s | %s KB\n' \
        "$file_path" "$creation_time" "$size_kb" >> "$log_file"; then
        echo "Ошибка: не удалось записать файл в лог $log_file." >&2
        return 1
    fi
}
