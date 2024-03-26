import machine
from machine import SoftI2C


i2c = SoftI2C(freq=50000, scl=machine.Pin(16), sda=machine.Pin(13))

i2c.scan()

while True:
    i2c.readfrom(0x1D, 7)
    

