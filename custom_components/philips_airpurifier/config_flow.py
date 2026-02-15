"""The Philips AirPurifier component."""

import ipaddress
import logging
import re
from typing import Any

from philips_airctrl import CoAPClient
import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .client import async_fetch_status
from .const import CONF_DEVICE_ID, CONF_MODEL, CONF_STATUS, DOMAIN, PhilipsApi
from .device_models import DEVICE_MODELS
from .helpers import extract_model, extract_name

_LOGGER = logging.getLogger(__name__)


def host_valid(host: str) -> bool:
    """Return True if hostname or IP address is valid."""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    disallowed = re.compile(r"[^a-zA-Z\d\-]")
    return all(x and not disallowed.search(x) for x in host.split("."))


class PhilipsAirPurifierConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Philips AirPurifier."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._host: str | None = None
        self._model: Any = None
        self._name: Any = None
        self._device_id: str | None = None
        self._wifi_version: Any = None
        self._status: Any = None

    def _get_schema(self, user_input: dict[str, Any]) -> vol.Schema:
        """Provide schema for user input."""
        return vol.Schema({vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): cv.string})

    async def _async_probe_host(self, host: str) -> dict[str, Any]:
        """Fetch status from host and validate basic connectivity."""
        if not host_valid(host):
            raise InvalidHost

        self._host = host
        _LOGGER.debug("trying to configure host: %s", self._host)

        try:
            _LOGGER.debug("trying to get status")
            status = await async_fetch_status(
                host,
                connect_timeout=30,
                status_timeout=30,
                create_client=CoAPClient.create,
            )
            _LOGGER.debug("got status")
            return status
        except TimeoutError:
            _LOGGER.warning(r"Timeout, host %s doesn't answer", self._host)
            raise
        except Exception as ex:
            _LOGGER.warning(r"Failed to connect: %s", ex)
            raise exceptions.ConfigEntryNotReady from ex

    async def async_step_dhcp(self, discovery_info: DhcpServiceInfo) -> ConfigFlowResult:
        """Handle initial step of auto discovery flow."""
        _LOGGER.debug("async_step_dhcp: called, found: %s", discovery_info)

        self._host = discovery_info.ip
        _LOGGER.debug("trying to configure host: %s", self._host)

        # let's try and connect to an AirPurifier
        try:
            _LOGGER.debug("trying to get status")
            status = await async_fetch_status(
                self._host,
                connect_timeout=30,
                status_timeout=30,
                create_client=CoAPClient.create,
            )
            _LOGGER.debug("got status")

            # get the status out of the queue
            _LOGGER.debug("status for host %s is: %s", self._host, status)

        except TimeoutError:
            _LOGGER.warning(
                r"Timeout, host %s looks like a Philips AirPurifier but doesn't answer, aborting",
                self._host,
            )
            return self.async_abort(reason="model_unsupported")

        except Exception as ex:
            _LOGGER.warning(r"Failed to connect: %s", ex)
            raise exceptions.ConfigEntryNotReady from ex

        # autodetect model
        self._model = extract_model(status)

        # autodetect Wifi version
        self._wifi_version = status.get(PhilipsApi.WIFI_VERSION)

        self._name = extract_name(status)
        self._device_id = status[PhilipsApi.DEVICE_ID]
        _LOGGER.debug(
            "Detected host %s as model %s with name: %s and firmware %s",
            self._host,
            self._model,
            self._name,
            self._wifi_version,
        )
        self._status = status

        # check if model is supported
        model_long = self._model + " " + self._wifi_version.split("@")[0]
        model = self._model
        model_family = self._model[:6]

        if model in DEVICE_MODELS:
            _LOGGER.info("Model %s supported", model)
            self._model = model
        elif model_long in DEVICE_MODELS:
            _LOGGER.info("Model %s supported", model_long)
            self._model = model_long
        elif model_family in DEVICE_MODELS:
            _LOGGER.info("Model family %s supported", model_family)
            self._model = model_family
        else:
            _LOGGER.warning(
                "Model %s of family %s not supported in DHCP discovery",
                model,
                model_family,
            )
            return self.async_abort(reason="model_unsupported")

        # use the device ID as unique_id
        unique_id = self._device_id
        _LOGGER.debug("async_step_user: unique_id=%s", unique_id)

        # set the unique id for the entry, abort if it already exists
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})

        # store the data for the next step to get confirmation
        self.context.update(
            {
                "title_placeholders": {
                    CONF_NAME: self._model + " " + self._name,
                }
            }
        )

        # show the confirmation form to the user
        _LOGGER.debug("waiting for async_step_confirm")
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Confirm the dhcp discovered data."""
        _LOGGER.debug("async_step_confirm called with user_input: %s", user_input)

        # user input was provided, so check and save it
        if user_input is not None:
            _LOGGER.debug(
                "entered creation for model %s with name '%s' at %s",
                self._model,
                self._name,
                self._host,
            )
            user_input[CONF_MODEL] = self._model
            user_input[CONF_NAME] = self._name
            user_input[CONF_DEVICE_ID] = self._device_id
            user_input[CONF_HOST] = self._host
            user_input[CONF_STATUS] = self._status

            config_entry_name = f"{self._model} {self._name}"

            return self.async_create_entry(title=config_entry_name, data=user_input)

        _LOGGER.debug("showing confirmation form")
        # show the form to the user
        self._set_confirm_only()
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={"model": self._model, "name": self._name},
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle initial step of user config flow."""
        errors = {}
        config_entry_data = user_input

        # user input was provided, so check and save it
        if config_entry_data is not None:
            try:
                host_input = config_entry_data[CONF_HOST]
                if not isinstance(host_input, str):
                    raise InvalidHost  # noqa: TRY301  # pragma: no cover

                try:
                    status = await self._async_probe_host(host_input)
                except TimeoutError:
                    return self.async_abort(reason="timeout")

                # autodetect model
                self._model = extract_model(status)

                # autodetect Wifi version
                self._wifi_version = status.get(PhilipsApi.WIFI_VERSION)

                self._name = extract_name(status)
                self._device_id = status[PhilipsApi.DEVICE_ID]
                config_entry_data[CONF_MODEL] = self._model
                config_entry_data[CONF_NAME] = self._name
                config_entry_data[CONF_DEVICE_ID] = self._device_id
                config_entry_data[CONF_HOST] = self._host
                config_entry_data[CONF_STATUS] = status

                _LOGGER.debug(
                    "Detected host %s as model %s with name: %s and firmware: %s",
                    self._host,
                    self._model,
                    self._name,
                    self._wifi_version,
                )

                # check if model is supported
                model_long = self._model + " " + self._wifi_version.split("@")[0]
                model = self._model
                model_family = self._model[:6]

                if model in DEVICE_MODELS:
                    _LOGGER.info("Model %s supported", model)
                    config_entry_data[CONF_MODEL] = model
                elif model_long in DEVICE_MODELS:
                    _LOGGER.info("Model %s supported", model_long)
                    config_entry_data[CONF_MODEL] = model_long
                elif model_family in DEVICE_MODELS:
                    _LOGGER.info("Model family %s supported", model_family)
                    config_entry_data[CONF_MODEL] = model_family
                else:
                    _LOGGER.warning(
                        "Model %s of family %s not supported in user discovery",
                        model,
                        model_family,
                    )
                    return self.async_abort(reason="model_unsupported")

                # use the device ID as unique_id
                config_entry_unique_id = self._device_id
                config_entry_name = f"{self._model} {self._name}"

                # set the unique id for the entry, abort if it already exists
                await self.async_set_unique_id(config_entry_unique_id)
                self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})

                # compile a name and return the config entry
                return self.async_create_entry(title=config_entry_name, data=config_entry_data)

            except InvalidHost:
                errors[CONF_HOST] = "host"
            except exceptions.ConfigEntryNotReady:
                errors[CONF_HOST] = "connect"

        if config_entry_data is None:
            config_entry_data = {}

        # no user_input so far
        schema = self._get_schema(config_entry_data)

        # show the form to the user
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguration to update host while keeping device identity."""
        errors: dict[str, str] = {}

        entry_id = self.context.get("entry_id")
        if not isinstance(entry_id, str):
            return self.async_abort(reason="cannot_connect")  # pragma: no cover

        entry = self.hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            host_input = user_input.get(CONF_HOST)
            if not isinstance(host_input, str):
                errors[CONF_HOST] = "host"  # pragma: no cover
            else:
                try:
                    status = await self._async_probe_host(host_input)
                    detected_device_id = status.get(PhilipsApi.DEVICE_ID)
                    if detected_device_id != entry.data.get(CONF_DEVICE_ID):
                        return self.async_abort(reason="different_device")

                    updated_data = {**entry.data, CONF_HOST: host_input, CONF_STATUS: status}
                    self.hass.config_entries.async_update_entry(entry, data=updated_data)
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reconfigure_successful")
                except InvalidHost:
                    errors[CONF_HOST] = "host"
                except TimeoutError:
                    errors[CONF_HOST] = "cannot_connect"
                except exceptions.ConfigEntryNotReady:
                    errors[CONF_HOST] = "cannot_connect"

        schema = self._get_schema({CONF_HOST: entry.data.get(CONF_HOST, "")})
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate that hostname/IP address is invalid."""
