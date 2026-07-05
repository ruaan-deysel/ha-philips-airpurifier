"""Tests for Philips AirPurifier config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.const import (
    CONF_DEVICE_ID,
    CONF_MAC,
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
    TEST_MAC_FORMATTED,
    TEST_MODEL,
    TEST_NAME,
)


@pytest.fixture(autouse=True)
def _no_real_entry_setup() -> object:
    """Neutralize the entry setup that the test harness runs after a flow.

    Config-flow tests create real config entries; the harness then sets them up,
    which would otherwise instantiate a real CoAP client and open a network
    socket. Patching the integration's client (and the observe start) keeps that
    automatic setup offline without affecting the flow assertions.
    """
    client = AsyncMock()
    client.get_status = AsyncMock(return_value=(MOCK_STATUS_GEN1.copy(), 60))
    client.set_control_values = AsyncMock()
    client.set_control_value = AsyncMock()
    client.shutdown = AsyncMock()
    with (
        patch("custom_components.philips_airpurifier.CoAPClient") as mock_setup_client_cls,
        patch(
            "custom_components.philips_airpurifier.coordinator.PhilipsAirPurifierCoordinator._start_observing",
        ),
    ):
        mock_setup_client_cls.create = AsyncMock(return_value=client)
        mock_setup_client_cls.return_value = client
        yield


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
    assert result["errors"] == {CONF_HOST: "invalid_host"}


async def test_user_flow_timeout(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test user flow shows cannot_connect error when connection times out."""
    mock_coap_client_config_flow.get_status.side_effect = TimeoutError

    # The timeout wraps the create+get_status calls. The simplest approach:
    # make CoAPClient.create raise TimeoutError. The nudge fallback probes
    # sys/dev/info; stub it to fail so the flow falls back to cannot_connect.
    with (
        patch(
            "custom_components.philips_airpurifier.config_flow.CoAPClient",
        ) as mock_cls,
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_device_info",
            AsyncMock(side_effect=TimeoutError),
        ),
    ):
        mock_cls.create = AsyncMock(side_effect=TimeoutError)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {CONF_HOST: "cannot_connect"}


