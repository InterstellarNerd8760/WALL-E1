# WALL-E1

Weather-balloon flight computer. Payload collects atmospheric data onboard and will transmit telemetry to ground.

**Repo owner:** Weston Rosch (`InterstellarNerd8760`)

## Hardware (current)

- Raspberry Pi Pico, MicroPython
- BME280 on I2C0: SDA=GP0, SCL=GP1, address `0x76`
- Waveshare Pico-LoRa SX1262 (HF, 850–930 MHz) — stacked HAT
- IPEX-1 pigtail seated on the HAT U.FL jack

## Deploy to the Pico (Thonny)

This is not a compiled firmware image. The Pico runs MicroPython; Thonny copies a file onto the board.

1. Plug in the Pico over USB.
2. Open Thonny → interpreter = MicroPython (Raspberry Pi Pico).
3. Open `firmware/main.py`.
4. Save **to the Pico** as `/main.py` (File → Save as → Raspberry Pi Pico).
5. Reset or click Run. Serial output should look like:
   `[12s] Temp: 22.41°C | Pressure: 1013.2 hPa | Humidity: …`

`main.py` on the Pico is what runs on boot. Keep the GitHub copy and the board copy in sync after each change.

If Thonny drops `/dev/cu.usbmodem…` or the Mac USB serial dies, that is separate from BME280 `OSError: [Errno 5] EIO`. Unplug, wait, replug; do not treat a serial crash as an I2C bug.

## Mission Control

Ground dashboard lives in `mission-control/`. Open `mission-control/index.html` in a browser — no build step.

Current UI is a simulated flight (Fair Oaks launch, baro telemetry, LoRa packet log, SpotTrace-shaped track). Live Pico / SX1262 / FindMeSPOT ingest is not wired yet.

Layout: left telemetry + altitude graph, center map, right LoRa log, bottom system status.

## Known issues in this snapshot

Firmware matches the last working Thonny script, including bugs we already know:

- Humidity calibration bytes are wrong (H1 length, H4/H5 packing, missing H6).
- `ctrl_hum` (`0xF2`) is never written, so humidity may not be sampled.
- Humidity compensation is not the Bosch formula.
- Recurring I2C `EIO` is intermittent contact/solder on the BME280, not this script. Works when pins are pressed.
- No altitude, no LoRa in firmware yet.

## Layout

```
firmware/          # Pico MicroPython (this is the flight computer)
  main.py
mission-control/   # ground dashboard — design owned by Weston
  index.html
  README.md
docs/
```

Development path: hardware connections → sensor validation → radio hardware → radio software → first TX (`HELLO FROM WALL-E1`) → telemetry packets → range test → integrated payload → balloon flight.

First major victory: collect sensor data **and** transmit a LoRa packet.
