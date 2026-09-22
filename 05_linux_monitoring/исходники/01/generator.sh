#!/bin/bash

# Generates an ordered string from the supplied letters.
# The result is at least min_length characters long.
# sequence_number adds repetitions and makes consecutive names unique.
generate_ordered_part() {
    local letters="$1"
    local sequence_number="$2"
    local min_length="$3"

    local first_letter="${letters:0:1}"
    local repeat_count=$((min_length - ${#letters} + 1 + sequence_number))
    local result=""

    if (( repeat_count < 1 )); then
        repeat_count=1
    fi

    local i
    for ((i = 0; i < repeat_count; i++)); do
        result+="$first_letter"
    done

    result+="${letters:1}"
    printf '%s' "$result"
}

# Generates a directory name in the form ordered_letters_DDMMYY.
generate_directory_name() {
    local letters="$1"
    local sequence_number="$2"
    local run_date="$3"
    local name_part

    name_part="$(generate_ordered_part "$letters" "$sequence_number" 4)"
    printf '%s_%s' "$name_part" "$run_date"
}

# Generates a file name in the form ordered_letters_DDMMYY.extension.
generate_file_name() {
    local name_letters="$1"
    local extension_letters="$2"
    local sequence_number="$3"
    local run_date="$4"
    local name_part

    name_part="$(generate_ordered_part "$name_letters" "$sequence_number" 4)"
    printf '%s_%s.%s' "$name_part" "$run_date" "$extension_letters"
}

# Creates a directory and prints its full path.
create_directory() {
    local base_path="$1"
    local directory_name="$2"
    local full_path="${base_path%/}/$directory_name"

    if ! mkdir -p -- "$full_path"; then
        echo "Ошибка: не удалось создать папку $full_path." >&2
        return 1
    fi

    printf '%s' "$full_path"
}

# Creates a non-sparse file of the requested size in kilobytes.
create_file() {
    local directory_path="$1"
    local file_name="$2"
    local size_kb="$3"
    local full_path="${directory_path%/}/$file_name"

    if ! dd if=/dev/zero of="$full_path" bs=1024 count="$size_kb" status=none; then
        echo "Ошибка: не удалось создать файл $full_path." >&2
        return 1
    fi

    printf '%s' "$full_path"
}