async def test_user_flow_status_nudge_fallback(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test user flow recovers via nudge when the status read times out.

    Devices like the CX7550 never answer a status read; the flow falls back to
    identifying the model via sys/dev/info and fetching status with a nudge.
    """
    cx7550_status = {
        PhilipsApi.NEW2_MODEL_ID: "CX7550/01",
        PhilipsApi.NEW2_NAME: "Büro",
        PhilipsApi.DEVICE_ID: TEST_DEVICE_ID,
        PhilipsApi.WIFI_VERSION: "AWS_Philips_AIR_Combo@86",
        PhilipsApi.NEW2_POWER: 1,
    }
    with (
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_status",
            AsyncMock(side_effect=TimeoutError),
        ),
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_device_info",
            AsyncMock(return_value={"modelid": "CX7550/01", "name": "Büro"}),
        ),
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_status_with_nudge",
            AsyncMock(return_value=cx7550_status),
        ),
        # Entry setup for a nudge device also fetches via nudge in the coordinator.
        patch(
            "custom_components.philips_airpurifier.coordinator.async_fetch_status_with_nudge",
            AsyncMock(return_value=cx7550_status),
        ),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_MODEL] == "CX7550"


async def test_user_flow_nudge_fetch_fails(
    hass: HomeAssistant,
) -> None:
    """Test the flow aborts cleanly when the nudge-based fetch fails."""
    with (
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_status",
            AsyncMock(side_effect=TimeoutError),
        ),
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_device_info",
            AsyncMock(return_value={"modelid": "CX7550/01", "name": "Büro"}),
        ),
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_status_with_nudge",
            AsyncMock(side_effect=Exception("nudge failed")),
        ),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_HOST: "cannot_connect"}


async def test_user_flow_nudge_not_supported_model(
    hass: HomeAssistant,
) -> None:
    """Test timeout + a non-nudge model falls back to cannot_connect."""
    with (
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_status",
            AsyncMock(side_effect=TimeoutError),
        ),
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_device_info",
            AsyncMock(return_value={"modelid": "AC3858/51", "name": "Living Room"}),
        ),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {CONF_HOST: "cannot_connect"}


async def test_user_flow_unknown_error(
    hass: HomeAssistant,
    mock_coap_client_config_flow: AsyncMock,
) -> None:
    """Test user flow when connection fails with unknown error.

    Generic exceptions are wrapped as CannotConnect, then caught
    and shown as errors[CONF_HOST] = "cannot_connect".
    """
    mock_coap_client_config_flow.get_status.side_effect = Exception("Unknown error")

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
        assert result["errors"] == {CONF_HOST: "cannot_connect"}


async def test_user_flow_model_unsupported(
    hass: HomeAssistant,
) -> None:
    """Test user flow with unsupported model."""
    unsupported_status = MOCK_STATUS_GEN1.copy()
    unsupported_status["modelid"] = "UNSUPPORTED_MODEL"

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


async def test_user_flow_model_family_supported_ac2210(
    hass: HomeAssistant,
) -> None:
    """Test user flow accepts AC2210/10 via AC2210 family fallback."""
    ac2210_status = MOCK_STATUS_GEN1.copy()
    ac2210_status["modelid"] = "AC2210/10"

    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(ac2210_status, 60))
        client.shutdown = AsyncMock()
        mock_cls.create = AsyncMock(return_value=client)

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_MODEL] == "AC2210"


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
    """Test DHCP discovery with timeout aborts as cannot_connect."""
    with (
        patch(
            "custom_components.philips_airpurifier.config_flow.CoAPClient",
        ) as mock_cls,
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_device_info",
            AsyncMock(side_effect=TimeoutError),
        ),
    ):
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
        assert result["reason"] == "cannot_connect"


async def test_dhcp_discovery_model_unsupported(hass: HomeAssistant) -> None:
    """Test DHCP discovery with unsupported model."""
    unsupported_status = MOCK_STATUS_GEN1.copy()
    unsupported_status["modelid"] = "UNSUPPORTED_MODEL"

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
    # Check that the host was updated and the MAC stored for future matching
    assert entry.data[CONF_HOST] == TEST_HOST
    assert entry.data[CONF_MAC] == TEST_MAC_FORMATTED


async def test_dhcp_discovery_mac_match_updates_host_without_probe(
    hass: HomeAssistant,
) -> None:
    """Test DHCP discovery of a known device (by MAC) with a new IP.

    The flow must update the stored host and abort without opening a CoAP
    connection: the device only serves a single client and may not even be
    reachable yet during an IP transition (issue #8).
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.200",
            CONF_MAC: TEST_MAC_FORMATTED,
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
        mock_cls.create = AsyncMock(side_effect=AssertionError("must not connect"))

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
    assert entry.data[CONF_HOST] == TEST_HOST
    mock_cls.create.assert_not_called()


async def test_dhcp_discovery_host_match_backfills_mac(
    hass: HomeAssistant,
) -> None:
    """Test DHCP discovery backfills the MAC on a legacy entry matched by host."""
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
        mock_cls.create = AsyncMock(side_effect=AssertionError("must not connect"))

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
    assert entry.data[CONF_MAC] == TEST_MAC_FORMATTED
    mock_cls.create.assert_not_called()


async def test_dhcp_discovery_known_device_unchanged_no_reload(
    hass: HomeAssistant,
) -> None:
    """Test DHCP discovery of a known device with unchanged data does not reload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: TEST_HOST,
            CONF_MAC: TEST_MAC_FORMATTED,
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_GEN1,
        },
        unique_id=TEST_DEVICE_ID,
    )
    entry.add_to_hass(hass)

    with patch.object(hass.config_entries, "async_schedule_reload") as reload_mock:
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
    reload_mock.assert_not_called()


async def test_user_flow_known_host_aborts_without_probe(
    hass: HomeAssistant,
) -> None:
    """Test user flow aborts for an already configured host without probing it."""
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
        mock_cls.create = AsyncMock(side_effect=AssertionError("must not connect"))

        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_cls.create.assert_not_called()


async def test_dhcp_discovery_unknown_error(hass: HomeAssistant) -> None:
    """Test DHCP discovery with unknown error aborts as cannot_connect."""
    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(side_effect=Exception("Unknown error"))
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
        assert result["reason"] == "cannot_connect"


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
    assert result["errors"] == {CONF_HOST: "invalid_host"}


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

    with (
        patch(
            "custom_components.philips_airpurifier.config_flow.CoAPClient",
        ) as mock_cls,
        patch(
            "custom_components.philips_airpurifier.config_flow.async_fetch_device_info",
            AsyncMock(side_effect=TimeoutError),
        ),
    ):
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
