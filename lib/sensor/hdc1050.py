#!/usr/bin/env python
# -*- coding: utf-8 -*-

# HDC1050 を使って温度や湿度を取得するライブラリです．
#
# 作成時に使用したのは，Strawberry Linux の
#「HDC1050 １チップ温度・湿度センサ・モジュール」．
# http://strawberry-linux.com/catalog/items?code=81050

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class HDC1050:
    DEV_ADDR		= 0x40 # 7bit
    REG_TEMP		= 0x00
    REG_HUMI		= 0x01
    REG_CONF		= 0x02
    REG_ID		= 0xFF

    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)

    def ping(self):
        dev_id = 0
        try:
            self.i2cbus.write(self.DEV_ADDR, self.REG_ID)
            value = self.i2cbus.read(self.DEV_ADDR, 2, self.REG_ID)
            dev_id = struct.unpack('>H', bytes(value[0:2]))[0]
        except:
            pass

        return dev_id == 0x1050
    
    def get_value(self):
        self.i2cbus.write(self.dev_addr, self.REG_TEMP)
        time.sleep(0.05)
    
        value = self.i2cbus.read(self.DEV_ADDR, 4)

        temp = struct.unpack('>H', bytes(value[0:2]))[0]
        temp = float(temp)/65536*165 - 40

        humi = struct.unpack('>H', bytes(value[2:4]))[0]
        humi = float(humi)/65536*100

        return { 'temp': temp, 'humi': humi }


if __name__ == '__main__':
    # TEST Code
    import sensor.hdc1050
    I2C_BUS = 0x1 # Raspberry Pi

    hdc1050 = sensor.hdc1050.HDC1050(I2C_BUS)

    ping = hdc1050.ping()
    print('PING: %s' % ping)

    if (ping):
        value = hdc1050.get_value()
        print('TEMP: %.1f, HUMI: %.1f' % (value['temp'], value['humi']))
