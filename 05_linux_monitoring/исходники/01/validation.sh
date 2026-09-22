#!/bin/bash

# Prints an error message to stderr and returns a failure status.
validation_error() {
    echo "Ошибка: $1" >&2
    return 1
}

# Checks all six arguments required by Part 1.
validate_args() {
    if [[ $# -ne 6 ]]; then
        validation_error "ожидалось 6 аргументов, получено $#."
        return 1
    fi

    local base_path="$1"
    local folder_count="$2"
    local folder_letters="$3"
    local files_per_folder="$4"
    local file_pattern="$5"
    local file_size="$6"

    if [[ ! "$base_path" =~ ^/ ]]; then
        validation_error "первый аргумент должен быть абсолютным путём."
        return 1
    fi

    if [[ "$base_path" == "/" ]]; then
        validation_error "корневой каталог / нельзя использовать как рабочий путь."
        return 1
    fi

    if [[ ! "$folder_count" =~ ^[1-9][0-9]*$ ]]; then
        validation_error "количество папок должно быть положительным целым числом."
        return 1
    fi

    if [[ ! "$folder_letters" =~ ^[A-Za-z]{1,7}$ ]]; then
        validation_error "буквы для папок должны содержать от 1 до 7 английских букв."
        return 1
    fi

    if [[ ! "$files_per_folder" =~ ^[1-9][0-9]*$ ]]; then
        validation_error "количество файлов должно быть положительным целым числом."
        return 1
    fi

    if [[ ! "$file_pattern" =~ ^[A-Za-z]{1,7}\.[A-Za-z]{1,3}$ ]]; then
        validation_error "шаблон файла должен иметь вид name.ext: имя — 1–7 английских букв, расширение — 1–3."
        return 1
    fi

    if [[ ! "$file_size" =~ ^([1-9][0-9]?|100)kb$ ]]; then
        validation_error "размер файла должен иметь формат Nkb, где N — от 1 до 100."
        return 1
    fi

    return 0
}

# Allows this file to be tested separately from main.sh.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    validate_args "$@"
fi
