#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# INA226 を使って電圧・電流・電力を取得するライブラリです．
#
# 作成時に使用したのは，Strawberry Linux の
#「INA226 I2Cディジタル電流・電圧・電力計モジュール」．
# https://strawberry-linux.com/catalog/items?code=12031

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import smbus

class INA226:
    NAME                = 'INA226'
    DEV_ADDR		= 0x40 # 7bit
    
    def __init__(self, bus, dev_addr=DEV_ADDR, prefix=''):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = smbus.SMBus(bus)
        self.prefix = prefix
        self.is_init = False

    def init(self):
        # shunt register is 2mohm.
        self.i2cbus.write_i2c_block_data(self.dev_addr, 0x05, [0x0A, 0x00])
        # 128 average, 8.2ms, continuous
        val = (0x04 << 9) | (0x07 << 6) | (0x07 << 3) | 0x07
        self.i2cbus.write_i2c_block_data(self.dev_addr, 0x00,
                                         [ (val >> 8) & 0xFF, (val >> 0) & 0xFF ])
        
        self.is_init = True
        time.sleep(1.1)

    def ping(self):
        try:
            data = self.i2cbus.read_i2c_block_data(self.dev_addr, 0xFF, 2)
            return (data[0] == 0x22) and (data[1] == 0x60)
        except:
            return False
    
    def get_value(self):
        if not self.is_init:
            self.init()

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, 0x02, 2)
        volt = (data[0] << 8 | data[1]) * 1.25 / 1000.0

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, 0x04, 2)
        if ((data[0] >> 7) == 1):
            curr = -1 * (0x10000 - (data[0] << 8 | data[1])) / 1000
        else:
            curr = (data[0] << 8 | data[1]) / 1000.0

        data = self.i2cbus.read_i2c_block_data(self.dev_addr, 0x03, 2)
        power = (data[0] << 8 | data[1]) * 25 / 1000.0

        return [ round(volt, 3), round(curr, 3), round(power, 3) ]

    def get_value_map(self):
        value = self.get_value()

        return {
            (self.prefix + 'voltage'): value[0],
            (self.prefix + 'current'): value[1],
            (self.prefix + 'power'): value[2]
        }


if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.ina226
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    ina226 = sensor.ina226.INA226(I2C_BUS)

    ping = ina226.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(ina226.get_value_map())
