#!/bin/bash
# Output formatting library for consistent script styling
# Source this file in your scripts with: source "$(dirname "$0")/../.lib/output.sh"
# shellcheck disable=SC2034  # All variables in this library are used by sourcing scripts

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly BOLD='\033[1m'
readonly DIM='\033[2m'
readonly NC='\033[0m' # No Color

# Unicode symbols (work in most modern terminals)
readonly CHECK='✓'
readonly CROSS='✗'
readonly ARROW='→'
readonly INFO='ℹ'
readonly WARNING='⚠'
# shellcheck disable=SC2034  # These symbols are available to sourcing scripts
readonly ROCKET='🚀'
readonly PACKAGE='📦'
readonly WRENCH='🔧'
readonly SPARKLES='✨'
readonly BUG='🐛'
readonly BOOKS='📚'

# Formatted output functions
log_header() {
    printf "\n%b==> %b%b\n" "$BOLD$BLUE" "$1" "$NC"
}

log_success() {
    printf "%b%s %b%b\n" "$GREEN" "$CHECK" "$1" "$NC"
}

log_error() {
    printf "%b%s %b%b\n" "$RED" "$CROSS" "$1" "$NC" >&2
}

log_warning() {
    printf "%b%s %b%b\n" "$YELLOW" "$WARNING" "$1" "$NC"
}

log_info() {
    printf "%b%s %b%b\n" "$CYAN" "$INFO" "$1" "$NC"
}

log_step() {
    printf "    %b%s%b %b\n" "$DIM" "$ARROW" "$NC" "$1"
}

log_result() {
    local status=$1
    shift
    if [[ $status -eq 0 ]]; then
        printf "    %b%s %s%b\n" "$GREEN" "$CHECK" "$*" "$NC"
    else
        printf "    %b%s %s%b\n" "$RED" "$CROSS" "$*" "$NC"
    fi
}

# Separator lines
log_separator() {
    printf "%b%s%b\n" "$DIM" "────────────────────────────────────────────────────────────" "$NC"
}

# Exit with error message
die() {
    log_error "$1"
    exit "${2:-1}"
}

# Check command availability
require_command() {
    local cmd=$1
    local install_hint=${2:-""}

    if ! command -v "$cmd" >/dev/null 2>&1; then
        log_error "Required command not found: $cmd"
        if [[ -n $install_hint ]]; then
            log_info "Install with: $install_hint"
        fi
        exit 1
    fi
}

# Activate the Home Assistant virtual environment if not already active.
# Silently skips when VIRTUAL_ENV is already set (e.g. in CI or nested calls).
activate_venv() {
    if [[ -n ${VIRTUAL_ENV:-} ]]; then
        return 0
    fi
    log_header "Activating virtual environment"
    # shellcheck source=/dev/null
    if [[ -f "$PWD/.venv/bin/activate" ]]; then
        source "$PWD/.venv/bin/activate"
    elif [[ -f "$HOME/ha-venv/bin/activate" ]]; then
        source "$HOME/ha-venv/bin/activate"
    elif [[ -f "$PWD/.local/ha-venv/bin/activate" ]]; then
        source "$PWD/.local/ha-venv/bin/activate"
    elif [[ -f "$HOME/.local/ha-venv/bin/activate" ]]; then
        source "$HOME/.local/ha-venv/bin/activate"
    else
        log_error "Virtual environment not found. Run: script/setup/bootstrap or uv sync --all-extras"
        exit 1
    fi
}

# Run a user-defined hook script if it exists.
# Hooks live in script/user/<name>.<phase>.sh and are sourced (not executed),
# so they can read and set variables in the calling script's environment.
#
# Usage:  run_hook <script-name> <phase>
# Phases: pre | post
#
# Example — in script/develop:
#   run_hook "develop" "pre"
#
# The user creates script/user/develop.pre.sh to customize behavior.
# SCRIPT_DIR must be set in the calling script before sourcing output.sh.
run_hook() {
    local script_name="$1"
    local phase="$2"
    local hook_file="script/hooks/${script_name}.${phase}.sh"
    if [[ -f "$hook_file" ]]; then
        log_info "Running hook: script/hooks/${script_name}.${phase}.sh"
        # shellcheck source=/dev/null
        source "$hook_file"
    fi
}
