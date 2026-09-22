#!/bin/bash

# Loads validation functions when this module is tested separately.
if ! declare -F validate_target_path >/dev/null; then
    source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/validation.sh"
fi

# Checks the basename format used by the Part 2 generator.
is_generated_target() {
    local path="$1"
    local name

    name="$(basename -- "$path")"
    [[ "$name" =~ ^[A-Za-z]+_[0-9]{6}(\.[A-Za-z]{1,3})?$ ]]
}

# Applies all safety checks to one possible deletion target.
is_safe_cleanup_target() {
    local path="$1"

    validate_target_path "$path" || return 1

    if ! is_generated_target "$path"; then
        echo "Пропуск: имя не соответствует формату генератора: $path" >&2
        return 1
    fi

    return 0
}

# Prints existing targets from a Part 2 log: files first, directories last.
collect_targets_from_log() {
    local log_file="$1"
    local path

    while IFS= read -r path; do
        if is_safe_cleanup_target "$path" && [[ -e "$path" || -L "$path" ]]; then
            printf '%s\n' "$path"
        fi
    done < <(awk -F ' \\| ' '$1 ~ /^FILE/ {print $2}' "$log_file")

    while IFS= read -r path; do
        if is_safe_cleanup_target "$path" && [[ -e "$path" || -L "$path" ]]; then
            printf '%s\n' "$path"
        fi
    done < <(
        awk -F ' \\| ' '$1 ~ /^DIR/ {print $2}' "$log_file" | tac
    )
}

# Prints generated targets modified within the supplied minute range.
collect_targets_by_time() {
    local start_time="$1"
    local end_time="$2"
    local end_exclusive
    local path

    end_exclusive="$(date -d "$end_time + 1 minute" '+%Y-%m-%d %H:%M:%S')"

    while IFS= read -r -d '' path; do
        if is_safe_cleanup_target "$path"; then
            printf '%s\n' "$path"
        fi
    done < <(
        find / -xdev -type f \
            -newermt "$start_time - 1 second" \
            ! -newermt "$end_exclusive - 1 second" \
            -print0 2>/dev/null
    )

    while IFS= read -r -d '' path; do
        if is_safe_cleanup_target "$path"; then
            printf '%s\n' "$path"
        fi
    done < <(
        find / -xdev -depth -type d \
            -newermt "$start_time - 1 second" \
            ! -newermt "$end_exclusive - 1 second" \
            -print0 2>/dev/null
    )
}

# Builds an ordered regular expression from the letters in a mask.
build_letters_regex() {
    local letters="$1"
    local regex=""
    local index
    local letter

    for ((index = 0; index < ${#letters}; index++)); do
        letter="${letters:index:1}"
        regex+="${letter}+"
    done

    printf '%s' "$regex"
}

# Prints generated files and directories matching letters_DDMMYY.
collect_targets_by_mask() {
    local mask="$1"
    local letters="${mask%%_*}"
    local mask_date="${mask##*_}"
    local letters_regex
    local name_regex
    local path
    local name

    letters_regex="$(build_letters_regex "$letters")"
    name_regex="^${letters_regex}_${mask_date}(\\.[A-Za-z]{1,3})?$"

    while IFS= read -r -d '' path; do
        name="$(basename -- "$path")"

        if [[ "$name" =~ $name_regex ]] &&
            is_safe_cleanup_target "$path"; then
            printf '%s\n' "$path"
        fi
    done < <(find / -xdev -type f -print0 2>/dev/null)

    while IFS= read -r -d '' path; do
        name="$(basename -- "$path")"

        if [[ "$name" =~ $name_regex ]] &&
            is_safe_cleanup_target "$path"; then
            printf '%s\n' "$path"
        fi
    done < <(find / -xdev -depth -type d -print0 2>/dev/null)
}

# Displays all targets before confirmation.
print_cleanup_targets() {
    local -a targets=("$@")
    local path

    printf 'Найдено объектов: %s\n' "${#targets[@]}"

    for path in "${targets[@]}"; do
        printf '%s\n' "$path"
    done
}

# Deletes validated targets in their supplied order.
delete_cleanup_targets() {
    local -a targets=("$@")
    local path
    local deleted_count=0
    local error_count=0

    for path in "${targets[@]}"; do
        if ! is_safe_cleanup_target "$path"; then
            ((error_count++))
            continue
        fi

        if [[ -L "$path" || -f "$path" ]]; then
            if rm -f -- "$path"; then
                printf 'Удалён файл: %s\n' "$path"
                ((deleted_count++))
            else
                echo "Ошибка удаления файла: $path" >&2
                ((error_count++))
            fi
        elif [[ -d "$path" ]]; then
            if rmdir -- "$path"; then
                printf 'Удалена папка: %s\n' "$path"
                ((deleted_count++))
            else
                echo "Ошибка удаления папки: $path" >&2
                ((error_count++))
            fi
        else
            printf 'Пропуск: объект не существует: %s\n' "$path" >&2
        fi
    done

    printf 'Удалено объектов: %s\n' "$deleted_count"

    if (( error_count > 0 )); then
        echo "Ошибок удаления: $error_count" >&2
        return 1
    fi

    return 0
}
