#!/bin/bash

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/validation.sh"
source "$SCRIPT_DIR/input.sh"
source "$SCRIPT_DIR/cleanup.sh"

main() {
    if ! validate_mode "$@"; then
        return 1
    fi

    local mode="$1"
    local -a targets=()

    case "$mode" in
        1)
            local log_file

            if ! log_file="$(prompt_log_file)"; then
                return 1
            fi

            mapfile -t targets < <(collect_targets_from_log "$log_file")
            ;;
        2)
            local range_output
            local -a date_range

            if ! range_output="$(prompt_datetime_range)"; then
                return 1
            fi

            mapfile -t date_range <<< "$range_output"
            mapfile -t targets < <(
                collect_targets_by_time "${date_range[0]}" "${date_range[1]}"
            )
            ;;
        3)
            local mask

            if ! mask="$(prompt_name_mask)"; then
                return 1
            fi

            mapfile -t targets < <(collect_targets_by_mask "$mask")
            ;;
    esac

    if (( ${#targets[@]} == 0 )); then
        echo "Подходящие объекты не найдены."
        return 0
    fi

    print_cleanup_targets "${targets[@]}"

    if ! request_confirmation; then
        return 0
    fi

    if ! delete_cleanup_targets "${targets[@]}"; then
        return 1
    fi

    echo "Очистка завершена."
}

main "$@"
