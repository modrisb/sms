"""Common routines/constants for the SMS MikroTik integration tests."""

from homeassistant.components.sms.const import (
    CONF_CHANNEL,
    CONF_PRIVATE_KEY,
    DEFAULT_CHANNEL,
    DEFAULT_PORT,
    CONF_INTERFACE,
    DEFAULT_INTERFACE,
    DOMAIN,
)
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .patches import INVALID_PK, VALID_PK

from tests.common import MockConfigEntry

VALID_CONFIGURATION = {
            CONF_HOST: "router.zzz",
            CONF_PORT: DEFAULT_PORT,
            CONF_INTERFACE: DEFAULT_INTERFACE,
            CONF_PRIVATE_KEY: VALID_PK,
            CONF_CHANNEL: DEFAULT_CHANNEL,
        }

INVALID_PKD_CONFIGURATION = {
            CONF_HOST: "router.zzz",
            CONF_PORT: DEFAULT_PORT,
            CONF_INTERFACE: DEFAULT_INTERFACE,
            CONF_PRIVATE_KEY: INVALID_PK,
            CONF_CHANNEL: DEFAULT_CHANNEL,
        }


TEST_DEFAULT_SCAN_INTERVAL= 1
TEST_CASE_SCAN_INTERVAL= TEST_DEFAULT_SCAN_INTERVAL + 0.1
TEST_COMMAND_TIMEOUT = 0.5
TEST_CASE_COMMAND_TIMEOUT = TEST_COMMAND_TIMEOUT + 0.1

#pytest ./tests/components/sms/ --cov=homeassistant.components.sms --cov-report term-missing

async def sms_integration_setup(
    hass: HomeAssistant, config_data=None, expected_entry_setup=True
):
    """Execute test case in standard configuration environment with grpc/mqtt mocks."""

    unique_id = "imei_based_id"
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=unique_id,
        data=config_data if config_data else VALID_CONFIGURATION,
    )

    # Load config_entry.
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id) == expected_entry_setup

    await hass.async_block_till_done()

def count_filtered_log_messages(caplog, level, msg_template):
    """Execute test case in standard configuration environment with grpc/mqtt mocks."""
    i_counter = 0
    for record in caplog.records:
        if (not msg_template or record.msg == msg_template) and record.levelno == level:
            i_counter += 1
    return i_counter
