from machine import Pin, I2C
from time import sleep

# WALL-E1 BME280 measurement test
# Black: SDA -> GP16 (physical pin 21)
# Purple: SCL -> GP17 (physical pin 22)
# Gold: GND
# White: 3V3
#
# Sensor only: no GPS, LoRa, or flight logic.

ADDRESS = 0x76
EXPECTED_CHIP_ID = 0x60
SAMPLE_INTERVAL_S = 5

i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)


def read_u16(register):
    return int.from_bytes(i2c.readfrom_mem(ADDRESS, register, 2), "little")


def read_s16(register):
    value = read_u16(register)
    if value & 0x8000:
        value -= 0x10000
    return value


def load_calibration():
    # Temperature coefficients
    cal = {}
    cal["T1"] = read_u16(0x88)
    cal["T2"] = read_s16(0x8A)
    cal["T3"] = read_s16(0x8C)

    # Pressure coefficients
    cal["P1"] = read_u16(0x8E)
    for name, register in (
        ("P2", 0x90), ("P3", 0x92), ("P4", 0x94), ("P5", 0x96),
        ("P6", 0x98), ("P7", 0x9A), ("P8", 0x9C), ("P9", 0x9E)
    ):
        cal[name] = read_s16(register)

    # Humidity coefficients (Bosch datasheet register layout)
    cal["H1"] = i2c.readfrom_mem(ADDRESS, 0xA1, 1)[0]
    cal["H2"] = read_s16(0xE1)
    cal["H3"] = i2c.readfrom_mem(ADDRESS, 0xE3, 1)[0]

    e4, e5, e6 = i2c.readfrom_mem(ADDRESS, 0xE4, 3)
    h4 = (e4 << 4) | (e5 & 0x0F)
    if h4 & 0x800:
        h4 -= 0x1000
    h5 = (e6 << 4) | (e5 >> 4)
    if h5 & 0x800:
        h5 -= 0x1000
    cal["H4"] = h4
    cal["H5"] = h5

    h6 = i2c.readfrom_mem(ADDRESS, 0xE7, 1)[0]
    if h6 & 0x80:
        h6 -= 0x100
    cal["H6"] = h6

    return cal


def read_measurements(cal):
    # Set humidity oversampling first; then start one forced measurement.
    i2c.writeto_mem(ADDRESS, 0xF2, b"\x01")
    # Temperature x1, pressure x1, forced mode.
    i2c.writeto_mem(ADDRESS, 0xF4, b"\x25")
    sleep(0.1)

    data = i2c.readfrom_mem(ADDRESS, 0xF7, 8)

    raw_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    raw_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
    raw_h = (data[6] << 8) | data[7]

    # Temperature compensation; t_fine is also used by pressure/humidity.
    var1 = ((raw_t >> 3) - (cal["T1"] << 1)) * cal["T2"] >> 11
    var2 = (((((raw_t >> 4) - cal["T1"]) ** 2) >> 12) * cal["T3"]) >> 14
    t_fine = var1 + var2
    temperature_c = ((t_fine * 5 + 128) >> 8) / 100.0

    # Pressure compensation (Bosch BME280 integer algorithm).
    var1 = t_fine - 128000
    var2 = var1 * var1 * cal["P6"]
    var2 += (var1 * cal["P5"]) << 17
    var2 += cal["P4"] << 35
    var1 = ((var1 * var1 * cal["P3"]) >> 8) + ((var1 * cal["P2"]) << 12)
    var1 = ((var1 + (1 << 47)) * cal["P1"]) >> 33

    if var1 == 0:
        raise ValueError("Invalid pressure calibration (P1 produced zero divisor)")

    pressure = 1048576 - raw_p
    pressure = ((pressure << 31) - var2) * 3125 // var1
    var1 = (cal["P9"] * (pressure >> 13) * (pressure >> 13)) >> 25
    var2 = (cal["P8"] * pressure) >> 19
    pressure = ((pressure + var1 + var2) >> 15) + (cal["P7"] << 4)
    pressure_hpa = (pressure / 256.0) / 100.0

    # Humidity compensation (Bosch BME280 datasheet algorithm).
    v = t_fine - 76800
    v = (
        ((((raw_h << 14) - (cal["H4"] << 20) - (cal["H5"] * v)) + 16384) >> 15)
        * (
            (
                ((((v * cal["H6"]) >> 10) * (((v * cal["H3"]) >> 11) + 32768)) >> 10)
                + 2097152
            )
            * cal["H2"] + 8192
        )
        >> 14
    )
    v -= (((((v >> 15) * (v >> 15)) >> 7) * cal["H1"]) >> 4)
    if v < 0:
        v = 0
    if v > 419430400:
        v = 419430400
    humidity_pct = (v >> 12) / 1024.0
    humidity_pct = max(0.0, min(100.0, humidity_pct))

    return temperature_c, pressure_hpa, humidity_pct


print("\nWALL-E1 BME280 MEASUREMENT TEST")
print("I2C scan:", [hex(addr) for addr in i2c.scan()])

if ADDRESS not in i2c.scan():
    raise RuntimeError("BME280 not detected at 0x76")

chip_id = i2c.readfrom_mem(ADDRESS, 0xD0, 1)[0]
print("Chip ID:", hex(chip_id))
if chip_id != EXPECTED_CHIP_ID:
    raise RuntimeError("Expected BME280 chip ID 0x60")

print("Loading sensor calibration...")
calibration = load_calibration()
print("Calibration loaded. Reading measurements every", SAMPLE_INTERVAL_S, "seconds.")
print("Press Ctrl+C in Thonny to stop.\n")

sample = 0
while True:
    sample += 1
    try:
        temp, pressure, humidity = read_measurements(calibration)
        print("Sample", sample)
        print("  Temperature: {:.2f} C".format(temp))
        print("  Pressure:    {:.2f} hPa".format(pressure))
        print("  Humidity:    {:.2f} %".format(humidity))
    except OSError as error:
        print("I2C read error:", error)
    except Exception as error:
        print("Measurement error:", error)

    print()
    sleep(SAMPLE_INTERVAL_S)
