"""Tests for Philips AirPurifier light platform."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.coordinator import (
    PhilipsAirPurifierCoordinator,
)
from custom_components.philips_airpurifier.light import PhilipsLight
from custom_components.philips_airpurifier.model import DeviceInformation
from homeassistant.components.light import ATTR_BRIGHTNESS
from homeassistant.components.light.const import DOMAIN as LIGHT_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import TEST_DEVICE_ID, TEST_MODEL

BACKLIGHT_ENTITY_ID = "light.living_room_display_backlight"
BRIGHTNESS_ENTITY_ID = "light.living_room_light_brightness"


async def test_light_setup(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that both light entities are created."""
    entity_registry = er.async_get(hass)

    backlight_entry = entity_registry.async_get(BACKLIGHT_ENTITY_ID)
    brightness_entry = entity_registry.async_get(BRIGHTNESS_ENTITY_ID)

    assert backlight_entry is not None
    assert backlight_entry.unique_id == f"{TEST_MODEL}-{TEST_DEVICE_ID}-uil"

    assert brightness_entry is not None
    assert brightness_entry.unique_id == f"{TEST_MODEL}-{TEST_DEVICE_ID}-aqil"


async def test_display_backlight_is_on(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that display backlight shows as on when uil='1'."""
    state = hass.states.get(BACKLIGHT_ENTITY_ID)
    assert state is not None
    assert state.state == "on"


async def test_display_backlight_turn_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning off display backlight."""
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: BACKLIGHT_ENTITY_ID},
        blocking=True,
    )

    # Verify set_control_values was called with uil="0"
    mock_coap_client.set_control_values.assert_called_once()
    call_args = mock_coap_client.set_control_values.call_args
    assert call_args[1]["data"] == {"uil": "0"}


async def test_display_backlight_turn_on(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning on display backlight."""
    # First turn it off
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: BACKLIGHT_ENTITY_ID},
        blocking=True,
    )

    mock_coap_client.set_control_values.reset_mock()

    # Now turn it on
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: BACKLIGHT_ENTITY_ID},
        blocking=True,
    )

    # Verify set_control_values was called with uil="1"
    mock_coap_client.set_control_values.assert_called_once()
    call_args = mock_coap_client.set_control_values.call_args
    assert call_args[1]["data"] == {"uil": "1"}


async def test_light_brightness_is_on(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that light brightness shows as on when aqil=100."""
    state = hass.states.get(BRIGHTNESS_ENTITY_ID)
    assert state is not None
    assert state.state == "on"


async def test_light_brightness_value(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that light brightness value is correctly calculated."""
    state = hass.states.get(BRIGHTNESS_ENTITY_ID)
    assert state is not None
    # aqil=100, on_value=100, brightness should be round(255 * 100 / 100) = 255
    assert state.attributes.get("brightness") == 255


async def test_light_brightness_turn_on_with_brightness(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning on light brightness with specific brightness value."""
    # Turn on with brightness 128 (50%)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: BRIGHTNESS_ENTITY_ID,
            ATTR_BRIGHTNESS: 128,
        },
        blocking=True,
    )

    # Verify set_control_values was called with aqil=50
    # Formula: round(100 * 128 / 255) = round(50.196) = 50
    mock_coap_client.set_control_values.assert_called_once()
    call_args = mock_coap_client.set_control_values.call_args
    assert call_args[1]["data"] == {"aqil": 50}


async def test_light_brightness_turn_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning off light brightness."""
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: BRIGHTNESS_ENTITY_ID},
        blocking=True,
    )

    # Verify set_control_values was called with aqil=0
    mock_coap_client.set_control_values.assert_called_once()
    call_args = mock_coap_client.set_control_values.call_args
    assert call_args[1]["data"] == {"aqil": 0}


async def test_light_brightness_turn_on_full_brightness(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning on light brightness to full brightness."""
    # First turn it off
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: BRIGHTNESS_ENTITY_ID},
        blocking=True,
    )

    mock_coap_client.set_control_values.reset_mock()

    # Turn on with brightness 255 (100%)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: BRIGHTNESS_ENTITY_ID,
            ATTR_BRIGHTNESS: 255,
        },
        blocking=True,
    )

    # Verify set_control_values was called with aqil=100
    # Formula: round(100 * 255 / 255) = 100
    mock_coap_client.set_control_values.assert_called_once()
    call_args = mock_coap_client.set_control_values.call_args
    assert call_args[1]["data"] == {"aqil": 100}


async def test_light_brightness_turn_on_without_brightness(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning on light brightness without specifying brightness."""
    # First turn it off
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: BRIGHTNESS_ENTITY_ID},
        blocking=True,
    )

    mock_coap_client.set_control_values.reset_mock()

    # Turn on without brightness parameter (should use on_value=100)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: BRIGHTNESS_ENTITY_ID},
        blocking=True,
    )

    # Verify set_control_values was called with aqil=100
    mock_coap_client.set_control_values.assert_called_once()
    call_args = mock_coap_client.set_control_values.call_args
    assert call_args[1]["data"] == {"aqil": 100}


async def test_display_backlight_color_mode(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that display backlight has ONOFF color mode."""
    state = hass.states.get(BACKLIGHT_ENTITY_ID)
    assert state is not None
    assert state.attributes.get("color_mode") == "onoff"
    assert state.attributes.get("supported_color_modes") == ["onoff"]


async def test_light_brightness_color_mode(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that light brightness has BRIGHTNESS color mode."""
    state = hass.states.get(BRIGHTNESS_ENTITY_ID)
    assert state is not None
    assert state.attributes.get("color_mode") == "brightness"
    assert state.attributes.get("supported_color_modes") == ["brightness"]


def _make_light_entity(kind: str, value: int) -> tuple[PhilipsLight, PhilipsAirPurifierCoordinator]:
    """Create a light entity with mocked coordinator for direct branch testing."""
    coordinator = PhilipsAirPurifierCoordinator(
        AsyncMock(),
        AsyncMock(),
        "192.168.1.130",
        DeviceInformation(
            model="AC3858/51",
            name="Light Branch",
            device_id="light-branch-id",
            host="192.168.1.130",
        ),
    )
    coordinator.data = {kind.partition("#")[0]: value}
    coordinator.async_set_control_value = AsyncMock()
    entity = PhilipsLight(coordinator, kind)
    return entity, coordinator


async def test_light_dimmable_auto_effect_branch() -> None:
    """Test brightness returns None when auto effect is active."""
    entity, _ = _make_light_entity("D03105#1", 101)
    entity._attr_effect = "auto"
    assert entity.brightness is None


async def test_light_dimmable_brightness_branches() -> None:
    """Test brightness logic for off/medium/on conversion."""
    entity, coordinator = _make_light_entity("D03105#1", 0)
    assert entity.brightness == 0

    coordinator.data["D03105"] = 115
    assert entity.brightness == 128

    coordinator.data["D03105"] = 123
    assert entity.brightness == 255


async def test_light_turn_on_effect_medium_and_default() -> None:
    """Test turn_on branches for effect, medium brightness, and default on."""
    entity, coordinator = _make_light_entity("D03105#1", 0)
    entity._handle_coordinator_update = lambda: None

    await entity.async_turn_on(effect="auto")
    coordinator.async_set_control_value.assert_awaited_with("D03105", 101)

    coordinator.async_set_control_value.reset_mock()
    await entity.async_turn_on(brightness=100)
    coordinator.async_set_control_value.assert_awaited_with("D03105", 115)

    coordinator.async_set_control_value.reset_mock()
    await entity.async_turn_on()
    coordinator.async_set_control_value.assert_awaited_with("D03105", 123)
