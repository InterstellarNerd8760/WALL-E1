from machine import Pin, I2C
import time

# WALL-E1 BME280 wiring diagnostic
# Black: SDA -> GP16 (physical pin 21)
# Purple: SCL -> GP17 (physical pin 22)
# Gold: GND
# White: 3V3
#
# This test does not initialize or use the LoRa radio.

ADDRESS = 0x76
EXPECTED_CHIP_ID = 0x60

i2c = I2C(0, sda=Pin(16), scl=Pin(17), freq=100000)

print("\nWALL-E1 BME280 DIAGNOSTIC")
print("I2C scan:", [hex(addr) for addr in i2c.scan()])

if ADDRESS not in i2c.scan():
    raise RuntimeError("BME280 not detected at address 0x76")

print("BME280 address detected.")

try:
    chip_id = i2c.readfrom_mem(ADDRESS, 0xD0, 1)[0]
    print("Chip ID:", hex(chip_id))

    if chip_id != EXPECTED_CHIP_ID:
        raise RuntimeError("Unexpected chip ID; expected 0x60 for BME280")

    print("Sensor register communication successful.")
    print("Starting repeated communication test...")

    while True:
        # Read the sensor ID repeatedly to check connection stability.
        chip_id = i2c.readfrom_mem(ADDRESS, 0xD0, 1)[0]

        if chip_id != EXPECTED_CHIP_ID:
            print("Unexpected chip ID:", hex(chip_id))
        else:
            print("BME280 connection OK")

        time.sleep(5)

except OSError as e:
    print("I2C communication failed:", e)
    raise
