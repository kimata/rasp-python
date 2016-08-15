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

    RAM_CO2		= 0x08
    RAM_ID		= 0x2C
    
    WRITE_RAM		= 0x1 << 4
    READ_RAM		= 0x2 << 4
    WRITE_EE		= 0x3 << 4
    READ_EE		= 0x4 << 4
    
    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)

    def ping(self):
        try:
            command = [ self.READ_RAM|0x3, 0x00, self.RAM_CO2 ]
            command = self.__compose_command(command)

            self.i2cbus.write(self.dev_addr, *command)

            time.sleep(0.05)

            value = self.i2cbus.read(self.DEV_ADDR, 5)
        
            if list(bytearray(value)) != \
               self.__compose_command(list(bytearray(value))[0:4]):
                raise Exception('invalid sum')
            return True
        except:
            return False
        
    def __compose_command(self, command):
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

    ping = k30.ping()
    print('PING: %s' % ping)

    if (ping):
        print('CO2: %d' % k30.get_value())
