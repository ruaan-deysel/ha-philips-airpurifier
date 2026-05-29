"""Structured diagnostic logging for Philips AirPurifier."""

from __future__ import annotations

from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
import json
import logging
import traceback
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DEBUG_LOG_FILE = "philips_airpurifier_debug.jsonl"


def package_version(package: str) -> str | None:
    """Return an installed package version, if available."""
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def exception_data(err: BaseException) -> dict[str, str]:
    """Return machine-readable exception details."""
    return {
        "exception_type": type(err).__name__,
        "exception": str(err),
        "traceback": "".join(traceback.format_exception(type(err), err, err.__traceback__)),
    }


def status_data(status: dict[str, Any]) -> dict[str, Any]:
    """Return status payload details for diagnostics."""
    return {
        "status": status,
        "status_key_count": len(status),
        "status_keys": sorted(str(key) for key in status),
    }


def async_debug_event(hass: HomeAssistant, event: str, **fields: Any) -> None:
    """Schedule a structured diagnostic event write."""
    record = {
        "ts": datetime.now(UTC).isoformat(),
        "event": event,
        **fields,
    }
    line = json.dumps(record, default=str, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    path = hass.config.path(DEBUG_LOG_FILE)

    try:
        hass.async_create_background_task(
            hass.async_add_executor_job(_append_line, path, line),
            f"philips_airpurifier_debug_log_{event}",
        )
    except Exception:
        _LOGGER.debug("Failed to schedule Philips AirPurifier debug log write", exc_info=True)


def _append_line(path: str, line: str) -> None:
    """Append a JSONL line to the debug log."""
    with open(path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{line}\n")
