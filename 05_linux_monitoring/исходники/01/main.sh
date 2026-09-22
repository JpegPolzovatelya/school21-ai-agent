#!/bin/bash

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/validation.sh"
source "$SCRIPT_DIR/generator.sh"
source "$SCRIPT_DIR/logger.sh"

readonly MIN_FREE_SPACE_KB=1048576

# Returns the available space on the root filesystem in kilobytes.
get_free_space_kb() {
    df -Pk / | awk 'NR == 2 {print $4}'
}

# Checks that creating another file will leave more than 1 GB free.
has_enough_space() {
    local required_kb="${1:-0}"
    local free_space_kb

    free_space_kb="$(get_free_space_kb)"

    if [[ ! "$free_space_kb" =~ ^[0-9]+$ ]]; then
        echo "Ошибка: не удалось определить свободное место в разделе /." >&2
        return 2
    fi

    (( free_space_kb - required_kb > MIN_FREE_SPACE_KB ))
}

main() {
    if ! validate_args "$@"; then
        return 1
    fi

    local base_path="$1"
    local directory_count="$2"
    local directory_letters="$3"
    local files_per_directory="$4"
    local file_pattern="$5"
    local file_size_argument="$6"

    local file_letters="${file_pattern%%.*}"
    local extension_letters="${file_pattern##*.}"
    local file_size_kb="${file_size_argument%kb}"
    local run_date
    local log_file

    run_date="$(date '+%d%m%y')"
    log_file="$SCRIPT_DIR/generator_$(date '+%d%m%y_%H%M%S').log"

    if ! initialize_log "$log_file"; then
        return 1
    fi

    local directory_index=0
    local created_directories=0

    while (( created_directories < directory_count )); do
        local space_status

        has_enough_space 0
        space_status=$?

        if (( space_status == 2 )); then
            return 1
        elif (( space_status != 0 )); then
            echo "Остановка: в разделе / осталось 1 ГБ свободного места или меньше."
            return 0
        fi

        local directory_name
        local directory_path

        directory_name="$(
            generate_directory_name \
                "$directory_letters" "$directory_index" "$run_date"
        )"
        directory_path="${base_path%/}/$directory_name"

        if [[ -e "$directory_path" ]]; then
            ((directory_index++))
            continue
        fi

        if ! directory_path="$(create_directory "$base_path" "$directory_name")"; then
            return 1
        fi

        if ! log_directory "$log_file" "$directory_path"; then
            return 1
        fi

        local file_index
        for ((file_index = 0; file_index < files_per_directory; file_index++)); do
            has_enough_space "$file_size_kb"
            space_status=$?

            if (( space_status == 2 )); then
                return 1
            elif (( space_status != 0 )); then
                echo "Остановка: создание следующего файла оставит 1 ГБ свободного места или меньше."
                return 0
            fi

            local file_name
            local file_path

            file_name="$(
                generate_file_name \
                    "$file_letters" "$extension_letters" \
                    "$file_index" "$run_date"
            )"

            if ! file_path="$(
                create_file "$directory_path" "$file_name" "$file_size_kb"
            )"; then
                return 1
            fi

            if ! log_file_entry "$log_file" "$file_path" "$file_size_kb"; then
                return 1
            fi
        done

        ((created_directories++))
        ((directory_index++))
    done

    echo "Генерация завершена."
    echo "Лог-файл: $log_file"
}

main "$@"
