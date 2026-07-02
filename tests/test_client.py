"""Tests for the CoAP client helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.philips_airpurifier.client import (
    async_fetch_device_info,
    async_fetch_status_with_nudge,
)

_CLIENT = "custom_components.philips_airpurifier.client"


async def _aiter(items: list[Any]) -> AsyncIterator[Any]:
    """Yield the given items as an async iterator."""
    for item in items:
        yield item


async def _aiter_raises(exc: Exception) -> AsyncIterator[Any]:
    """Raise the given exception on first iteration (after yielding nothing)."""
    if False:  # pragma: no cover - makes this a generator without yielding
        yield None
    raise exc


async def test_async_fetch_device_info_returns_library_info() -> None:
    """Device info comes from CoAPClient.get_device_info with sync disabled."""
    info = {"modelid": "CX7550/01", "name": "Büro", "device_id": "abc"}
    client = MagicMock()
    client.get_device_info = AsyncMock(return_value=info)
    client.shutdown = AsyncMock()
    create = AsyncMock(return_value=client)

    result = await async_fetch_device_info("1.2.3.4", create_client=create)

    assert result == info
    create.assert_awaited_once_with("1.2.3.4", sync=False)
    client.shutdown.assert_awaited()


async def test_async_fetch_status_with_nudge_success() -> None:
    """Test the observe-plus-nudge fetch returns the first pushed status."""
    status = {"D01S05": "CX7550/01", "D03102": 1}
    client = MagicMock()
    client.observe_status = MagicMock(return_value=_aiter([status]))
    client.set_control_value = AsyncMock()
    client.shutdown = AsyncMock()

    with (
        patch(f"{_CLIENT}.async_create_client", AsyncMock(return_value=client)),
        patch(f"{_CLIENT}._NUDGE_REGISTER_DELAY", 0),
    ):
        result = await async_fetch_status_with_nudge("1.2.3.4", [("D03105", 0), ("D03105", 115)])

    assert result == status
    client.set_control_value.assert_awaited()
    client.shutdown.assert_awaited()


async def test_async_fetch_status_with_nudge_timeout() -> None:
    """Test the nudge fetch raises a descriptive TimeoutError when no push arrives."""
    client = MagicMock()
    client.observe_status = MagicMock(return_value=_aiter([]))
    client.set_control_value = AsyncMock()
    client.shutdown = AsyncMock()

    with (
        patch(f"{_CLIENT}.async_create_client", AsyncMock(return_value=client)),
        patch(f"{_CLIENT}._NUDGE_REGISTER_DELAY", 0),
        patch(f"{_CLIENT}._NUDGE_WAIT_TIMEOUT", 0.01),
        pytest.raises(TimeoutError, match="no status push from 1.2.3.4"),
    ):
        await async_fetch_status_with_nudge("1.2.3.4", [("D03105", 0)])

    client.shutdown.assert_awaited()


async def test_async_fetch_status_with_nudge_write_failure_is_logged() -> None:
    """A failing control write is swallowed; a later push still succeeds."""
    status = {"D01S05": "CX7550/01"}
    client = MagicMock()
    client.observe_status = MagicMock(return_value=_aiter([status]))
    client.set_control_value = AsyncMock(side_effect=RuntimeError("write rejected"))
    client.shutdown = AsyncMock()

    with (
        patch(f"{_CLIENT}.async_create_client", AsyncMock(return_value=client)),
        patch(f"{_CLIENT}._NUDGE_REGISTER_DELAY", 0),
    ):
        result = await async_fetch_status_with_nudge("1.2.3.4", [("D03105", 0)])

    assert result == status
    client.set_control_value.assert_awaited()
    client.shutdown.assert_awaited()


async def test_async_fetch_status_with_nudge_observe_error_is_logged() -> None:
    """An observe-stream error is swallowed and surfaces as a nudge timeout."""
    client = MagicMock()
    client.observe_status = MagicMock(return_value=_aiter_raises(RuntimeError("stream died")))
    client.set_control_value = AsyncMock()
    client.shutdown = AsyncMock()

    with (
        patch(f"{_CLIENT}.async_create_client", AsyncMock(return_value=client)),
        patch(f"{_CLIENT}._NUDGE_REGISTER_DELAY", 0),
        patch(f"{_CLIENT}._NUDGE_WAIT_TIMEOUT", 0.01),
        pytest.raises(TimeoutError, match="no status push from 1.2.3.4"),
    ):
        await async_fetch_status_with_nudge("1.2.3.4", [("D03105", 0)])

    client.shutdown.assert_awaited()
