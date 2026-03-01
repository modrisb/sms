"""The sms gateway to interact with a GSM modem."""

import asyncio
from contextlib import suppress
import logging

from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback

from .const import (
    COMMAND_TIMEOUT,
    CONF_INTERFACE,
    DOMAIN,
    GATEWAY_CLEARING_INBOX_FAILED,
    GATEWAY_CMD_TIMEOUT,
    GATEWAY_READ_INBOX_FAILED,
    ID_RSA,
    KNOWN_HOSTS,
    SSH_DIRECTORY,
    CannotConnect,
)

_LOGGER = logging.getLogger(__name__)

NUMERIC_STATUS_FIELDS = ['rssi', 'rsrp', 'rsrq', 'sinr']

class Gateway:
    """SMS gateway to interact with a GSM modem."""

    def __init__(self, config, hass):
        """Initialize the sms gateway."""
        _LOGGER.debug("Init with connection mode:%s", config["host"])
        self._hass = hass
        self._first_pull = True
        self._config = config
        self._base_shell_cmd = f"ssh -i {SSH_DIRECTORY}{ID_RSA} -o UserKnownHostsFile={SSH_DIRECTORY}{KNOWN_HOSTS} -p {config[CONF_PORT]} admin@{config[CONF_HOST]}"
        self._modem_status = None
        self.manufacturer = None
        self.model = None
        self.firmware = None

    async def execute_cmd(self, cmd: str, raise_exception = True) -> any:
        """Execute remote shell command via."""

        create_process = asyncio.create_subprocess_shell(
            cmd,
            stdin=None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            close_fds=False,  # required for posix_spawn
        )

        stdout_data = b""
        stderr_data = b""
        rc = 0
        process = await create_process
        try:
            async with asyncio.timeout(COMMAND_TIMEOUT):
                stdout_data, stderr_data = await process.communicate()
            rc = process.returncode
        except TimeoutError:
            _LOGGER.error(
                GATEWAY_CMD_TIMEOUT, cmd, COMMAND_TIMEOUT
            )
            if process:
                rc = process.returncode
                with suppress(TypeError):
                    process.kill()
                    # https://bugs.python.org/issue43884
                    process._transport.close()  # type: ignore[attr-defined]  # noqa: SLF001
                del process

        if raise_exception and (rc or len(stderr_data)>0):
            raise CannotConnect(f"Command execution failed: return code {rc}, message {stdout_data}, error message {stderr_data}, command {cmd}")
        return (rc, stdout_data, stderr_data)

    async def init_async(self):
        """Initialize the sms gateway asynchronously. This method is also called in config flow to verify connection."""
        await self.get_modem_status_fields()
        self.manufacturer = self._modem_status["manufacturer"]
        self.model = self._modem_status["model"]
        self.firmware = self._modem_status["revision"]

    async def sms_read_messages(self, force=False):
        """Read all received SMS messages.

        @param state_machine: state machine which invoked action
        @type state_machine: gammu.StateMachine
        """
        _LOGGER.debug("Pulling modem")

        entries = await self.get_and_delete_all_sms(force)
        _LOGGER.debug("%s SMS entries received", len(entries))

        for entry in entries:
            message = entry["message"]
            _LOGGER.debug("Processing sms message:%s", message)

        self._hass.add_job(self._notify_incoming_sms, entries)

    async def get_and_delete_all_sms(self, force=False):
        """Read and delete all SMS in the modem."""

        entries = []
        cmd_response = await self.execute_cmd(f"{self._base_shell_cmd} '/tool sms inbox print proplist=timestamp,phone,message'", False)
        if cmd_response[0] == 0 and len(cmd_response[2]) == 0:
            as_string = cmd_response[1].decode('utf-8')
            as_lines = as_string.split("\r\n")
            for line in as_lines:
                as_items = line.split("  ", 4)
                if len(as_items) >= 4 and len(as_items[2]) > 0:
                    entry = {"date":as_items[1],"phone":as_items[2],"message":as_items[3],}
                    entries.append(entry)
        else:
            _LOGGER.error(GATEWAY_READ_INBOX_FAILED, cmd_response[0], cmd_response[1], cmd_response[2])
        if len(entries)>0:
            _LOGGER.debug("Removing %s SMSs from router", len(entries))
            cmd_response = await self.execute_cmd(f"{self._base_shell_cmd} '/tool sms inbox remove [find]'", False)
            if cmd_response[0] != 0 or len(cmd_response[2]) > 0:
                _LOGGER.error(GATEWAY_CLEARING_INBOX_FAILED, cmd_response[0], cmd_response[1], cmd_response[2])
        return entries

    @callback
    def _notify_incoming_sms(self, messages):
        """Notify hass when an incoming SMS message is received."""
        for message in messages:
            event_data = {
                "phone": message["phone"],
                "date": message["date"],
                "text": message["message"],
            }
            self._hass.bus.async_fire(f"{DOMAIN}.incoming_sms", event_data)

    async def send_sms_async(self, message):
        """Send sms message via the worker."""
        lte = self._config[CONF_INTERFACE]
        target = message["target"]
        msg = message["message"]
        _LOGGER.debug("Sending SMS '%s' to %s via %s", msg, target, lte)
        cmd_response = await self.execute_cmd(f'{self._base_shell_cmd} \'/tool sms send {lte} phone={target} message="{msg}"\'')
        _LOGGER.debug("Sending SMS %s %s %s", cmd_response[0], cmd_response[1], cmd_response[2])
        return cmd_response

    async def get_imei_async(self):
        """Get the IMEI of the device."""
        await self.get_modem_status_fields()
        return self._modem_status["imei"]

    async def get_modem_status_fields(self):
        """Get the manufacturer of the modem."""
        fields = {}
        lte = self._config[CONF_INTERFACE]
        cmd_response = await self.execute_cmd(f"{self._base_shell_cmd} '/interface lte monitor {lte} once'")
        _LOGGER.debug("Modem status retrieved")
        as_string = cmd_response[1].decode('utf-8')
        as_lines = as_string.split("\r\n")
        for line in as_lines:
            as_fields = line.split(":")
            if len(as_fields)>=2:
                f_name = as_fields[0].strip().replace("-", "_")
                f_value = as_fields[1].strip()
                if f_name in NUMERIC_STATUS_FIELDS:
                    f_value = f_value.replace("dBm", "")
                    f_value = f_value.replace("dB", "")
                fields[f_name] = f_value
        self._modem_status = fields
        return fields

    async def terminate_async(self):
        """Terminate modem connection."""


async def create_sms_gateway(config, hass):
    """Create the sms gateway."""
    gateway = Gateway(config, hass)
    try:
        await gateway.init_async()
    except Exception as exc:  # noqa: BLE001
        _LOGGER.error("Failed to initialize, error %s", exc)
        await gateway.terminate_async()
        return None
    return gateway
