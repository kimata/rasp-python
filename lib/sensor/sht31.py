#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SHT-31 を使って温度や湿度を取得するライブラリです．
#
# 作成時に使用したのは，Strawberry Linux の
#「SHT-31 １チップ温度・湿度センサ・モジュール」．
# https://strawberry-linux.com/support/80031/1870819

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class SHT31:
    NAME                = 'SHT-31'
    DEV_ADDR		= 0x44 # 7bit
    REG_MAESURE		= [0x24, 0x00]
    REG_STATUS		= [0xF3, 0x2D]

    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)

    def crc(self, msg):
        poly=0x31
        crc = 0xFF
    
        for data in bytearray(msg):
            crc ^= data
            for i in range(8):
                if crc & 0x80:
                    crc = (crc << 1 ) ^ poly
                else:
                    crc <<= 1
            crc &= 0xFF

        return crc
            
    def ping(self):
        value = '   '
        try:
            self.i2cbus.write(self.dev_addr, self.REG_STATUS)
            value = self.i2cbus.read(self.DEV_ADDR, 3)
        except:
            pass

        return bytearray(value[2:3])[0] == self.crc(value[0:2])
    
    def get_value(self):
        self.i2cbus.write(self.dev_addr, self.REG_MAESURE)
        time.sleep(0.05)
    
        value = self.i2cbus.read(self.DEV_ADDR, 6)

        if (bytearray(value[2:3])[0] != self.crc(value[0:2])) or \
           (bytearray(value[5:6])[0] != self.crc(value[3:5])):
            raise IOError('CRC unmatch')
        
        temp = -45 + (175 *  struct.unpack('>H', bytes(value[0:2]))[0]) / float(2**16 - 1)
        humi = 100 * struct.unpack('>H', bytes(value[3:5]))[0] / float(2**16 - 1)
        
        return [ round(temp, 4), round(humi, 1) ]

    def get_value_map(self):
        value = self.get_value()

        return { 'temp': value[0], 'humi': value[1] }


if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.sht31
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    sht31 = sensor.sht31.SHT31(I2C_BUS)

    ping = sht31.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(sht31.get_value_map())
