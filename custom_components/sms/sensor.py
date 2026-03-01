"""Support for SMS dongle sensor."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, GATEWAY, MODEM_STATUS_COORDINATOR, SMS_GATEWAY

_LOGGER = logging.getLogger(__name__)

SIGNAL_SENSORS = (
    SensorEntityDescription(
        key="rssi",   #key="SignalStrength",
        translation_key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rsrp",    #key="SignalPercent",
        translation_key="rsrp",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_registry_enabled_default=True,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="rsrq", #key="BitErrorRate",
        translation_key="rsrq",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="sinr", #key="BitErrorRate",
        translation_key="sinr",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        entity_registry_enabled_default=False,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

NETWORK_SENSORS = (
    SensorEntityDescription(
        key="current_operator",
        translation_key="current_operator",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="status",
        translation_key="status",
        entity_registry_enabled_default=True,
    ),
    SensorEntityDescription(
        key="current_cellid",
        translation_key="current_cellid",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="iccid",
        translation_key="iccid",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key="lac",
        translation_key="lac",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up all device sensors."""
    sms_data = hass.data[DOMAIN][SMS_GATEWAY]
    modem_status_coordinator = sms_data[MODEM_STATUS_COORDINATOR]
    gateway = sms_data[GATEWAY]
    unique_id = str(await gateway.get_imei_async())
    entities = [
        DeviceSensor(modem_status_coordinator, description, unique_id, gateway)
        for description in SIGNAL_SENSORS
    ]
    entities.extend(
        DeviceSensor(modem_status_coordinator, description, unique_id, gateway)
        for description in NETWORK_SENSORS
    )
    async_add_entities(entities, True)
    _LOGGER.info("%s sensor entities added", len(entities))


class DeviceSensor(CoordinatorEntity, SensorEntity):
    """Implementation of a device sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, description, unique_id, gateway):
        """Initialize the device sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name="SMS Gateway",
            manufacturer=gateway.manufacturer,
            model=gateway.model,
            sw_version=gateway.firmware,
        )
        self._attr_unique_id = f"{unique_id}_{description.key}"
        self.entity_description = description

    @property
    def native_value(self):
        """Return the state of the device."""
        return self.coordinator.data.get(self.entity_description.key)
