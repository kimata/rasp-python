#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))


class BP35A1:
    def __init__(self, ser):
        self.ser = ser
        a = 1

    def setopt(self):
        ser.write("ROPT\r\n")



if __name__ == '__main__':
    # TEST Code
    import serial
    import pprint
    import meter.bp35a1

    ser = serial.Serial(, 115200)

    bp35a1 = meter.bp35a1.BP35A1(ser)
    


