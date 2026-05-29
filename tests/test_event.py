"""Tests for Philips AirPurifier event platform."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from custom_components.philips_airpurifier.const import PhilipsApi
from custom_components.philips_airpurifier.event import (
    EVENT_CLEARED,
    EVENT_ERROR,
    EVENT_OUT_OF_WATER,
    PhilipsNotificationEvent,
    async_setup_entry,
)
from homeassistant.core import HomeAssistant

TEST_MODEL = "AC2729"
TEST_DEVICE_ID = "aabbccddeeff"


def _make_event_entity(initial: dict | None = None) -> tuple[PhilipsNotificationEvent, MagicMock]:
    """Return a notification event entity backed by a mock coordinator."""
    coordinator = MagicMock()
    coordinator.model = TEST_MODEL
    coordinator.device_id = TEST_DEVICE_ID
    coordinator.device_name = "Living Room"
    coordinator.mac = None
    coordinator.data = initial if initial is not None else {}

    entity = PhilipsNotificationEvent(coordinator)
    # Avoid touching the entity/state machine in these pure unit tests.
    entity.async_write_ha_state = MagicMock()  # type: ignore[method-assign]
    return entity, coordinator


async def test_setup_adds_entity_when_error_key_present(hass: HomeAssistant) -> None:
    """The entity is created only when the status exposes an error code key."""
    coordinator = MagicMock()
    coordinator.data = {PhilipsApi.ERROR_CODE: 0}
    coordinator.mac = None
    entry = MagicMock()
    entry.runtime_data = coordinator
    added: list = []

    await async_setup_entry(hass, entry, added.extend)
    assert len(added) == 1
    assert isinstance(added[0], PhilipsNotificationEvent)


async def test_setup_skips_entity_without_error_key(hass: HomeAssistant) -> None:
    """No entity is created when the device does not report an error code."""
    coordinator = MagicMock()
    coordinator.data = {"pwr": "1"}
    entry = MagicMock()
    entry.runtime_data = coordinator
    added: list = []

    await async_setup_entry(hass, entry, added.extend)
    assert added == []


def test_first_update_seeds_baseline_without_firing() -> None:
    """The first coordinator update records the code but fires no event."""
    entity, coordinator = _make_event_entity({PhilipsApi.ERROR_CODE: 49408})

    with patch.object(entity, "_trigger_event") as trigger:
        entity._handle_coordinator_update()

    trigger.assert_not_called()
    assert entity._last_code == 49408


def test_error_event_fired_on_change() -> None:
    """A new non-zero, non-water error fires an 'error' event with details."""
    entity, coordinator = _make_event_entity({PhilipsApi.ERROR_CODE: 0})
    entity._handle_coordinator_update()  # seed baseline at 0

    coordinator.data = {PhilipsApi.ERROR_CODE: 4}
    with patch.object(entity, "_trigger_event") as trigger:
        entity._handle_coordinator_update()

    trigger.assert_called_once_with(EVENT_ERROR, {"code": 4, "source": PhilipsApi.ERROR_CODE})


def test_out_of_water_event_fired() -> None:
    """The out-of-water bit (bit 9) fires a dedicated event."""
    entity, coordinator = _make_event_entity({PhilipsApi.ERROR_CODE: 0})
    entity._handle_coordinator_update()

    coordinator.data = {PhilipsApi.ERROR_CODE: 256}  # bit 9 set
    with patch.object(entity, "_trigger_event") as trigger:
        entity._handle_coordinator_update()

    trigger.assert_called_once_with(EVENT_OUT_OF_WATER, {"code": 256, "source": PhilipsApi.ERROR_CODE})


def test_cleared_event_fired_when_code_returns_to_zero() -> None:
    """Returning to code 0 fires a 'cleared' event."""
    entity, coordinator = _make_event_entity({PhilipsApi.ERROR_CODE: 4})
    entity._handle_coordinator_update()  # baseline 4

    coordinator.data = {PhilipsApi.ERROR_CODE: 0}
    with patch.object(entity, "_trigger_event") as trigger:
        entity._handle_coordinator_update()

    trigger.assert_called_once_with(EVENT_CLEARED, {"code": 0, "source": PhilipsApi.ERROR_CODE})


def test_non_integer_code_is_treated_as_zero() -> None:
    """A non-numeric error code is coerced to 0 rather than raising."""
    entity, coordinator = _make_event_entity({PhilipsApi.ERROR_CODE: "n/a"})
    entity._handle_coordinator_update()
    assert entity._last_code == 0
