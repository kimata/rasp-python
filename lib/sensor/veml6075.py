#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# VEML6075 を使って紫外線を計測するライブラリです．

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class VEML6075:
    NAME                = 'VEML6075'
    DEV_ADDR		= 0x10 # 7bit
    REG_UV_CONF         = 0x00
    REG_UVA             = 0x07
    REG_UVB             = 0x09
    REG_UVCOMP1         = 0x0A
    REG_UVCOMP2         = 0x0B
    REG_DEVID           = 0x0C
    
    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)
        self.is_init = False

    def init(self):
        # 100ms
        self.i2cbus.write(self.dev_addr, [self.REG_UV_CONF, 0x10, 0x00])
        time.sleep(1.1)

        self.is_init = True

    def ping(self):
        try:
            data = self.i2cbus.read(self.dev_addr, 2, self.REG_DEVID)

            return int.from_bytes(data, byteorder='little') == 0x26
        except:
            return False
    
    def get_value(self):
        if not self.is_init:
            self.init()

        data = self.i2cbus.read(self.dev_addr, 2, self.REG_UVA)
        uva = int.from_bytes(data, byteorder='little')

        data = self.i2cbus.read(self.dev_addr, 2, self.REG_UVB)
        uvb = int.from_bytes(data, byteorder='little')

        data = self.i2cbus.read(self.dev_addr, 2, self.REG_UVCOMP1)
        uvcomp1 = int.from_bytes(data, byteorder='little')

        data = self.i2cbus.read(self.dev_addr, 2, self.REG_UVCOMP2)
        uvcomp2 = int.from_bytes(data, byteorder='little')

        uva_calc = uva - ((2.22 * 1.0 * uvcomp1) / 1.0) - ((1.33 * 1.0 * uvcomp2) / 1.0)
        uvb_calc = uvb - ((2.95 * 1.0 * uvcomp1) / 1.0) - ((1.75 * 1.0 * uvcomp2) / 1.0)
        uvi = ((uva_calc * 0.001461) + (uvb_calc * 0.002591)) / 2

        return [ round(uva_calc, 2), round(uvb_calc, 1), round(uvi, 1) ]

    def get_value_map(self):
        value = self.get_value()

        return {
            'uva': value[0],
            'uvb': value[1],
            'uvi': value[2],
        }


if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.veml6075
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    veml6075 = sensor.veml6075.VEML6075(I2C_BUS)

    ping = veml6075.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(veml6075.get_value_map())
