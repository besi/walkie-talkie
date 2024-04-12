# 2024, Marco Klingmann

import os
import time
from machine import Pin
from machine import I2S

import network
import espnow

BOARDS = ("lolin", "pico32")
board = BOARDS[0] # 0: lolin, 1: pico32

# ======= PIN CONFIGURATION =======
SCK_PIN = 18
WS_PIN = 23
SD_MIC_PIN = 13 #serial data, mic
SD_SPEAKER_PIN = 5 #serial data, mic
TRANSMIT_BUTTON_PIN = 22
# ======= PIN CONFIGURATION =======

if board == "pico32":
    # ======= PIN CONFIGURATION =======
    SCK_PIN = 33
    WS_PIN = 32
    SD_MIC_PIN = 36 #serial data, mic
    SD_SPEAKER_PIN = 5 #serial data, mic
    TRANSMIT_BUTTON_PIN = 2
    # ======= PIN CONFIGURATION =======

# ==== I2S Config ====
I2S_ID = 0
BUFFER_LENGTH_IN_BYTES = 48000

# ======= AUDIO CONFIGURATION =======
SAMPLE_SIZE_IN_BITS = 16
FORMAT = I2S.MONO
SAMPLE_RATE_IN_HZ = 8000
# ======= AUDIO CONFIGURATION =======
SAMPLE_SIZE_IN_BYTES = SAMPLE_SIZE_IN_BITS // 8

audio_in = I2S(
    I2S_ID,
    sck=Pin(SCK_PIN),
    ws=Pin(WS_PIN),
    sd=Pin(SD_MIC_PIN),
    mode=I2S.RX,
    bits=SAMPLE_SIZE_IN_BITS,
    format=FORMAT,
    rate=SAMPLE_RATE_IN_HZ,
    ibuf=BUFFER_LENGTH_IN_BYTES,
)

audio_out = I2S(
    I2S_ID,
    sck=Pin(SCK_PIN),
    ws=Pin(WS_PIN),
    sd=Pin(SD_SPEAKER_PIN),
    mode=I2S.TX,
    bits=SAMPLE_SIZE_IN_BITS,
    format=FORMAT,
    rate=SAMPLE_RATE_IN_HZ,
    ibuf=BUFFER_LENGTH_IN_BYTES,
)

button = Pin(TRANSMIT_BUTTON_PIN, Pin.IN)

# === ESP Now ===

# A WLAN interface must be active to send()/recv()
sta = network.WLAN(network.STA_IF)  # Or network.AP_IF
sta.active(True)
sta.disconnect()      # For ESP8266

e_now = espnow.ESPNow()
e_now.active(True)
bcast = b'\xff\xff\xff\xff\xff\xff' # broadcast address
e_now.add_peer(bcast)
buffer_size = espnow.MAX_DATA_LEN

# allocate sample arrays
# memoryview used to reduce heap allocation in while loop
mic_samples = bytearray(buffer_size)
mic_samples_mv = memoryview(mic_samples)
out_samples = bytearray(buffer_size)
out_samples_mv = memoryview(out_samples)

#esp now mac address
sender_mac = bytearray(6)
e_now_received_data = [sender_mac, out_samples_mv]


# Main loop
while True:
    # Check if the button is pressed
    if button.value() == 1:  # Button pressed
        print("Started Sending")
        
        audio_in = I2S(
            I2S_ID,
            sck=Pin(SCK_PIN),
            ws=Pin(WS_PIN),
            sd=Pin(SD_MIC_PIN),
            mode=I2S.RX,
            bits=SAMPLE_SIZE_IN_BITS,
            format=FORMAT,
            rate=SAMPLE_RATE_IN_HZ,
            ibuf=BUFFER_LENGTH_IN_BYTES,
        )
          
        start_time = time.ticks_ms() # get millisecond counter
        delta_time = 0
        while delta_time < 1000 or button.value() == 1:
            #print("transmission")
            
            num_bytes_read_from_mic = audio_in.readinto(mic_samples_mv)
            if num_bytes_read_from_mic > 0:
                bytes_to_send = min(num_bytes_read_from_mic, espnow.MAX_DATA_LEN)
                if (num_bytes_read_from_mic > espnow.MAX_DATA_LEN):
                    print(f"Some mic data is skipped!! {num_bytes_read_from_mic}")
                    
                e_now.send(bcast, mic_samples_mv[:bytes_to_send], False)
                
            
            delta_time = time.ticks_diff(time.ticks_ms(), start_time) 
    
    else:
        print(" ::: Start Receiving :::")
        
        audio_out = I2S(
            I2S_ID,
            sck=Pin(SCK_PIN),
            ws=Pin(WS_PIN),
            sd=Pin(SD_SPEAKER_PIN),
            mode=I2S.TX,
            bits=SAMPLE_SIZE_IN_BITS,
            format=FORMAT,
            rate=SAMPLE_RATE_IN_HZ,
            ibuf=BUFFER_LENGTH_IN_BYTES,
        )
        
        start_time = time.ticks_ms()
        delta_time = 0
        while delta_time < 1000 or button.value() == 0:
            #print("receiving")
            
            if e_now.any():
                num_bytes_received = e_now.recvinto(e_now_received_data, 50)
                if num_bytes_received > 0:
                    _ = audio_out.write(out_samples_mv[:num_bytes_received])
                
                
            delta_time = time.ticks_diff(time.ticks_ms(), start_time) 


audio_in.deinit()
audio_out.deinit()
