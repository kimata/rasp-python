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

import i2cbus
import pprint

class ADS1015:
    NAME                = 'ADS1015'
    DEV_ADDR            = 0x48 # 7bit
    REG_CONFIG          = 0x01
    REG_VALUE           = 0x00

    REG_CONFIG_FSR_0256 = 5
    REG_CONFIG_FSR_2048 = 2

    REG_CONFIG_MUX_01   = 0
    REG_CONFIG_MUX_0G   = 4

    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)
        self.mux = self.REG_CONFIG_MUX_01
        self.pga = self.REG_CONFIG_FSR_0256

    def init(self):
        os = 1
        self.i2cbus.write(
            self.dev_addr,
            [self.REG_CONFIG, (os << 7) | (self.mux << 4) | (self.pga << 1), 0x03]
        )

    def set_mux(self, mux):
        self.mux = mux

    def set_pga(self, pga):
        self.pga = pga

    def ping(self):
        try:
            value = self.i2cbus.read(self.dev_addr, 2, self.REG_CONFIG)
            return value[0] != 0
        except:
            return False

    def get_value(self):
        self.init()
        time.sleep(0.1)
        self.i2cbus.write(self.dev_addr, [self.REG_VALUE])

        value = self.i2cbus.read(self.dev_addr, 2)
        raw = int.from_bytes(value, byteorder='big', signed=True)
        if self.pga == self.REG_CONFIG_FSR_0256:
            mvolt = raw * 7.8125 / 1000
        elif self.pga == self.REG_CONFIG_FSR_2048:
            mvolt = raw * 62.5 / 1000

        return [ round(mvolt, 3) ]

    def get_value_map(self):
        value = self.get_value()

        return { 'mvolt': value[0] }

    
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.ads1015
    I2C_BUS = 0x0 # I2C のバス番号 (Raspberry Pi は 0x1)

    ads1015 = sensor.ads1015.ADS1015(I2C_BUS)

    ping = ads1015.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(ads1015.get_value_map())
