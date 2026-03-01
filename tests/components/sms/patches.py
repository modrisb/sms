"""Mocks for the SMS MikroTik integration tests: ."""

import asyncio

VALID_PK = "-----BEGIN RSA PRIVATE KEY----- -----END RSA PRIVATE KEY-----"
INVALID_PK ="pk"
VALID_MODEM_RESPONSE = b'               status: registered                    \r\n           pin-status: ok                            \r\n  registration-status: registered                    \r\n         manufacturer: Quectel                       \r\n                model: EC200A                        \r\n             revision: EC200AEUHAR01A19M16           \r\n     current-operator: LMT                           \r\n                  lac: 40131                         \r\n       current-cellid: 2348052                       \r\n               enb-id: 9172                          \r\n            sector-id: 20                            \r\n           phy-cellid: 487                           \r\n    access-technology: LTE                           \r\n       session-uptime: 2h34m41s                      \r\n                 imei: 863553067852461               \r\n                 imsi: 247010601150621               \r\n                iccid: 8937101121700016212           \r\n               earfcn: 1300 (band 3, bandwidth 20Mhz)\r\n                 rssi: -82dBm                        \r\n                 rsrp: -93dBm                        \r\n                 rsrq: -9dB                          \r\n                 sinr: 13dB                          \r\n\r\n'
VALID_INBOX_RESPONSE = b'Columns: TIMESTAMP, PHONE, MESSAGE\r\n#  TIMESTAMP                  PHONE         MESSAGE  \r\n0  2026-02-25 20:56:59+02:00  +37126546652  Test03 we\r\n\r\n'
VALID_DELETE_RESPONSE = b''
VALID_SEND_RESPONSE = b'\r\n'

COMMAND_STATUS = "lte monitor"
COMMAND_INBOX = "sms inbox print"
COMMAND_REMOVE ="sms inbox remove"
COMMAND_SEND = "sms send"

TEST_SETTINGS = {
    "sub_fail": 0,
    "cmd_fail": None,
    "abort": 0,
    "pass_count": -1,
    "delay": 0,
    "cmd": None,
}

def set_test_conf(sub_fail=0, cmd_fail="~", abort=0, pass_count=-1, delay=0):
    """Set test mock parameters."""
    TEST_SETTINGS["sub_fail"] = sub_fail
    TEST_SETTINGS["cmd_fail"] = cmd_fail
    TEST_SETTINGS["abort"] = abort
    TEST_SETTINGS["pass_count"] = pass_count
    TEST_SETTINGS["delay"] = delay

def get_test_conf(p_name):
    """Get test mock parameter."""
    return TEST_SETTINGS[p_name]

async def create_subprocess_shell(
            cmd,
            stdin=None,
            stdout=1,
            stderr=2,
            close_fds=False,  # required for posix_spawn
        ):
    """asyncio.create_subprocess_shell mock."""
    TEST_SETTINGS["cmd"] = cmd
    if TEST_SETTINGS["pass_count"]>=0:
        TEST_SETTINGS["pass_count"] = TEST_SETTINGS["pass_count"] -1
    process = lambda: None  # noqa: E731
    process.communicate = communicate
    process.kill = kill
    process._transport = lambda: None
    process._transport.close = close
    process.returncode = get_rc()[0] if TEST_SETTINGS["abort"]==0 else 0
    if get_rc()[0]!=0 and TEST_SETTINGS["abort"]!=0:
        raise ZeroDivisionError("test mock")
    if TEST_SETTINGS["pass_count"]>0:
        process.returncode=0
    return process

def get_rc():
    """asyncio.create_subprocess_shell mock."""
    cmd = TEST_SETTINGS["cmd"]
    tag = TEST_SETTINGS["cmd_fail"]
    rc = TEST_SETTINGS["sub_fail"]
    if COMMAND_STATUS in cmd:
        response = VALID_MODEM_RESPONSE
        rc = 0 if tag != COMMAND_STATUS else rc
    elif COMMAND_INBOX in cmd:
        response = VALID_INBOX_RESPONSE
        rc = 0 if tag != COMMAND_INBOX else rc
    elif COMMAND_REMOVE in cmd:
        response = VALID_DELETE_RESPONSE
        rc = 0 if tag != COMMAND_REMOVE else rc
    elif COMMAND_SEND in cmd:
        response = VALID_SEND_RESPONSE
        rc = 0 if tag != COMMAND_SEND else rc
    else:
        response = b""
        rc = 0 if tag != "~" else rc
    return (rc, response)

async def communicate():
    """asyncio.create_subprocess_shell mock."""
    if TEST_SETTINGS["delay"]>0 and COMMAND_STATUS in TEST_SETTINGS["cmd"]:
        await asyncio.sleep(TEST_SETTINGS["delay"])
    st = get_rc()
    return (st[1] if st[0]==0 else b"", b"")

def kill():
    """asyncio.create_subprocess_shell mock."""

def close():
    """asyncio.create_subprocess_shell mock."""

