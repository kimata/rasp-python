#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# VEML7700 を使って照度(LUX)を取得するライブラリです．

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class VEML7700:
    NAME                = 'VEML7700'

    DEV_ADDR            = 0x10 # 7bit

    REG_ALS_CONF        = 0x00
    REG_ALS             = 0x04

    ALS_GAIN_1D8X       = 0x02 << 11

    ALS_IT_100MS        = 0x00 << 6
    ALS_IT_25MS         = 0x0C << 6

    ALS_SD_POWER_ON     = 0x00 << 0
    ALS_SD_POWER_OFF    = 0x01 << 0

    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)
        self.gain = self.ALS_GAIN_1D8X
        self.integ = self.ALS_IT_25MS

    def enable(self):
        value = self.gain | self.integ | self.ALS_SD_POWER_ON

        self.i2cbus.write(self.dev_addr,
                          [self.REG_ALS_CONF, (value >> 0) & 0xFF, (value >> 8) & 0xFF ])

    def disable(self):
        value = self.gain | self.integ | self.ALS_SD_POWER_OFF

        self.i2cbus.write(self.dev_addr,
                          [self.REG_ALS_CONF, (value >> 0) & 0xFF, (value >> 8) & 0xFF ])

    def set_integ(self, integ):
        self.integ = integ

    def set_gain(self, gain):
        self.gain = gain

    def wait(self):
        if self.integ == self.ALS_IT_25MS:
            time.sleep(0.025 + 0.1)
        elif self.integ == self.ALS_IT_100MS:
            time.sleep(0.100 + 0.1)

    def ping(self):
        try:
            value = self.i2cbus.read(self.DEV_ADDR, 2, self.REG_ALS_CONF)
            return True
        except:
            pass

        return False
    
    def get_value_impl(self):
        self.enable()
        self.wait()

        value = self.i2cbus.read(self.dev_addr, 2, self.REG_ALS)

        self.disable()

        als = int.from_bytes(value, byteorder='little')

        if self.integ == self.ALS_IT_25MS:
            als *= 1.8432
        elif self.integ == self.ALS_IT_100MS:
            als *= 0.4608

        return [ als ];

    def get_value(self):
        value = self.get_value_impl()

        if value[0] < 1000:
            self.set_integ(self.ALS_IT_100MS)
            return self.get_value_impl()
        else:
            return value

    def get_value_map(self):
        value = self.get_value()

        return { 'lux': value[0] }

        
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.veml7700
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    veml7700 = sensor.veml7700.VEML7700(I2C_BUS)
    ping = veml7700.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(veml7700.get_value_map())
