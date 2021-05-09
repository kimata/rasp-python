#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ADS-1015 を使って温度や湿度を取得するライブラリです．
#

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import sensor.ads1015
import pprint

class GROVE_TDS:
    NAME                = 'GROVE-TDS'
    DEV_ADDR            = 0x48 # 7bit

    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.adc = sensor.ads1015.ADS1015(bus, dev_addr)

    def ping(self):
        return self.adc.ping()

    def get_value(self):
        volt = self.adc.get_value()[0] / 1000.0
        tds = (133.42*volt*volt*volt - 255.86*volt*volt + 857.39*volt)*0.5

        return [ round(tds, 3) ]

    def get_value_map(self):
        value = self.get_value()

        return { 'tds': value[0] }

    
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.grove_tds
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    grove_tds = sensor.grove_tds.GROVE_TDS(I2C_BUS)

    ping = grove_tds.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(grove_tds.get_value_map())
