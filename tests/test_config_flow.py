"""Tests for Philips AirPurifier config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.const import (
    CONF_DEVICE_ID,
    CONF_MODEL,
    CONF_STATUS,
    DOMAIN,
    PhilipsApi,
)
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .const import (
    MOCK_STATUS_GEN1,
    TEST_DEVICE_ID,
    TEST_HOST,
    TEST_MAC,
    TEST_MODEL,
    TEST_NAME,
)


async def test_user_flow_success(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test successful user flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: TEST_HOST},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{TEST_MODEL} {TEST_NAME}"
    assert result["data"][CONF_HOST] == TEST_HOST
    assert result["data"][CONF_MODEL] == TEST_MODEL
    assert result["data"][CONF_NAME] == TEST_NAME
    assert result["data"][CONF_DEVICE_ID] == TEST_DEVICE_ID
    assert result["data"][CONF_STATUS] == MOCK_STATUS_GEN1


async def test_user_flow_invalid_host(hass: HomeAssistant) -> None:
    """Test user flow with invalid host."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "invalid host!@#"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_HOST: "host"}


async def test_user_flow_timeout(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test user flow when connection times out."""
    mock_coap_client_config_flow.get_status.side_effect = TimeoutError

    # Also make the CoAPClient.create timeout by patching it on the class mock
    # Actually, the timeout wraps the create+get_status calls. We need the
    # TimeoutManager's async_timeout to raise TimeoutError.
    # The simplest approach: make CoAPClient.create raise TimeoutError
    from unittest.mock import patch

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        mock_cls.create = AsyncMock(side_effect=TimeoutError)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "timeout"


async def test_user_flow_unknown_error(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test user flow when connection fails with unknown error.

    Generic exceptions are wrapped as ConfigEntryNotReady, then caught
    and shown as errors[CONF_HOST] = "connect".
    """
    mock_coap_client_config_flow.get_status.side_effect = Exception("Unknown error")

    # The exception happens inside the inner try block (not the TimeoutManager),
    # so it gets caught as a generic Exception -> ConfigEntryNotReady -> "connect"
    # But we need to make sure it doesn't get caught by TimeoutError first.
    # Since get_status raises Exception (not TimeoutError), it goes to the
    # `except Exception` branch -> raises ConfigEntryNotReady -> outer except catches it.
    from unittest.mock import patch

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(side_effect=Exception("Unknown error"))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {CONF_HOST: "connect"}


async def test_user_flow_model_unsupported(
    hass: HomeAssistant,
) -> None:
    """Test user flow with unsupported model."""
    unsupported_status = MOCK_STATUS_GEN1.copy()
    unsupported_status["modelid"] = "UNSUPPORTED_MODEL"

    from unittest.mock import patch

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(unsupported_status, 60))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "model_unsupported"


async def test_user_flow_model_family_supported(
    hass: HomeAssistant,
) -> None:
    """Test user flow accepts AC0650/10 via AC0650 family fallback."""
    ac0650_status = MOCK_STATUS_GEN1.copy()
    ac0650_status["modelid"] = "AC0650/10"

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(ac0650_status, 60))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_MODEL] == "AC0650"


async def test_user_flow_already_configured(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test user flow when device is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.200",
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_GEN1,
        },
        unique_id=TEST_DEVICE_ID,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: TEST_HOST},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_dhcp_discovery_success(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test successful DHCP discovery flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip=TEST_HOST,
            macaddress=TEST_MAC,
            hostname="philips-air",
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        "model": TEST_MODEL,
        "name": TEST_NAME,
    }

    # Confirm the device
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"{TEST_MODEL} {TEST_NAME}"
    assert result["data"][CONF_HOST] == TEST_HOST
    assert result["data"][CONF_MODEL] == TEST_MODEL
    assert result["data"][CONF_NAME] == TEST_NAME
    assert result["data"][CONF_DEVICE_ID] == TEST_DEVICE_ID
    assert result["data"][CONF_STATUS] == MOCK_STATUS_GEN1


