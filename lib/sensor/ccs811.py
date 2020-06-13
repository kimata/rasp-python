#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# CCS811 を使って TVOC 濃度を取得するライブラリです．
#
# 作成時に使用したのは，Strawberry Linux の
#「CCS811 エアークオリティセンサモジュール」．
# https://strawberry-linux.com/catalog/items?code=11811

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class CCS811:
    NAME                = 'CCS811'
    DEV_ADDR		= 0x5A # 7bit
    
    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)
        self.is_init = False

    def init(self):
        data = self.i2cbus.read(self.dev_addr, 1, 0x00)
        data = int.from_bytes(data, byteorder='big')

        if (data & 0x08) == 0:
            self.i2cbus.write(self.dev_addr, [0xF4])
            self.i2cbus.write(self.dev_addr, [0x01, 0x10])

        time.sleep(1.1)

        self.is_init = True

    def ping(self):
        try:
            data = self.i2cbus.read(self.dev_addr, 1, 0x20)

            return int.from_bytes(data, byteorder='big') == 0x81
        except:
            return False
    
    def get_value(self):
        if not self.is_init:
            self.init()

        data = self.i2cbus.read(self.dev_addr, 8, 0x02)

        return [ (data[0] << 8 | data[1]), (data[2] << 8 | data[3]) ]
        

    def get_value_map(self):
        value = self.get_value()

        return {
            'eco2': value[0],
            'tvoc': value[1],
        }


if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.ccs811
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    ccs811 = sensor.ccs811.CCS811(I2C_BUS)

    ping = ccs811.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(ccs811.get_value_map())
