"""Support for SMS notification services."""

from __future__ import annotations

import logging

from homeassistant.components.notify import BaseNotificationService
from homeassistant.const import CONF_TARGET
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    DOMAIN,
    GATEWAY,
    MAX_MESSAGE_LENGTH,
    NOTIFY_NO_GATEWAY,
    NOTIFY_NO_TARGET,
    NOTIFY_SENDING_FAILED,
    NOTIFY_TOO_LONG,
    NOTIFY_WRONG_ENCODING,
    SMS_GATEWAY,
    CannotConnect,
)

_LOGGER = logging.getLogger(__name__)


async def async_get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> SMSNotificationService | None:
    """Get the SMS notification service."""

    return SMSNotificationService(hass)


class SMSNotificationService(BaseNotificationService):
    """Implement the notification service for SMS."""

    def __init__(self, hass):
        """Initialize the service."""

        self.hass = hass

    async def async_send_message(self, message="", **kwargs):
        """Send SMS message."""

        _LOGGER.info("Sending SMS message %s", message)
        if SMS_GATEWAY not in self.hass.data[DOMAIN]:
            _LOGGER.error(NOTIFY_NO_GATEWAY)
            return

        gateway = self.hass.data[DOMAIN][SMS_GATEWAY][GATEWAY]

        targets = kwargs.get(CONF_TARGET)
        if targets is None:
            _LOGGER.error(NOTIFY_NO_TARGET)
            return

        if not message.isascii():
            _LOGGER.error(NOTIFY_WRONG_ENCODING)
            return

        if len(message) > MAX_MESSAGE_LENGTH:
            _LOGGER.error(NOTIFY_TOO_LONG, MAX_MESSAGE_LENGTH)
            return

        # RouterOS cr, lf representation for command line
        message = message.replace("\n", "\\n")
        message = message.replace("\r", "\\r")
        message = message.replace('"', '\\"')

        # Send messages
        for target in targets:
            try:
                # Actually send the message
                await gateway.send_sms_async({"target":target, "message":message})
            except CannotConnect as exc:
                _LOGGER.error(NOTIFY_SENDING_FAILED, target, exc)
