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
    DEV_ADDR            = 0x4A # 7bit

    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.adc = sensor.ads1015.ADS1015(bus, dev_addr)
        self.adc.set_mux(self.adc.REG_CONFIG_MUX_0G)
        self.adc.set_pga(self.adc.REG_CONFIG_FSR_2048)

    def ping(self):
        return self.adc.ping()

    def get_value(self, temp=25.0):
        volt = self.adc.get_value()[0] / 1000.0
        tds = (133.42*volt*volt*volt - 255.86*volt*volt + 857.39*volt)*0.5
        tds /= 1 + 0.018 * (temp-25) # 0.018 は実測データから算出

        return [ round(tds, 3) ]

    def get_value_map(self, temp=25.0):
        value = self.get_value(temp)

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
