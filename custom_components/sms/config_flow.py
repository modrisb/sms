"""Config flow for SMS integration."""

import logging
from typing import Any

import aiofiles
import voluptuous as vol

from homeassistant import core
from homeassistant.config_entries import CONN_CLASS_LOCAL_POLL, ConfigFlow, FlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CHANNEL,
    CONF_INTERFACE,
    CONF_PRIVATE_KEY,
    DEFAULT_CHANNEL,
    DEFAULT_INTERFACE,
    DEFAULT_PORT,
    DOMAIN,
    ID_RSA,
    KNOWN_HOSTS,
    SSH_DIRECTORY,
    CannotConnect,
)
from .gateway import Gateway, create_sms_gateway

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_INTERFACE, default=DEFAULT_INTERFACE): str,
        vol.Required(CONF_PRIVATE_KEY): str,
        vol.Optional(CONF_CHANNEL, default=DEFAULT_CHANNEL): str,
    }
)


async def get_imei_from_config(hass: HomeAssistant, data: dict[str, Any]) -> str:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    gateway = await create_sms_gateway(data, hass)
    if not gateway:
        raise CannotConnect
    try:
        imei = await gateway.get_imei_async()
        _LOGGER.debug("Modem imei %s", imei)
    finally:
        await gateway.terminate_async()

    # Return info that you want to store in the config entry.
    return imei

async def set_pk(hass: HomeAssistant, config):
    """Check pk validity and set-up files for ssh connection."""
    pk_ok = False
    rsa_pk = config[CONF_PRIVATE_KEY]
    if rsa_pk.startswith("-----BEGIN RSA PRIVATE KEY-----") and rsa_pk.endswith("-----END RSA PRIVATE KEY-----"):
        gtw = Gateway(config, hass)
        resp = await gtw.execute_cmd(f"mkdir {SSH_DIRECTORY}; ssh-keyscan -p {config[CONF_PORT]} -H {config[CONF_HOST]} > {SSH_DIRECTORY}{KNOWN_HOSTS}", False)
        _LOGGER.debug("RSA1 rc %s, message %s, error %s", resp[0], resp[1],resp[2])
        rsa_pk = rsa_pk + "\n"
        rsa_pk = rsa_pk.replace(" ", "\n")
        rsa_pk = rsa_pk.replace("\nRSA\nPRIVATE\nKEY", " RSA PRIVATE KEY")
        async with aiofiles.open(f"{SSH_DIRECTORY}{ID_RSA}", "w") as id_file:
            await id_file.write(rsa_pk)
        resp = await gtw.execute_cmd(f"chmod 700 {SSH_DIRECTORY}; chmod 600 {SSH_DIRECTORY}{ID_RSA}; chmod 644 {SSH_DIRECTORY}{KNOWN_HOSTS}", False)
        _LOGGER.debug("RSA2 rc %s, message %s, error %s", resp[0], resp[1],resp[2])
        pk_ok = True
    return pk_ok

class SMSFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SMS integration."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Set initial values for ChirpConfigFlow."""
        self.hass: core.HomeAssistant = core.async_get_hass()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:    #ConfigFlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        errors = {}
        if user_input is not None:
            if not await set_pk(self.hass, user_input):
                errors["base"] = "pk_invalid"

            if not errors:
                try:
                    imei = await get_imei_from_config(self.hass, user_input)
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(imei)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=imei, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
