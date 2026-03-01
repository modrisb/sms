"""Tests for the SMS MikroTik integration config flow."""
import asyncio
import logging
from unittest import mock

from homeassistant.components.sms.const import (
    GATEWAY_CLEARING_INBOX_FAILED,
    GATEWAY_CMD_TIMEOUT,
    GATEWAY_READ_INBOX_FAILED,
)
from homeassistant.core import HomeAssistant

from .common import (
    TEST_CASE_COMMAND_TIMEOUT,
    TEST_CASE_SCAN_INTERVAL,
    TEST_COMMAND_TIMEOUT,
    TEST_DEFAULT_SCAN_INTERVAL,
    count_filtered_log_messages,
    sms_integration_setup,
)
from .patches import (
    COMMAND_INBOX,
    COMMAND_REMOVE,
    COMMAND_STATUS,
    create_subprocess_shell,
    set_test_conf,
)


@mock.patch("homeassistant.components.sms.coordinator.DEFAULT_SCAN_INTERVAL", new=TEST_DEFAULT_SCAN_INTERVAL)
@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_status_update_with_comm_err(hass: HomeAssistant, caplog) -> None:
    """Test with status comm error, expecting error message in log."""
    set_test_conf()
    await sms_integration_setup(hass, expected_entry_setup=True)
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_STATUS)   #   force initialization to fail due to comm error during sensor update
    await asyncio.sleep(TEST_CASE_SCAN_INTERVAL)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, None)
    assert err_count == 1

@mock.patch("homeassistant.components.sms.gateway.COMMAND_TIMEOUT", new=TEST_COMMAND_TIMEOUT)
@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_cmd_timeout(hass: HomeAssistant, caplog) -> None:
    """Test with comm timeout, expecting error message in log."""
    set_test_conf(delay=TEST_CASE_COMMAND_TIMEOUT)   #   force cmd execution to time out
    await sms_integration_setup(hass, expected_entry_setup=False)
    await asyncio.sleep(TEST_CASE_COMMAND_TIMEOUT+0.1)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, GATEWAY_CMD_TIMEOUT)
    assert err_count == 1

@mock.patch("homeassistant.components.sms.coordinator.DEFAULT_SCAN_INTERVAL", new=TEST_DEFAULT_SCAN_INTERVAL)
@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_sms_read_failure(hass: HomeAssistant, caplog) -> None:
    """Test with failed sms read, expecting error message in log."""
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_INBOX)
    await sms_integration_setup(hass, expected_entry_setup=True)
    await asyncio.sleep(TEST_CASE_SCAN_INTERVAL/4)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, GATEWAY_READ_INBOX_FAILED)
    assert err_count == 1

@mock.patch("homeassistant.components.sms.coordinator.DEFAULT_SCAN_INTERVAL", new=TEST_DEFAULT_SCAN_INTERVAL)
@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_sms_remove_failure(hass: HomeAssistant, caplog) -> None:
    """Test with failed sms removal, expecting error message in log."""
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_REMOVE)
    await sms_integration_setup(hass, expected_entry_setup=True)
    await asyncio.sleep(TEST_CASE_SCAN_INTERVAL/4)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, GATEWAY_CLEARING_INBOX_FAILED)
    assert err_count == 1
