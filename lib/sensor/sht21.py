#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SHT-35 を使って温度や湿度を取得するライブラリです．
#
# 作成時に使用したのは，Tindie の
#「SHT35-D (Digital) Humidity & Temperature Sensor」．
# https://www.tindie.com/products/closedcube/sht35-d-digital-humidity-temperature-sensor/

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class SHT21:
    NAME                = 'SHT-21'
    DEV_ADDR		= 0x40 # 7bit
    REG_USER		= 0xE7
    REG_MEASURE_TEMP	= 0xF3
    REG_MEASURE_HUMI	= 0xF5

    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)

    def crc(self, data):
        crc = 0x00
        for s in data:
            crc ^= s
            for i in range(8):
                if crc & 0x80:
                    crc <<= 1
                    crc ^= 0x131
                else:
                    crc <<= 1
        return crc

    def ping(self):
        try:
            value = self.i2cbus.read(self.DEV_ADDR, 1, self.REG_USER)
            return (value[0] & 0x02) != 0

        except:
            return False
    
    def get_value(self):
        self.i2cbus.write(self.DEV_ADDR, [self.REG_MEASURE_TEMP])
        time.sleep(0.1)
        value = self.i2cbus.read(self.DEV_ADDR, 3)

        if (self.crc(value[0:2]) != value[2]):
            raise IOError("ERROR: CRC unmatch.")
        
        temp = -46.85 + 175.72 * int.from_bytes(value[0:2], byteorder='big') / pow(2, 16)

        self.i2cbus.write(self.DEV_ADDR, [self.REG_MEASURE_HUMI])
        time.sleep(0.1)
        value = self.i2cbus.read(self.DEV_ADDR, 3)

        if (self.crc(value[0:2]) != value[2]):
            raise IOError("ERROR: CRC unmatch.")

        humi = -6 + 125.0 * int.from_bytes(value[0:2], byteorder='big') / pow(2, 16)
        
        return [ round(temp, 2), round(humi, 2) ]

    def get_value_map(self):
        value = self.get_value()

        return { 'temp': value[0], 'humi': value[1] }

    
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.sht21
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    sht21 = sensor.sht21.SHT21(I2C_BUS)

    ping = sht21.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(sht21.get_value_map())
