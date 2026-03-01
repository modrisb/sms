"""DataUpdateCoordinators for the sms integration."""

import asyncio
from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.config_entries import ConfigEntry

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, CannotConnect

_LOGGER = logging.getLogger(__name__)


class ModemStatusCoordinator(DataUpdateCoordinator):
    """Signal strength coordinator."""

    def __init__(self, hass, entry: ConfigEntry, gateway):
        """Initialize signal strength coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="Modem status",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._gateway = gateway
        #self._hass = hass

    async def _async_update_data(self):
        """Fetch device signal quality."""
        try:
            if self.hass.data.get(DOMAIN) != {}:
                self.hass.add_job(self._gateway.sms_read_messages())
            async with asyncio.timeout(10):
                return await self._gateway.get_modem_status_fields()
        except CannotConnect as exc:
            raise UpdateFailed(f"Error communicating with device: {exc}") from exc
