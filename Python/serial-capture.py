#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on July 2025

@author: bernardo
https://makersportal.com/blog/2018/2/25/python-datalogger-reading-the-serial-output-from-arduino-to-analyze-data-using-pyserial

"""
import serial
import numpy as np

ser = serial.Serial('/dev/ttyLoopRd', 921600, timeout=2)

while True:
    try:
        ser.reset_input_buffer()
        # ser_bytes= ser.readline()
        ser_bytes = ser.read(4)        # read up to ten bytes (timeout)
        val = np.frombuffer(ser_bytes, dtype=np.int32)
        print(f"Val: {val}")
    except (KeyboardInterrupt, SystemExit):
        print("Keyboard Interrupt")
        break
    #except:
    #    pass
    
ser.close()         
