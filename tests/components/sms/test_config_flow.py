"""Tests for the SMS MikroTik integration config flow."""
import logging
from unittest import mock

from homeassistant import data_entry_flow
from homeassistant.components.sms.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .common import (
    INVALID_PKD_CONFIGURATION,
    VALID_CONFIGURATION,
    count_filtered_log_messages,
    sms_integration_setup,
)
from .patches import COMMAND_STATUS, create_subprocess_shell, set_test_conf


#@mock.patch("homeassistant.components.sms.asyncio.create_subprocess_shell", new=create_subprocess_shell)
@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_with_failing_conection(hass: HomeAssistant) -> None:
    """Test configuration with failing communication with router, failure on status retrieval."""
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_STATUS)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=VALID_CONFIGURATION,
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {'base': 'cannot_connect'}

async def get_imei_from_config(hass: HomeAssistant, data) -> str:
    """Test mock to simulate unknown initialization failure."""
    raise ZeroDivisionError("test mock")

@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
@mock.patch("homeassistant.components.sms.config_flow.get_imei_from_config", new=get_imei_from_config)
async def test_sms_unknown_failure(hass: HomeAssistant) -> None:
    """Test configuration with failing initialization process."""
    set_test_conf()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=VALID_CONFIGURATION,
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {'base': 'unknown'}

@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_sms_connection_failure_pk_invalid(hass: HomeAssistant) -> None:
    """Test configuration with wrong format RSA pk data."""
    set_test_conf()  # connection to fail
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=INVALID_PKD_CONFIGURATION,
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {'base': 'pk_invalid'}

@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_sms_connection_ok_pk_valid(hass: HomeAssistant) -> None:
    """Test configuration with valid configuration data."""
    set_test_conf()  # connection to fail
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=VALID_CONFIGURATION,
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert not result.get("errors")

@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_connection_ok(hass: HomeAssistant, caplog) -> None:
    """Test configuration with failing comm to router."""
    set_test_conf(sub_fail=1,cmd_fail=COMMAND_STATUS)   #   force initialization to fail due to comm error
    await sms_integration_setup(hass, expected_entry_setup=False)

    err_count = count_filtered_log_messages(caplog, logging.ERROR, None)
    assert err_count == 1

@mock.patch("asyncio.create_subprocess_shell", new=create_subprocess_shell)
async def test_single_instance_allowed(hass: HomeAssistant) -> None:
    """Test installation of 2nd integration instance, expecting failure."""
    set_test_conf()  # connection to fail
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=VALID_CONFIGURATION,
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert not result.get("errors")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == 'single_instance_allowed'
