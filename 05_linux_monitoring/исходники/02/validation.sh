#!/bin/bash

# Prints a validation error to stderr.
validation_error() {
    echo "Ошибка: $1" >&2
    return 1
}

# Checks the three arguments required by Part 2.
validate_args() {
    if [[ $# -ne 3 ]]; then
        validation_error "ожидалось 3 аргумента, получено $#."
        return 1
    fi

    local directory_letters="$1"
    local file_pattern="$2"
    local file_size="$3"

    if [[ ! "$directory_letters" =~ ^[A-Za-z]{1,7}$ ]]; then
        validation_error \
            "буквы для папок должны содержать от 1 до 7 английских букв."
        return 1
    fi

    if [[ ! "$file_pattern" =~ ^[A-Za-z]{1,7}\.[A-Za-z]{1,3}$ ]]; then
        validation_error \
            "шаблон файла должен иметь вид name.ext: имя — 1–7 английских букв, расширение — 1–3."
        return 1
    fi

    if [[ ! "$file_size" =~ ^([1-9][0-9]?|100)Mb$ ]]; then
        validation_error \
            "размер файла должен иметь формат NMb, где N — от 1 до 100."
        return 1
    fi

    return 0
}

# Runs validation only when this file is executed directly.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    validate_args "$@"
fi
