#!/bin/bash
# download.sh: Resilient file download helper for setup and validation scripts.
#
# Provides _download() which wraps curl with retry and timeout handling.
#
# Source this file after output.sh:
#   # shellcheck source=script/.lib/download.sh
#   source "$SCRIPT_DIR/.lib/download.sh"

# _download URL DEST
# Downloads a file with timeout and retry (3 attempts, exponential back-off).
#
# Retry policy: up to 3 attempts with doubling back-off (2 s → 4 s).
# Timeouts:     10 s to establish a connection, 60 s for the full transfer.
#
# Returns 0 on success, 1 if all attempts fail.
_download() {
    local url="$1" dest="$2" attempt max_attempts delay
    max_attempts=3
    delay=2
    for ((attempt = 1; attempt <= max_attempts; attempt++)); do
        if curl -fsSL \
            --connect-timeout 10 \
            --max-time 60 \
            --retry 0 \
            "$url" -o "$dest"; then
            return 0
        fi
        if ((attempt < max_attempts)); then
            log_warning "Download failed (attempt ${attempt}/${max_attempts}): ${url##*/} — retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * 2))
        fi
    done
    log_error "Download failed after ${max_attempts} attempts: $url"
    return 1
}
