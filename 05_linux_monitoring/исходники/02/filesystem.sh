#!/bin/bash

readonly MIN_FREE_SPACE_KB=1048576

# Returns the available space on the root filesystem in kilobytes.
get_free_space_kb() {
    df -Pk / | awk 'NR == 2 {print $4}'
}

# Checks that creating a file will leave more than 1 GB free.
has_enough_space() {
    local size_mb="${1:-0}"
    local required_kb=$((size_mb * 1024))
    local free_space_kb

    free_space_kb="$(get_free_space_kb)"

    if [[ ! "$free_space_kb" =~ ^[0-9]+$ ]]; then
        echo "Ошибка: не удалось определить свободное место в разделе /." >&2
        return 2
    fi

    (( free_space_kb - required_kb > MIN_FREE_SPACE_KB ))
}

# Returns success when a path must not be used for generation.
is_forbidden_path() {
    local path="$1"

    case "$path" in
        / | *bin* | /proc | /proc/* | /sys | /sys/* | /dev | /dev/* | \
        /run | /run/*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Prints writable candidate directories, one path per line.
list_candidate_directories() {
    local directory

    while IFS= read -r directory; do
        if [[ -d "$directory" && -w "$directory" ]] &&
            ! is_forbidden_path "$directory"; then
            printf '%s\n' "$directory"
        fi
    done < <(find / -xdev -type d -print 2>/dev/null)
}

# Selects one random element from the supplied directory list.
select_random_directory() {
    local -a directories=("$@")
    local directory_count="${#directories[@]}"

    if (( directory_count == 0 )); then
        echo "Ошибка: не найдено доступных каталогов для записи." >&2
        return 1
    fi

    printf '%s' "${directories[RANDOM % directory_count]}"
}

# Prints a random integer in the inclusive range min..max.
random_between() {
    local minimum="$1"
    local maximum="$2"

    if (( minimum > maximum )); then
        echo "Ошибка: неверный диапазон случайного числа." >&2
        return 1
    fi

    printf '%s' $((RANDOM % (maximum - minimum + 1) + minimum))
}
