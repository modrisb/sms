"""Tests for the SMS MikroTik notifications."""
import logging
from unittest import mock

from homeassistant.components.sms.const import (
    DOMAIN,
    NOTIFY_NO_GATEWAY,
    NOTIFY_NO_TARGET,
    NOTIFY_SENDING_FAILED,
    NOTIFY_TOO_LONG,
    NOTIFY_WRONG_ENCODING,
    SMS_GATEWAY,
)
from homeassistant.core import HomeAssistant

from .common import count_filtered_log_messages, sms_integration_setup
from .patches import COMMAND_SEND, create_subprocess_shell, set_test_conf


@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_successful_sms_sending(hass: HomeAssistant, caplog) -> None:
    """Test SMS sending - message sent, expecting no error messages in log."""
    set_test_conf()
    await sms_integration_setup(hass, expected_entry_setup=True)
    phone = "+3xx"
    sms_out = "test mock"
    sms_data = {"target": '+'+str(phone), "message": sms_out}
    await hass.services.async_call("notify", "sms", sms_data, blocking=True)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, None)
    assert err_count == 0

@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_comm_err_sms_sending(hass: HomeAssistant, caplog) -> None:
    """Test SMS sending - comm error, expecting error message in log."""
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_SEND)
    await sms_integration_setup(hass, expected_entry_setup=True)
    phone = "+3xx"
    sms_out = "test mock"
    sms_data = {"target": '+'+str(phone), "message": sms_out}
    await hass.services.async_call("notify", "sms", sms_data)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, NOTIFY_SENDING_FAILED)
    assert err_count == 1

@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_sms_sending_no_target(hass: HomeAssistant, caplog) -> None:
    """Test SMS sending - no target, expecting error message in log."""
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_SEND)
    await sms_integration_setup(hass, expected_entry_setup=True)
    sms_out = "test mock"
    sms_data = {"message": sms_out}
    await hass.services.async_call("notify", "sms", sms_data)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, NOTIFY_NO_TARGET)
    assert err_count == 1

@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_sms_no_gateway(hass: HomeAssistant, caplog) -> None:
    """Test SMS sending - no sending gateway, expecting error message in log."""
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_SEND)
    await sms_integration_setup(hass, expected_entry_setup=True)
    del hass.data[DOMAIN][SMS_GATEWAY]  # remove gateway
    phone = "+3xx"
    sms_out = "test mock"
    sms_data = {"target": '+'+str(phone), "message": sms_out}
    await hass.services.async_call("notify", "sms", sms_data)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, NOTIFY_NO_GATEWAY)
    assert err_count == 1

@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_utf8_sms(hass: HomeAssistant, caplog) -> None:
    """Test SMS sending - wrong encoding, expecting error message in log."""
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_SEND)
    await sms_integration_setup(hass, expected_entry_setup=True)
    phone = "+3xx"
    sms_out = "testē mock"
    sms_data = {"target": '+'+str(phone), "message": sms_out}
    await hass.services.async_call("notify", "sms", sms_data)#, blocking=True)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, NOTIFY_WRONG_ENCODING)
    assert err_count == 1


@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_sms_above160(hass: HomeAssistant, caplog) -> None:
    """Test SMS sending - message too long, expecting error message in log."""
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_SEND)
    await sms_integration_setup(hass, expected_entry_setup=True)
    phone = "+3xx"
    sms_out = "0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789x"
    sms_data = {"target": '+'+str(phone), "message": sms_out}
    await hass.services.async_call("notify", "sms", sms_data)#, blocking=True)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, NOTIFY_TOO_LONG)
    assert err_count == 1