async def test_dhcp_discovery_timeout(hass: HomeAssistant) -> None:
    """Test DHCP discovery with timeout aborts as model_unsupported."""
    from unittest.mock import patch

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        mock_cls.create = AsyncMock(side_effect=TimeoutError)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=TEST_HOST,
                macaddress=TEST_MAC,
                hostname="philips-air",
            ),
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "model_unsupported"


async def test_dhcp_discovery_model_unsupported(hass: HomeAssistant) -> None:
    """Test DHCP discovery with unsupported model."""
    unsupported_status = MOCK_STATUS_GEN1.copy()
    unsupported_status["modelid"] = "UNSUPPORTED_MODEL"

    from unittest.mock import patch

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(unsupported_status, 60))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=TEST_HOST,
                macaddress=TEST_MAC,
                hostname="philips-air",
            ),
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "model_unsupported"


async def test_dhcp_discovery_already_configured(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test DHCP discovery when device is already configured - should update host."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.200",
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_GEN1,
        },
        unique_id=TEST_DEVICE_ID,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip=TEST_HOST,
            macaddress=TEST_MAC,
            hostname="philips-air",
        ),
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    # Check that the host was updated
    assert entry.data[CONF_HOST] == TEST_HOST


async def test_dhcp_discovery_unknown_error(hass: HomeAssistant) -> None:
    """Test DHCP discovery with unknown error raises ConfigEntryNotReady."""
    from unittest.mock import patch

    from homeassistant import exceptions

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(side_effect=Exception("Unknown error"))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        with pytest.raises(exceptions.ConfigEntryNotReady):
            await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_DHCP},
                data=DhcpServiceInfo(
                    ip=TEST_HOST,
                    macaddress=TEST_MAC,
                    hostname="philips-air",
                ),
            )


async def test_reconfigure_flow_success(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test successful reconfigure flow updates host for same device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.200",
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_GEN1,
        },
        unique_id=TEST_DEVICE_ID,
    )
    entry.add_to_hass(hass)

    with patch.object(hass.config_entries, "async_reload", new=AsyncMock(return_value=True)) as reload_mock:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_HOST] == TEST_HOST
    reload_mock.assert_awaited_once_with(entry.entry_id)


async def test_reconfigure_flow_invalid_host(
    hass: HomeAssistant,
) -> None:
    """Test reconfigure flow rejects invalid host."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: TEST_HOST,
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_GEN1,
        },
        unique_id=TEST_DEVICE_ID,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "invalid host!@#"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {CONF_HOST: "host"}


async def test_reconfigure_flow_cannot_connect(
    hass: HomeAssistant,
) -> None:
    """Test reconfigure flow shows cannot_connect on status fetch errors."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: TEST_HOST,
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_GEN1,
        },
        unique_id=TEST_DEVICE_ID,
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        mock_cls.create = AsyncMock(side_effect=TimeoutError)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.1.201"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {CONF_HOST: "cannot_connect"}


async def test_reconfigure_flow_config_entry_not_ready(
    hass: HomeAssistant,
) -> None:
    """Test reconfigure flow shows cannot_connect on ConfigEntryNotReady."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: TEST_HOST,
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_GEN1,
        },
        unique_id=TEST_DEVICE_ID,
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(side_effect=Exception("Unknown error"))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.1.201"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {CONF_HOST: "cannot_connect"}


async def test_reconfigure_flow_different_device_abort(
    hass: HomeAssistant,
) -> None:
    """Test reconfigure flow aborts when host belongs to a different device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: TEST_HOST,
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_GEN1,
        },
        unique_id=TEST_DEVICE_ID,
    )
    entry.add_to_hass(hass)

    other_status = {**MOCK_STATUS_GEN1, PhilipsApi.DEVICE_ID: "different-device-id"}

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(other_status, 60))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.168.1.202"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "different_device"


async def test_reconfigure_flow_unknown_entry_id_aborts(
    hass: HomeAssistant,
) -> None:
    """Test reconfigure flow aborts if entry_id does not exist."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_RECONFIGURE, "entry_id": "missing-entry-id"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_confirm_step(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test the confirm step after DHCP discovery."""
    # Start DHCP discovery
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip=TEST_HOST,
            macaddress=TEST_MAC,
            hostname="philips-air",
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert "model" in result["description_placeholders"]
    assert "name" in result["description_placeholders"]

    # Confirm
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_host_valid_ipv4(hass: HomeAssistant) -> None:
    """Test that valid IPv4 addresses are accepted."""
    from custom_components.philips_airpurifier.config_flow import host_valid

    assert host_valid("192.168.1.1") is True
    assert host_valid("10.0.0.1") is True
    assert host_valid("172.16.0.1") is True


