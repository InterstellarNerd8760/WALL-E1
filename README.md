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
- No altitude, SD log, or LoRa TX in firmware yet.
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

Stack when the Pico has male headers: Pico on top of the HAT, Pico USB over the HAT silkscreen `USB` / `PWR` / `CHG` / battery end. IPEX end of the HAT sits under the Pico DEBUG end.

The Pico is currently headerless in a breadboard with sensor jumpers, so it cannot stack yet.

## Firmware — deploy with Thonny

This is not a compiled image. Thonny copies a file onto the board.

1. Plug in the Pico over USB.
2. Thonny → interpreter = MicroPython (Raspberry Pi Pico).
3. Open `firmware/main.py`.
4. Save **to the Pico** as `/main.py` (File → Save as → Raspberry Pi Pico).
5. Reset or Run. Serial should look like:
   `[12s] Temp: 22.41°C | Pressure: 1013.2 hPa | Humidity: …`

`/main.py` on the Pico is what runs on boot. Keep that copy in sync with GitHub after each change.

If Thonny drops `/dev/cu.usbmodem…` or the Mac USB serial dies, that is **not** the BME280 `OSError: [Errno 5] EIO`. Unplug, wait, replug.

### Known firmware issues

Matches the last working Thonny script, bugs included:

- Humidity calibration bytes are wrong (H1 length, H4/H5 packing, missing H6).
- `ctrl_hum` (`0xF2`) is never written, so humidity may not be sampled.
- Humidity compensation is not the Bosch formula.
- Recurring I2C `EIO` is intermittent contact/solder on the BME280, not this script. Works when the pins are pressed hard.
- Team soldering iron / solder is not good enough for a reliable rework yet.

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
