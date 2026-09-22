#!/bin/bash

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/validation.sh"
source "$SCRIPT_DIR/generator.sh"
source "$SCRIPT_DIR/logger.sh"
source "$SCRIPT_DIR/filesystem.sh"

readonly MAX_DIRECTORIES=100
readonly MAX_FILES_PER_DIRECTORY=100

# Finishes timing, writes it to the log and prints it to the terminal.
finish_run() {
    local log_file="$1"
    local start_time="$2"
    local start_seconds="$3"
    local end_time
    local end_seconds
    local duration_seconds

    end_time="$(current_datetime)"
    end_seconds="$(date +%s)"
    duration_seconds=$((end_seconds - start_seconds))

    print_runtime "$start_time" "$end_time" "$duration_seconds"

    if ! log_runtime \
        "$log_file" "$start_time" "$end_time" "$duration_seconds"; then
        return 1
    fi

    printf 'Лог-файл: %s\n' "$log_file"
}

main() {
    if ! validate_args "$@"; then
        return 1
    fi

    local directory_letters="$1"
    local file_pattern="$2"
    local file_size_argument="$3"

    local file_letters="${file_pattern%%.*}"
    local extension_letters="${file_pattern##*.}"
    local file_size_mb="${file_size_argument%Mb}"
    local run_date
    local log_file
    local start_time
    local start_seconds

    run_date="$(date '+%d%m%y')"
    log_file="$SCRIPT_DIR/generator_$(date '+%d%m%y_%H%M%S').log"
    start_time="$(current_datetime)"
    start_seconds="$(date +%s)"

    if ! initialize_log "$log_file"; then
        return 1
    fi

    local -a candidate_directories
    mapfile -t candidate_directories < <(list_candidate_directories)

    if (( ${#candidate_directories[@]} == 0 )); then
        echo "Ошибка: не найдено доступных каталогов для записи." >&2
        finish_run "$log_file" "$start_time" "$start_seconds"
        return 1
    fi

    local directory_target
    directory_target="$(random_between 1 "$MAX_DIRECTORIES")"

    local directory_index=0
    local created_directories=0

    printf 'Будет создано папок: %s\n' "$directory_target"

    while (( created_directories < directory_target )); do
        local space_status

        has_enough_space 0
        space_status=$?

        if (( space_status == 2 )); then
            finish_run "$log_file" "$start_time" "$start_seconds"
            return 1
        elif (( space_status != 0 )); then
            echo "Остановка: в разделе / осталось 1 ГБ свободного места или меньше."
            finish_run "$log_file" "$start_time" "$start_seconds"
            return 0
        fi

        local base_path
        local directory_name
        local directory_path

        if ! base_path="$(
            select_random_directory "${candidate_directories[@]}"
        )"; then
            finish_run "$log_file" "$start_time" "$start_seconds"
            return 1
        fi

        directory_name="$(
            generate_directory_name \
                "$directory_letters" "$directory_index" "$run_date"
        )"
        directory_path="${base_path%/}/$directory_name"

        if [[ -e "$directory_path" ]]; then
            ((directory_index++))
            continue
        fi

        if ! directory_path="$(
            create_directory "$base_path" "$directory_name"
        )"; then
            finish_run "$log_file" "$start_time" "$start_seconds"
            return 1
        fi

        if ! log_directory "$log_file" "$directory_path"; then
            finish_run "$log_file" "$start_time" "$start_seconds"
            return 1
        fi

        local files_target
        files_target="$(random_between 1 "$MAX_FILES_PER_DIRECTORY")"

        local file_index
        for ((file_index = 0; file_index < files_target; file_index++)); do
            has_enough_space "$file_size_mb"
            space_status=$?

            if (( space_status == 2 )); then
                finish_run "$log_file" "$start_time" "$start_seconds"
                return 1
            elif (( space_status != 0 )); then
                echo "Остановка: следующий файл оставит 1 ГБ свободного места или меньше."
                finish_run "$log_file" "$start_time" "$start_seconds"
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
                create_file "$directory_path" "$file_name" "$file_size_mb"
            )"; then
                finish_run "$log_file" "$start_time" "$start_seconds"
                return 1
            fi

            if ! log_file_entry \
                "$log_file" "$file_path" "$file_size_mb"; then
                finish_run "$log_file" "$start_time" "$start_seconds"
                return 1
            fi
        done

        ((created_directories++))
        ((directory_index++))
    done

    echo "Генерация завершена."
    finish_run "$log_file" "$start_time" "$start_seconds"
}

main "$@"
