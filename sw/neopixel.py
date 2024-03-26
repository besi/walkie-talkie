import machine
import neopixel
import time

np = neopixel.NeoPixel(machine.Pin(7), 1)

blue = 0


while True:
    np[0] = (0, 0, blue)
    blue = blue + 1
    np.write()
    time.sleep(0.1)
    if blue >= 100:
        blue = 0

