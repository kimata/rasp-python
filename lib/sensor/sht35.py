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

import smbus

class SHT35:
    NAME                = 'SHT-35'
    DEV_ADDR		= 0x44 # 7bit
    
    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = smbus.SMBus(bus)
        self.is_init = False

    def init(self):
        # periodic, 1mps, repeatability high
        self.i2cbus.write_byte_data(self.dev_addr, 0x21, 0x30)
        self.is_init = True
        time.sleep(0.01)

    def crc(self, data):
        crc = 0xff
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
            self.i2cbus.write_byte_data(self.dev_addr, 0xF3, 0x2D)
            data = self.i2cbus.read_i2c_block_data(self.dev_addr, 0x00, 3)

            return self.crc(data[0:2]) == data[2]
        except:
            return False
    
    def get_value(self):
        if not self.is_init:
            self.init()

        self.i2cbus.write_byte_data(self.dev_addr, 0xE0, 0x00)
    
        data = self.i2cbus.read_i2c_block_data(self.dev_addr, 0x00, 6)

        if (self.crc(data[0:2]) != data[2]) or (self.crc(data[3:5]) != data[5]):
            raise IOError("ERROR: CRC unmatch.")
        temp = -45 + 175.0 * ((data[0] << 8) | data[1]) / (pow(2, 16) - 1)
        humi = 100.0 * ((data[3] << 8) | data[4]) / (pow(2, 16) - 1)

        return [ round(temp, 2), round(humi, 2) ]

    def get_value_map(self):
        value = self.get_value()

        return { 'temp': value[0], 'humi': value[1] }

    
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.sht35
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    sht35 = sensor.sht35.SHT35(I2C_BUS)

    ping = sht35.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(sht35.get_value_map())