async def test_host_valid_ipv6(hass: HomeAssistant) -> None:
    """Test that valid IPv6 addresses are accepted."""
    from custom_components.philips_airpurifier.config_flow import host_valid

    assert host_valid("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
    assert host_valid("::1") is True
    assert host_valid("fe80::1") is True


async def test_host_valid_hostname(hass: HomeAssistant) -> None:
    """Test that valid hostnames are accepted."""
    from custom_components.philips_airpurifier.config_flow import host_valid

    assert host_valid("philips-air") is True
    assert host_valid("philips.local") is True
    assert host_valid("my-device-123") is True


async def test_host_invalid(hass: HomeAssistant) -> None:
    """Test that invalid hosts are rejected."""
    from custom_components.philips_airpurifier.config_flow import host_valid

    assert host_valid("invalid host!") is False
    assert host_valid("host@name") is False
    assert host_valid("host#name") is False
    assert host_valid("") is False
    assert host_valid("host..name") is False  # Double dot means empty segment


async def test_user_flow_model_long_supported_branch(hass: HomeAssistant) -> None:
    """Test user flow resolves model via model_long key branch."""
    status = MOCK_STATUS_GEN1.copy()
    status["modelid"] = "SYNTH"
    status["WifiVersion"] = "LONGKEY@1.0.0"

    from unittest.mock import patch

    with (
        patch("custom_components.philips_airpurifier.config_flow.CoAPClient") as mock_cls,
        patch.dict(
            "custom_components.philips_airpurifier.config_flow.DEVICE_MODELS",
            {"SYNTH LONGKEY": object()},
            clear=False,
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(status, 60))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_MODEL] == "SYNTH LONGKEY"


async def test_dhcp_flow_model_family_supported_branch(hass: HomeAssistant) -> None:
    """Test DHCP flow resolves model via model_family key branch."""
    status = MOCK_STATUS_GEN1.copy()
    status["modelid"] = "FAM001-EXTRA"
    status["WifiVersion"] = "IRRELEVANT@1.0.0"

    from unittest.mock import patch

    with (
        patch("custom_components.philips_airpurifier.config_flow.CoAPClient") as mock_cls,
        patch.dict(
            "custom_components.philips_airpurifier.config_flow.DEVICE_MODELS",
            {"FAM001": object()},
            clear=False,
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(status, 60))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=TEST_HOST,
                macaddress=TEST_MAC,
                hostname="philips-air",
            ),
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"


async def test_dhcp_flow_model_long_supported_branch(hass: HomeAssistant) -> None:
    """Test DHCP flow resolves model via model_long key branch."""
    status = MOCK_STATUS_GEN1.copy()
    status["modelid"] = "DHCPX"
    status["WifiVersion"] = "DHCPLONG@2.0.0"

    from unittest.mock import patch

    with (
        patch("custom_components.philips_airpurifier.config_flow.CoAPClient") as mock_cls,
        patch.dict(
            "custom_components.philips_airpurifier.config_flow.DEVICE_MODELS",
            {"DHCPX DHCPLONG": object()},
            clear=False,
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(status, 60))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=TEST_HOST,
                macaddress=TEST_MAC,
                hostname="philips-air",
            ),
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"


async def test_user_flow_model_family_supported_branch(hass: HomeAssistant) -> None:
    """Test user flow resolves model via model_family key branch."""
    status = MOCK_STATUS_GEN1.copy()
    status["modelid"] = "USR123-EXT"
    status["WifiVersion"] = "WHATEVER@1.0.0"

    from unittest.mock import patch

    with (
        patch("custom_components.philips_airpurifier.config_flow.CoAPClient") as mock_cls,
        patch.dict(
            "custom_components.philips_airpurifier.config_flow.DEVICE_MODELS",
            {"USR123": object()},
            clear=False,
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(status, 60))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
