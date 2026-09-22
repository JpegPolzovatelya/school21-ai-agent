#!/bin/bash

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly LOGS_DIRECTORY="$SCRIPT_DIR/../04"
readonly REPORT_FILE="$SCRIPT_DIR/report.html"
readonly SERVER_PORT=8080

source "$SCRIPT_DIR/validation.sh"
source "$SCRIPT_DIR/report.sh"
source "$SCRIPT_DIR/server.sh"

main() {
    validate_args "$@" || return 1
    validate_dependencies || return 1
    collect_log_files "$LOGS_DIRECTORY" || return 1

    generate_report "$REPORT_FILE" "${LOG_FILES[@]}" || return 1
    serve_report "$SCRIPT_DIR" "$SERVER_PORT"
}

main "$@"
