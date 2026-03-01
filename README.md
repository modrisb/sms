# SMS notifications via RouterOS GSM-modem MQTT Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

SMS as [Home Assistant](https://home-assistant.io) integration component implements messaging support via MikroTik RouterOS SSH/commandline interfaces. This limits message encoding to ASCII 7bit characters and length up to 160 characters. Depricated SMS with gammu interface was used as basis for RouterOS integration development by replacing interface with SSH.

## Sensors supported
* SMS integration presents sensors for modem networking/signal statuses.

## Services implemented
* SMS integration implements notify.sms service.

## Prerequisits
The RouterOS router must have modem installed, public key for connection added to router's configuration.

## Manual installation 
1. Inside the `custom_components` directory, create a new folder called `sms`.
2. Download all files from the `custom_components/sms/` repository to this directory `custom_components/sms`.
3. Install integration from Home Assistant Settings/Devices & Services/Add Integration and continue with UI configuration. RouterOS router must be configured with public key paired with private key integration configuration.

HACS might be used for installation too - check repository 'sms'.

## Credits
[Home Assistant](https://github.com/home-assistant) : Home Assistant open-source powerful domotic plateform with MQTT integration.<br>
[HACS](https://hacs.xyz/) : Home Assistant Community Store gives you a powerful UI to handle downloads of all your custom needs.<br>
