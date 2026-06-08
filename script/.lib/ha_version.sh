#!/bin/bash
# ha_version.sh: Home Assistant version resolution for setup and validation scripts.
#
# Provides resolve_ha_version() which resolves flexible version specifiers to
# concrete version numbers via PyPI.
#
# Source this file after output.sh:
#   # shellcheck source=script/.lib/ha_version.sh
#   source "$SCRIPT_DIR/.lib/ha_version.sh"
#
# Supported version formats:
#   "latest"          → newest stable release on PyPI
#   "beta"            → newest pre-release (alpha/beta/RC) on PyPI
#   "YEAR.MONTH"      → latest stable patch for that month on PyPI
#   "YEAR.MONTH.N"    → returned as-is (explicit stable pin, e.g. 2026.4.0, 2026.4.2)
#   "YEAR.MONTH.NbM"  → returned as-is (explicit pre-release pin, e.g. 2026.4.0b1)
#   "YEAR.MONTH.NrcM" → returned as-is (explicit release-candidate pin)
#
# Note: Callers that wish to treat YEAR.MONTH.0 as "latest patch" (e.g. when
# reading from hacs.json) should strip the .0 before calling this function.

# _PYPI_JSON_CACHE holds the raw PyPI JSON after the first successful fetch so
# that multiple resolve_ha_version calls in the same shell session only hit the
# network once.
_PYPI_JSON_CACHE=""

# _pypi_populate_cache
#
# Fetches the homeassistant PyPI JSON with retry and timeout handling and stores
# it in _PYPI_JSON_CACHE.  Runs in the CURRENT shell (not a subshell) so the
# cache variable is visible to the caller after the function returns.
#
# Retry policy: up to 3 attempts with doubling back-off (2 s → 4 s).
# Timeouts:     10 s to establish a connection, 30 s for the full transfer.
#
# Returns 0 if the cache is populated (either from a prior call or a fresh
# fetch), 1 if all attempts fail.
_pypi_populate_cache() {
    [[ -n "$_PYPI_JSON_CACHE" ]] && return 0

    local attempt max_attempts delay output
    max_attempts=3
    delay=2

    for ((attempt = 1; attempt <= max_attempts; attempt++)); do
        if output=$(curl -fsSL \
            --connect-timeout 10 \
            --max-time 30 \
            https://pypi.org/pypi/homeassistant/json); then
            _PYPI_JSON_CACHE="$output"
            return 0
        fi
        if ((attempt < max_attempts)); then
            log_warning "PyPI request failed (attempt ${attempt}/${max_attempts}), retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * 2))
        fi
    done

    log_error "Failed to reach PyPI after ${max_attempts} attempts"
    return 1
}

# _pypi_sort_key VERSION
#
# Emits a zero-padded sort key so pre-releases (a < b < rc) sort before the
# corresponding stable release without requiring external Python packages.
# Used internally; not intended to be called directly.
_PYPI_SORT_KEY_PY='
import sys, re
def key(v):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)((?:a|b|rc)\d+)?$", v)
    if not m:
        return (0, 0, 0, 3, 0)
    year, month, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    pre = m.group(4) or ""
    pm = re.match(r"^(a|b|rc)(\d+)$", pre) if pre else None
    prank = {"a": 0, "b": 1, "rc": 2}.get(pm.group(1), 3) if pm else 3
    pnum  = int(pm.group(2)) if pm else 0
    return (year, month, patch, prank, pnum)
versions = [v.strip() for v in sys.stdin]
print(sorted(versions, key=key)[-1] if versions else "")
'

# resolve_ha_version OUTPUT_VAR INPUT_VERSION
#
# Resolves a Home Assistant version specifier and stores the result in OUTPUT_VAR.
# Returns 1 and logs an error if PyPI resolution fails.
#
# Usage:
#   resolve_ha_version HA_VERSION "2026.4"      # → e.g., "2026.4.3"
#   resolve_ha_version HA_VERSION "2026.4.0"    # → "2026.4.0" (no-op, explicit pin)
#   resolve_ha_version HA_VERSION "latest"      # → newest stable release
#   resolve_ha_version HA_VERSION "beta"        # → newest pre-release (a/b/rc)
#   resolve_ha_version HA_VERSION "2026.4.3"    # → "2026.4.3" (no-op)
#   resolve_ha_version HA_VERSION "2026.4.0b1"  # → "2026.4.0b1" (no-op)
resolve_ha_version() {
    # shellcheck disable=SC2178  # intentional nameref assignment
    local -n _rha_result="$1"
    local version="$2"
    local resolved

    # "latest" → newest stable release on PyPI (info.version skips pre-releases)
    if [[ "$version" == "latest" ]]; then
        log_info "Resolving latest Home Assistant version via PyPI..."
        _pypi_populate_cache || return 1
        resolved=$(printf '%s' "$_PYPI_JSON_CACHE" |
            python3 -c 'import sys, json; print(json.load(sys.stdin)["info"]["version"])')
        if [[ -z "$resolved" ]]; then
            log_error "Failed to resolve latest Home Assistant version from PyPI"
            return 1
        fi
        log_info "Resolved to: ${resolved}"
        _rha_result="$resolved"
        return 0
    fi

    # "beta" → newest pre-release (alpha/beta/RC) on PyPI
    if [[ "$version" == "beta" ]]; then
        log_info "Resolving latest Home Assistant pre-release version via PyPI..."
        _pypi_populate_cache || return 1
        resolved=$(printf '%s' "$_PYPI_JSON_CACHE" |
            python3 -c 'import sys, json, re
data = json.load(sys.stdin)
pre = [v for v in data["releases"] if re.match(r"^\d{4}\.\d+\.\d+(a|b|rc)\d+$", v)]
sys.stdout.write("\n".join(pre))
' | python3 -c "$_PYPI_SORT_KEY_PY")
        if [[ -z "$resolved" ]]; then
            log_error "Failed to resolve latest Home Assistant pre-release version from PyPI"
            return 1
        fi
        log_info "Resolved to: ${resolved}"
        _rha_result="$resolved"
        return 0
    fi

    # "YEAR.MONTH" (no patch component) → latest stable patch for that minor
    if [[ "$version" =~ ^[0-9]{4}\.[0-9]+$ ]]; then
        local minor_prefix
        minor_prefix="${version}." # "2026.4" → "2026.4."
        log_info "Resolving latest patch for Home Assistant ${minor_prefix%.} via PyPI..."
        _pypi_populate_cache || return 1
        resolved=$(printf '%s' "$_PYPI_JSON_CACHE" |
            python3 -c 'import sys, json
prefix = sys.argv[1]
data = json.load(sys.stdin)
versions = sorted(
    [v for v in data["releases"] if v.startswith(prefix) and all(p.isdigit() for p in v.split("."))],
    key=lambda v: int(v.split(".")[-1])
)
print(versions[-1] if versions else "")
' "$minor_prefix")
        if [[ -z "$resolved" ]]; then
            log_error "Failed to resolve latest patch for Home Assistant ${minor_prefix%.} from PyPI"
            return 1
        fi
        log_info "Resolved to: ${resolved}"
        _rha_result="$resolved"
        return 0
    fi

    # Explicit version (pinned stable or pre-release) → pass through unchanged
    # Examples: "2026.4.3", "2026.4.0b1", "2026.4.0rc2"
    _rha_result="$version"
}
