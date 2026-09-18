from machine import Pin, I2C
from time import sleep
import utime

print("=== WALL-E Flight Computer ===")

# Part 97 station ID — separate from the ~3.14 s telemetry loop.
# LoRa TX not wired yet (HAT cannot stack until Pico has headers).
CALLSIGN = "KO6OGZ"
ID_PAYLOAD = "KO6OGZ WALL-E1"
ID_INTERVAL_MS = 10 * 60 * 1000  # 10 minutes

i2c = I2C(0, sda=Pin(0), scl=Pin(1))

# Calibration coefficients
# Temp
dig_T1 = int.from_bytes(i2c.readfrom_mem(0x76, 0x88, 2), "little")
dig_T2 = int.from_bytes(i2c.readfrom_mem(0x76, 0x8A, 2), "little")
if dig_T2 & 0x8000:
    dig_T2 = dig_T2 - 0x10000
dig_T3 = int.from_bytes(i2c.readfrom_mem(0x76, 0x8C, 2), "little")
if dig_T3 & 0x8000:
    dig_T3 = dig_T3 - 0x10000

# Pressure
dig_P1 = int.from_bytes(i2c.readfrom_mem(0x76, 0x8E, 2), "little")
dig_P2 = int.from_bytes(i2c.readfrom_mem(0x76, 0x90, 2), "little")
if dig_P2 & 0x8000:
    dig_P2 = dig_P2 - 0x10000
dig_P3 = int.from_bytes(i2c.readfrom_mem(0x76, 0x92, 2), "little")
if dig_P3 & 0x8000:
    dig_P3 = dig_P3 - 0x10000
dig_P4 = int.from_bytes(i2c.readfrom_mem(0x76, 0x94, 2), "little")
if dig_P4 & 0x8000:
    dig_P4 = dig_P4 - 0x10000
dig_P5 = int.from_bytes(i2c.readfrom_mem(0x76, 0x96, 2), "little")
if dig_P5 & 0x8000:
    dig_P5 = dig_P5 - 0x10000
dig_P6 = int.from_bytes(i2c.readfrom_mem(0x76, 0x98, 2), "little")
if dig_P6 & 0x8000:
    dig_P6 = dig_P6 - 0x10000
dig_P7 = int.from_bytes(i2c.readfrom_mem(0x76, 0x9A, 2), "little")
if dig_P7 & 0x8000:
    dig_P7 = dig_P7 - 0x10000
dig_P8 = int.from_bytes(i2c.readfrom_mem(0x76, 0x9C, 2), "little")
if dig_P8 & 0x8000:
    dig_P8 = dig_P8 - 0x10000
dig_P9 = int.from_bytes(i2c.readfrom_mem(0x76, 0x9E, 2), "little")
if dig_P9 & 0x8000:
    dig_P9 = dig_P9 - 0x10000

# Humidity — Bosch datasheet packing (H1/H3 = 1 byte; H4/H5 = 12-bit; H6 present)
dig_H1 = i2c.readfrom_mem(0x76, 0xA1, 1)[0]
dig_H2 = int.from_bytes(i2c.readfrom_mem(0x76, 0xE1, 2), "little")
if dig_H2 & 0x8000:
    dig_H2 = dig_H2 - 0x10000
dig_H3 = i2c.readfrom_mem(0x76, 0xE3, 1)[0]
e4, e5, e6 = i2c.readfrom_mem(0x76, 0xE4, 3)
dig_H4 = (e4 << 4) | (e5 & 0x0F)
if dig_H4 & 0x800:
    dig_H4 = dig_H4 - 0x1000
dig_H5 = (e6 << 4) | (e5 >> 4)
if dig_H5 & 0x800:
    dig_H5 = dig_H5 - 0x1000
dig_H6 = i2c.readfrom_mem(0x76, 0xE7, 1)[0]
if dig_H6 & 0x80:
    dig_H6 = dig_H6 - 0x100

print("Calibration loaded successfully")


def read_bme280():
    # ctrl_hum must be written before ctrl_meas to take effect (osrs_h = 1).
    i2c.writeto_mem(0x76, 0xF2, b"\x01")
    # Forced mode, temp+pressure 1x.
    i2c.writeto_mem(0x76, 0xF4, b"\x25")
    sleep(0.2)

    data = i2c.readfrom_mem(0x76, 0xF7, 8)

    p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
    h = (data[6] << 8) | data[7]

    var1 = ((t >> 3) - (dig_T1 << 1)) * dig_T2 >> 11
    var2 = (((((t >> 4) - dig_T1) * ((t >> 4) - dig_T1)) >> 12) * dig_T3) >> 14
    t_fine = var1 + var2
    temperature = (t_fine * 5 + 128) >> 8
    temperature = temperature / 100.0

    var1 = t_fine - 128000
    var2 = var1 * var1 * dig_P6
    var2 = var2 + ((var1 * dig_P5) << 17)
    var2 = var2 + (dig_P4 << 35)
    var1 = ((var1 * var1 * dig_P3) >> 8) + ((var1 * dig_P2) << 12)
    var1 = ((var1 + (1 << 47)) * dig_P1) >> 33

    if var1 == 0:
        pressure = 0
    else:
        pressure = 1048576 - p
        pressure = ((pressure << 31) - var2) * 3125 // var1
        var1 = (dig_P9 * (pressure >> 13) * (pressure >> 13)) >> 25
        var2 = (dig_P8 * pressure) >> 19
        pressure = ((pressure + var1 + var2) >> 15) + (dig_P7 << 4)
        pressure = pressure / 25600.0

    # Bosch BME280 humidity compensation
    v_x1 = t_fine - 76800
    v_x1 = (
        ((((h << 14) - (dig_H4 << 20) - (dig_H5 * v_x1)) + 16384) >> 15)
        * (
            (
                ((((v_x1 * dig_H6) >> 10) * (((v_x1 * dig_H3) >> 11) + 32768)) >> 10)
                + 2097152
            )
            * dig_H2
            + 8192
        )
        >> 14
    )
    v_x1 = v_x1 - (((((v_x1 >> 15) * (v_x1 >> 15)) >> 7) * dig_H1) >> 4)
    if v_x1 < 0:
        v_x1 = 0
    if v_x1 > 419430400:
        v_x1 = 419430400
    humidity = (v_x1 >> 12) / 1024.0
    if humidity > 100.0:
        humidity = 100.0
    if humidity < 0.0:
        humidity = 0.0

    return temperature, pressure, humidity


def send_station_id():
    """Station ID callout (Part 97: at least every 10 minutes).

    Serial-only for now. TODO(SX1262): TX ID_PAYLOAD over Waveshare Pico-LoRa
    once the HAT is stacked — do not init SPI here (would risk wedging boot
    without the radio present).
    """
    print(f"[ID] {ID_PAYLOAD}")


# Fire ID on first loop pass, then every ID_INTERVAL_MS thereafter.
next_id_ms = utime.ticks_ms()

while True:
    now = utime.ticks_ms()
    if utime.ticks_diff(now, next_id_ms) >= 0:
        try:
            send_station_id()
        except Exception as e:
            print("ID error:", e)
        next_id_ms = utime.ticks_add(now, ID_INTERVAL_MS)

    try:
        t, p, h = read_bme280()
        print(
            f"[{utime.ticks_ms() // 1000}s] Temp: {t:.2f}\u00b0C | Pressure: {p:.1f} hPa | Humidity: {h:.1f}%"
        )
    except Exception as e:
        print("Read error:", e)
    sleep(3.14)
