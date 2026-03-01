"""The sms component."""

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, GATEWAY, HASS_CONFIG, MODEM_STATUS_COORDINATOR, SMS_GATEWAY
from .coordinator import ModemStatusCoordinator
from .gateway import create_sms_gateway

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

#SMS_CONFIG_SCHEMA = {vol.Required(CONF_DEVICE): cv.isdevice}
#
#CONFIG_SCHEMA = vol.Schema(
#    {
#        DOMAIN: vol.Schema(
#            vol.All(
#                cv.deprecated(CONF_DEVICE),
#                SMS_CONFIG_SCHEMA,
#            ),
#       )
#    },
#    extra=vol.ALLOW_EXTRA,
#)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configure Gammu state machine."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[HASS_CONFIG] = config
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure Gammu state machine."""

    gateway = await create_sms_gateway(entry.data, hass)
    if not gateway:
        raise ConfigEntryNotReady("Cannot find device")

    modem_status_coordinator = ModemStatusCoordinator(hass, entry, gateway)

    # Fetch initial data so we have data when entities subscribe
    await modem_status_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][SMS_GATEWAY] = {
        MODEM_STATUS_COORDINATOR: modem_status_coordinator,
        GATEWAY: gateway,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # set up notify platform, no entry support for notify component yet,
    # have to use discovery to load platform.
    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            {CONF_NAME: DOMAIN},
            hass.data[HASS_CONFIG],
        )
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        gateway = hass.data[DOMAIN].pop(SMS_GATEWAY)[GATEWAY]
        await gateway.terminate_async()

    return unload_ok
