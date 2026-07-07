# Alstom P14x Protection Relay

[![Validate](https://github.com/LucMathlin/ha-alstom-p14x/actions/workflows/validate.yml/badge.svg)](https://github.com/LucMathlin/ha-alstom-p14x/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=LucMathlin&repository=ha-alstom-p14x&category=integration)

A Home Assistant custom integration for Alstom/GE P14x series protection relays (P141, P142, P143, P145) via Modbus TCP.

## Supported Devices

- Alstom/GE MiCOM P141
- Alstom/GE MiCOM P142
- Alstom/GE MiCOM P143
- Alstom/GE MiCOM P145

## Features

- Real-time sensor readings (current, voltage, frequency, power)
- Binary sensors for relay status and trip indicators
- Button entities for relay control operations
- Configurable via the Home Assistant UI (config flow)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/LucMathlin/ha-alstom-p14x` with category **Integration**
4. Search for "Alstom P14x" and install
5. Restart Home Assistant

### Manual

1. Copy `custom_components/alstom_p14x/` to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Alstom P14x"
3. Enter the Modbus TCP host and port of your relay
4. Configure polling interval as needed

## Requirements

- Modbus TCP connectivity to the relay
- `pymodbus>=3.6.0` (installed automatically)
