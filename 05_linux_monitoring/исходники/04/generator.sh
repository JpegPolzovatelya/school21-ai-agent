#!/bin/bash

# Выводит случайное целое число от minimum до maximum включительно.
random_between() {
    local minimum="$1"
    local maximum="$2"

    printf '%s' $((RANDOM % (maximum - minimum + 1) + minimum))
}

# Выводит один случайный элемент из переданного списка.
random_element() {
    local -a values=("$@")

    printf '%s' "${values[RANDOM % ${#values[@]}]}"
}

# Генерирует корректный IPv4-адрес: каждый октет находится в диапазоне 0–255.
generate_ip() {
    printf '%s.%s.%s.%s' \
        "$(random_between 1 223)" \
        "$(random_between 0 255)" \
        "$(random_between 0 255)" \
        "$(random_between 1 254)"
}

# Преобразует Unix-время в формат даты nginx, например 04/Jul/2026:12:30:15 +0300.
format_log_datetime() {
    local timestamp="$1"

    LC_TIME=C date -d "@$timestamp" '+%d/%b/%Y:%H:%M:%S %z'
}

# Формирует одну полную строку nginx в формате Combined Log Format.
generate_log_record() {
    local timestamp="$1"
    local ip
    local method
    local url
    local code
    local response_size
    local referer
    local user_agent
    local log_datetime

    ip="$(generate_ip)"
    method="$(random_element "${HTTP_METHODS[@]}")"
    url="$(random_element "${URLS[@]}")"
    code="$(random_element "${HTTP_CODES[@]}")"
    response_size="$(random_between 128 65535)"
    referer="$(random_element "${REFERERS[@]}")"
    user_agent="$(random_element "${USER_AGENTS[@]}")"
    log_datetime="$(format_log_datetime "$timestamp")"

    printf '%s - - [%s] "%s %s HTTP/1.1" %s %s "%s" "%s"\n' \
        "$ip" "$log_datetime" "$method" "$url" "$code" "$response_size" \
        "$referer" "$user_agent"
}
