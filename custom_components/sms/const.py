"""Constants for sms Component."""
from homeassistant.exceptions import HomeAssistantError

DOMAIN = "sms"
SMS_GATEWAY = "SMS_GATEWAY"
HASS_CONFIG = "sms_hass_config"
MODEM_STATUS_COORDINATOR = "MODEM_STATUS_COORDINATOR"
GATEWAY = "gateway"
DEFAULT_SCAN_INTERVAL = 60
CONF_CHANNEL = "channel"
CONF_INTERFACE = "interface"
DEFAULT_INTERFACE = "lte"

DEFAULT_CHANNEL = ""
COMMAND_TIMEOUT = 6
CONF_PRIVATE_KEY = "private_key"
DEFAULT_PORT = 22
SSH_DIRECTORY = "/config/.ssh/"
ID_RSA = "id_ros"
KNOWN_HOSTS = "known_to_ros"
MAX_MESSAGE_LENGTH = 160
NOTIFY_SENDING_FAILED = "Sending to %s failed: %s"
NOTIFY_NO_TARGET = "No target number specified, cannot send message"
NOTIFY_NO_GATEWAY = "SMS gateway not found, cannot send message"
NOTIFY_WRONG_ENCODING = "Wrong message encoding: only printable ASCII characters supported, message not sent"
NOTIFY_TOO_LONG = "Message length exceeds %s characters, message not sent"
GATEWAY_CMD_TIMEOUT = "Timed out running command: `%s`, after: %ss"
GATEWAY_READ_INBOX_FAILED = "Reading sms inbox failed: return code %s, message %s, error message %s"
GATEWAY_CLEARING_INBOX_FAILED = "Clearing sms inbox failed: return code %s, message %s, error message %s"

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
