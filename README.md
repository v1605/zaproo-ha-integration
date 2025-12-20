# Zaparoo Home Assistant Integration

The Zaparoo integration connects Home Assistant to a Zaparoo device, allowing you to emulate token scans, control active launchers, and monitor media and connection state in real time.
This integration is designed with events in mind. It uses a persistent WebSocket connection for fast updates and responsive control.

## Features

- Emulate scanning Zaparoo NFC or token data
- Stop active launchers remotely
- Query current media state and database info
- Live sensors for:
  - Last Zaparoo event
  - Device connection state
  - Currently playing media
- Compatible with automations, scripts, and dashboards

## Installation

### Via HACS (recommended)

1. Add this repository as a Custom Repository as Type Integration
2. Install the Zaparoo integration
3. Restart Home Assistant

### Manual Installation

1. Copy `custom_components/zaparoo` into your Home Assistant configuration directory
2. Restart Home Assistant


## Configuration

Configuration is done through the Home Assistant UI.
You will need:
- The Zaparoo device hostname or address
- Network connectivity to the device to the Home Assistant Server

Once configured, the integration creates a Zaparoo device with associated sensors and services.


## Services

### zaparoo.launch

Emulate scanning a Zaparoo token. This is the primary way to trigger ZapScript actions from Home Assistant.

Fields:

- device_id (required)  
  Target Zaparoo device

- type (optional)  
  Optional internal token category (used for logging), for example nfc

- text (optional)  
  Main token text containing ZapScript  
  Example:
  **launch.title:SNES/Super Mario World

- data (optional)  
  Raw token data as a hexadecimal string  
  Example:
  04A224BCFF12

- unsafe (optional, default: false)  
  Allow unsafe ZapScript operations

Example:
```yaml
service: zaparoo.launch  
data:  
  device_id: YOUR_DEVICE_ID  
  text: "**launch.title:SNES/Super Mario World"
```

### zaparoo.stop

Stop any active launcher, if supported by the device.

Fields:

- device_id (required)  
  Target Zaparoo device

Example:
```yaml
service: zaparoo.stop  
data:  
  device_id: YOUR_DEVICE_ID
```

### zaparoo.media

Query the current media state and database info.
This service returns a response payload and is intended for use in scripts and automations that consume service responses.

Fields:

- device_id (required)  
  Target Zaparoo device

Example:
```yaml
service: zaparoo.media  
data:  
  device_id: YOUR_DEVICE_ID  
response_variable: media_state
```
---

## Sensors

Each configured Zaparoo device provides the following sensors.

### Zaparoo Notification

Displays the most recent Zaparoo notification, such as media.started.
The sensor exposes additional attributes containing the full event payload received from the device. The full documentation of events can be found [here](https://zaparoo.org/docs/core/api/notifications/)

### Zaparoo Connected

Shows whether the Zaparoo device is currently connected.
true indicates the device is online  
false indicates the device is offline or powered off

### Zaparoo Media

Shows the name of the currently playing media, if available.
Additional attributes expose the full media payload returned by the device, including metadata such as title and platform.
If no media is active, the sensor state will be unknown.


## Debugging

To enable debug logging:
```yaml
logger:  
  logs:  
    custom_components.zaparoo: debug
```

## License

GPL-3.0 license




