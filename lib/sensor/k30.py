#!/usr/bin/env python
# -*- coding: utf-8 -*-

# K30 を使って温度や湿度を取得するライブラリです．
#
# 作成時に使用したのは，Strawberry Linux の
#「K30 １チップ温度・湿度センサ・モジュール」．
# http://strawberry-linux.com/catalog/items?code=81050

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class K30:
    DEV_ADDR		= 0x68 # 7bit
    REG_TEMP		= 0x00
    REG_HUMI		= 0x01
    REG_CONF		= 0x02
    REG_ID		= 0xFF

    RAM_CO2		= 0x08
    EE_METER_CTRL	= 0x03
    
    WRITE_RAM		= 0x1 << 4
    READ_RAM		= 0x2 << 4
    WRITE_EE		= 0x3 << 4
    READ_EE		= 0x4 << 4
    
    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)

    # def ping(self):
    #     dev_id = 0
    #     # try:
    #     self.i2cbus.write(self.DEV_ADDR, self.REG_ID)
    #     value = self.i2cbus.read(self.DEV_ADDR, 2, self.REG_ID)
    #     dev_id = struct.unpack('>H', bytes(value[0:2]))[0]
    #     # except:
    #     #     pass

    #     return dev_id == 0x1050

    def __compose_command(self, command):
        # print("------")
        # print(command)
        # print("------")
        
        return command + [sum(command)]
    
    def get_value(self):
        command = [ self.READ_RAM|0x2, 0x00, self.RAM_CO2 ]
        command = self.__compose_command(command)

        self.i2cbus.write(self.dev_addr, *command)

        time.sleep(0.05)

        value = self.i2cbus.read(self.DEV_ADDR, 4)

        if (list(bytearray(value))[0] & 0x1) != 0x1:
            raise Exception('command incomplete')
        
        if list(bytearray(value)) != \
           self.__compose_command(list(bytearray(value))[0:3]):
            raise Exception('invalid sum')

        co2 = struct.unpack('>H', bytes(value[1:3]))[0]
        return co2

if __name__ == '__main__':
    # TEST Code
    import sensor.k30
    I2C_BUS = 0x1 # Raspberry Pi

    k30 = sensor.k30.K30(I2C_BUS)

    # ping = k30.ping()
    # print('PING: %s' % ping)
    
    ping = True
    
    if (ping):
        print('CO2: %d' % k30.get_value())
