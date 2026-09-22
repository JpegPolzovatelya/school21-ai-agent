#!/bin/bash

readonly MIN_RECORDS=100
readonly MAX_RECORDS=1000
readonly SECONDS_PER_DAY=86400

# Создаёт один дневной лог с записями, отсортированными по времени.
generate_daily_log() {
    local day="$1"
    local output_file="$2"
    local record_count
    local day_start
    local index
    local interval_start
    local interval_end
    local timestamp

    record_count="$(random_between "$MIN_RECORDS" "$MAX_RECORDS")"
    day_start="$(date -d "$day 00:00:00" +%s)"

    if [[ ! "$day_start" =~ ^[0-9]+$ ]]; then
        echo "Ошибка: не удалось преобразовать дату $day." >&2
        return 1
    fi

    if ! : > "$output_file"; then
        echo "Ошибка: не удалось создать файл $output_file." >&2
        return 1
    fi

    # Делим сутки на интервалы и выбираем время внутри каждого интервала.
    # Поэтому каждая следующая запись гарантированно будет позже предыдущей.
    for ((index = 0; index < record_count; index++)); do
        interval_start=$((index * SECONDS_PER_DAY / record_count))
        interval_end=$(((index + 1) * SECONDS_PER_DAY / record_count - 1))
        timestamp=$((day_start + interval_start + RANDOM % (interval_end - interval_start + 1)))

        if ! generate_log_record "$timestamp" >> "$output_file"; then
            echo "Ошибка: не удалось записать данные в $output_file." >&2
            return 1
        fi
    done

    printf 'Создан %s: %s записей\n' "$output_file" "$record_count"
}
