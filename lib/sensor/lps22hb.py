#!/usr/bin/env python
# -*- coding: utf-8 -*-

# LPS22HB を使って温度や湿度を取得するライブラリです．
#
# 作成時に使用したのは，秋月電子 の
#「ＬＰＳ２５Ｈ使用　気圧センサーモジュールＤＩＰ化キット」．
# http://akizukidenshi.com/catalog/g/gK-08338/

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class LPS22HB:
    NAME                = 'LPS22HB'
    
    DEV_ADDR		= 0x5C # 7bit
    REG_CTRL1		= 0x10
    
    REG_ID		= 0x0F
    REG_PRESS		= 0x28
    REG_FIFO		= 0x14

    RATE_ONE        	= 0x0 << 4
    RATE_1HZ        	= 0x1 << 4
    RATE_10HZ        	= 0x2 << 4
    RATE_25HZ        	= 0x3 << 4
    RATE_50HZ        	= 0x4 << 4
    RATE_70HZ        	= 0x5 << 4

    LPF_2               = 0x0 << 2
    LPF_9               = 0x2 << 2
    LPF_20              = 0x3 << 2

    MODE_BYPASS		= 0x0 << 5
    
    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)

    def ping(self):
        dev_id = None
        try:
            value = self.i2cbus.read(self.DEV_ADDR, 1, self.REG_ID)
            dev_id = struct.unpack('B', bytes(value))[0]
        except:
            pass

        return (dev_id == 0xB1)

    def enable(self):
        # Bypass Mode
        self.i2cbus.write(self.dev_addr, [self.REG_FIFO, self.MODE_BYPASS])
        # 70Hz で変換を行い 20 サンプルの平均を取る
        self.i2cbus.write(self.dev_addr, [self.REG_CTRL1, self.RATE_50HZ | self.LPF_20])

    def get_value(self):
        self.enable()
        time.sleep(0.5)
        
        value = self.i2cbus.read(self.DEV_ADDR, 3, self.REG_PRESS)
        press = struct.unpack('<I', value + b'\0')[0] / 4096

        return [ int(press) ]

    def get_value_map(self):
        value = self.get_value()

        return { 'press': value[0] }
    
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.lps22hb

    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    lps22hb = sensor.lps22hb.LPS22HB(I2C_BUS)
    ping = lps22hb.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(lps22hb.get_value_map())

