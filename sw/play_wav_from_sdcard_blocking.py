# The MIT License (MIT)
# Copyright (c) 2022 Mike Teachman
# https://opensource.org/licenses/MIT

# Purpose:  Play a WAV audio file out of a speaker or headphones
#
# - read audio samples from a WAV file on SD Card
# - write audio samples to an I2S amplifier or DAC module
# - the WAV file will play continuously in a loop until
#   a keyboard interrupt is detected or the board is reset
#
# blocking version
# - the write() method blocks until the entire sample buffer is written to the I2S interface

import os
from machine import I2S
from machine import Pin

from machine import SDCard

sd = SDCard(slot=1)  # sck=18, mosi=23, miso=19, cs=5
os.mount(sd, "/sd")

# ======= I2S CONFIGURATION =======
SCK_PIN = 33
WS_PIN = 32
SD_PIN = 16
I2S_ID = 0
BUFFER_LENGTH_IN_BYTES = 40000
# ======= I2S CONFIGURATION =======



# ======= AUDIO CONFIGURATION =======
WAV_FILE = "mic7.wav"
WAV_SAMPLE_SIZE_IN_BITS = 16
FORMAT = I2S.MONO
SAMPLE_RATE_IN_HZ = 22_050
# ======= AUDIO CONFIGURATION =======

audio_out = I2S(
    I2S_ID,
    sck=Pin(SCK_PIN),
    ws=Pin(WS_PIN),
    sd=Pin(SD_PIN),
    mode=I2S.TX,
    bits=WAV_SAMPLE_SIZE_IN_BITS,
    format=FORMAT,
    rate=SAMPLE_RATE_IN_HZ,
    ibuf=BUFFER_LENGTH_IN_BYTES,
)

wav = open("/sd/{}".format(WAV_FILE), "rb")
_ = wav.seek(44)  # advance to first byte of Data section in WAV file

# allocate sample array
# memoryview used to reduce heap allocation
wav_samples = bytearray(10000)
wav_samples_mv = memoryview(wav_samples)

# continuously read audio samples from the WAV file
# and write them to an I2S DAC
print("==========  START PLAYBACK ==========")
try:
    while True:
        num_read = wav.readinto(wav_samples_mv)
        # end of WAV file?
        if num_read == 0:
            # end-of-file, advance to first byte of Data section
            _ = wav.seek(44)
        else:
            _ = audio_out.write(wav_samples_mv[:num_read])
except (KeyboardInterrupt, Exception) as e:
    print("caught exception {} {}".format(type(e).__name__, e))

# cleanup
wav.close()

os.umount("/sd")
sd.deinit()

audio_out.deinit()
print("Done")