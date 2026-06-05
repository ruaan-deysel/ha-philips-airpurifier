"""Client helpers for Philips Air Purifier CoAP communication."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from philips_airctrl import CoAPClient


async def async_create_client(
    host: str,
    timeout: float = 25,
    create_client: Any | None = None,
) -> CoAPClient:
    """Create a CoAP client for a host with timeout protection."""
    creator = create_client or CoAPClient.create
    return await asyncio.wait_for(creator(host), timeout=timeout)


async def async_fetch_status(
    host: str,
    connect_timeout: float = 30,
    status_timeout: float = 30,
    create_client: Any | None = None,
) -> dict[str, Any]:
    """Fetch current status using a temporary CoAP client and shut it down.

    Use this only for short-lived discovery/config-flow probes. The running
    coordinator uses its persistent client for bounded snapshots and one
    long-lived observation instead of creating ad hoc clients.
    """
    client = await async_create_client(host, timeout=connect_timeout, create_client=create_client)
    try:
        status, _ = await asyncio.wait_for(client.get_status(observe=False), timeout=status_timeout)
        return status
    finally:
        with contextlib.suppress(Exception):
            await client.shutdown()
