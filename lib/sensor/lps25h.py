#!/usr/bin/env python
# -*- coding: utf-8 -*-

# LPS25H を使って温度や湿度を取得するライブラリです．
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

class LPS25H:
    NAME                = 'LPS25H'
    
    DEV_ADDR		= 0x5C # 7bit
    REG_CTRL1		= 0x20
    REG_CTRL2		= 0x21
    REG_FIFO		= 0x2E
    REG_RES		= 0x10
    REG_PRESS		= 0xA8 # auto increment
    
    REG_ID		= 0x0F

    POWER_ON        	= 0x80
    POWER_OFF    	= 0x00

    FIFO_ENABLE		= 0x40
    
    RATE_ONE        	= 0x0 << 4
    RATE_1HZ        	= 0x1 << 4
    RATE_7HZ        	= 0x2 << 4
    RATE_12HZ        	= 0x3 << 4
    RATE_25HZ        	= 0x4 << 4

    AVE_8        	= (0x0 << 2) | 0x0
    AVE_32        	= (0x1 << 2) | 0x1
    AVE_128        	= (0x2 << 2) | 0x2
    AVE_512        	= (0x3 << 2) | 0x3

    MODE_BYPASS		= 0x0 << 5
    MODE_STREAM		= 0x2 << 5
    MODE_MEAN		= 0x6 << 5

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

        return (dev_id == 0xBD) or (dev_id == 0xBB) # LPS25H or LPS331AP

    def enable(self):
        # 25Hz で変換を行い 8 サンプルの平均を取る
        self.i2cbus.write(self.dev_addr, [self.REG_RES, self.AVE_8])
        self.i2cbus.write(self.dev_addr, [self.REG_FIFO, self.MODE_MEAN])
        self.i2cbus.write(self.dev_addr, [self.REG_CTRL2, self.FIFO_ENABLE])
        self.i2cbus.write(self.dev_addr, [self.REG_CTRL1, self.POWER_ON | self.RATE_25HZ])
        
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
    import sensor.lps25h

    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    lps25h = sensor.lps25h.LPS25H(I2C_BUS)
    ping = lps25h.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(lps25h.get_value_map())

