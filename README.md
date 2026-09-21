# WALL-E1

Weather-balloon flight computer and ground dashboard.

Payload will collect atmospheric data, log it onboard, and send telemetry to the ground. Two pieces live in this repo:

| Path | What it is |
| --- | --- |
| `firmware/main.py` | Pico MicroPython flight computer |
| `mission-control/index.html` | Ground UI (browser, no build) |

**Repo owner:** Weston Rosch (`InterstellarNerd8760`)

## Status

- Firmware reads the BME280 over I2C and prints temp / pressure / humidity every ~3.14 s.
- Humidity uses Bosch cal packing, `ctrl_hum`, and datasheet compensation.
- Part 97 station ID (`KO6OGZ WALL-E1`) prints on a separate 10-minute timer (serial stub until LoRa TX).
- No altitude, SD log, or LoRa TX in firmware yet.
- **Near-term gate:** reliable BME280 connections first. HELLO / LoRa TX stays parked until the sensor path actually works (hardware contact — not fixable from the terminal alone).
- Mission Control is a **simulated** flight so the UI can be built before radio works: Fair Oaks launch, baro-shaped telemetry, LoRa packet log, SpotTrace-shaped track.
- Live Pico / SX1262 / FindMeSPOT ingest is not wired.

First major victory is still: collect sensor data **and** transmit a LoRa packet (`HELLO FROM WALL-E1`).

## Hardware

- Raspberry Pi Pico, MicroPython
- BME280 on I2C0: SDA=`GP0`, SCL=`GP1`, address `0x76`
- Waveshare Pico-LoRa SX1262 Node (HF, 850–930 MHz) — Pico-footprint HAT, stack, do not hand-wire SPI
- IPEX-1 pigtail seated on the HAT U.FL jack → SMA
- `ANT_SW`: A=`3V3`, B=`GP22`
- HAT battery jack: PH1.25 LiPo (USB for now)

**Stack:** The Pico is headerless. The LoRa HAT has male headers pre-soldered. The HAT goes straight onto the Pico (LoRa on the Pico) — that is the whole stack. Align USB end with HAT silkscreen `USB` / `PWR` / `CHG` / battery end; IPEX/antenna end toward the Pico DEBUG end. Seat the antenna on U.FL→SMA before any TX.

BME280 is still on breadboard jumpers for connection work; that path is separate from the HAT stack.

## Firmware — deploy with Thonny

This is not a compiled image. Thonny copies a file onto the board.

1. Plug in the Pico over USB.
2. Thonny → interpreter = MicroPython (Raspberry Pi Pico).
3. Open `firmware/main.py`.
4. Save **to the Pico** as `/main.py` (File → Save as → Raspberry Pi Pico).
5. Reset or Run. Serial should look like:
   `[12s] Temp: 22.41°C | Pressure: 1013.2 hPa | Humidity: …`
   and periodically `[ID] KO6OGZ WALL-E1`.

`/main.py` on the Pico is what runs on boot. Keep that copy in sync with GitHub after each change.

If Thonny drops `/dev/cu.usbmodem…` or the Mac USB serial dies, that is **not** the BME280 `OSError: [Errno 5] EIO`. Unplug, wait, replug.

### Known firmware issues

- Recurring I2C `EIO` is intermittent contact/solder on the BME280, not this script. Works when the pins are pressed hard.
- Team soldering iron / solder is not good enough for a reliable rework yet.
- LoRa / SX1262 TX not in firmware yet — parked behind a working BME280 path. Hardware stack (HAT on Pico) is available; do not ticket HELLO TX until the sensor is solid.

## Mission Control

Open `mission-control/index.html` in a desktop browser. No install, no bundler.

Layout: left telemetry + altitude graph, center map, right LoRa log, bottom system status.

Controls: Pause / 10× / Reset. Keys: `space` pause, `f` 10×, `r` reset.

More detail: [`mission-control/README.md`](mission-control/README.md).

## Repo layout

```
firmware/main.py              # flight computer
mission-control/index.html    # ground dashboard
mission-control/README.md
```

## Path to flight

Hardware connections → sensor validation → radio hardware → radio software → first TX → telemetry packets → range test → integrated payload → balloon flight.
