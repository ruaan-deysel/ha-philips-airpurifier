"""Client helpers for Philips Air Purifier CoAP communication."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from philips_airctrl import CoAPClient

DEFAULT_CONNECT_TIMEOUT = 25
DEFAULT_STATUS_TIMEOUT = 20
DEFAULT_CONTROL_TIMEOUT = 20
DEFAULT_SHUTDOWN_TIMEOUT = 5


async def async_create_client(
    host: str,
    timeout: float = DEFAULT_CONNECT_TIMEOUT,
    create_client: Any | None = None,
) -> CoAPClient:
    """Create a CoAP client for a host with timeout protection."""
    creator = create_client or CoAPClient.create
    return await asyncio.wait_for(creator(host), timeout=timeout)


async def async_shutdown_client(
    client: CoAPClient,
    timeout: float = DEFAULT_SHUTDOWN_TIMEOUT,
) -> None:
    """Shut down a CoAP client without allowing cleanup to hang Home Assistant."""
    with contextlib.suppress(Exception):
        await asyncio.wait_for(client.shutdown(), timeout=timeout)


async def async_get_status(
    host: str,
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
    status_timeout: float = DEFAULT_STATUS_TIMEOUT,
    shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT,
    create_client: Any | None = None,
) -> tuple[dict[str, Any], int]:
    """Fetch current status using a temporary CoAP client and shut it down."""
    client = await async_create_client(host, timeout=connect_timeout, create_client=create_client)
    try:
        return await asyncio.wait_for(client.get_status(), timeout=status_timeout)
    finally:
        await async_shutdown_client(client, timeout=shutdown_timeout)


async def async_fetch_status(
    host: str,
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
    status_timeout: float = DEFAULT_STATUS_TIMEOUT,
    shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT,
    create_client: Any | None = None,
) -> dict[str, Any]:
    """Fetch current status using a temporary CoAP client and shut it down."""
    status, _ = await async_get_status(
        host,
        connect_timeout=connect_timeout,
        status_timeout=status_timeout,
        shutdown_timeout=shutdown_timeout,
        create_client=create_client,
    )
    return status


async def async_set_control_values(
    host: str,
    data: dict[str, Any],
    connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
    control_timeout: float = DEFAULT_CONTROL_TIMEOUT,
    shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT,
    create_client: Any | None = None,
) -> None:
    """Set control values using a temporary CoAP client and bounded waits."""
    client = await async_create_client(host, timeout=connect_timeout, create_client=create_client)
    try:
        result = await asyncio.wait_for(
            client.set_control_values(data=data),
            timeout=control_timeout,
        )
        if result is False:
            msg = f"Device at {host} rejected control update"
            raise RuntimeError(msg)
    finally:
        await async_shutdown_client(client, timeout=shutdown_timeout)
