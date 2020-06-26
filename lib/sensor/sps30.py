#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPS30 を使って TVOC 濃度を取得するライブラリです．
#
# 作成時に使用したのは，Strawberry Linux の
#「SPS30 エアークオリティセンサモジュール」．
# https://strawberry-linux.com/catalog/items?code=11811

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus
import pprint

class SPS30:
    NAME                = 'SPS30'
    DEV_ADDR		= 0x69 # 7bit
    
    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)
        self.is_init = False

    def init(self):
        self.start_measure()
        self.is_init = True
        time.sleep(0.1) 

    def ping(self):
        try:
            self.i2cbus.write(self.dev_addr, [0xD1, 0x00])
            data = self.i2cbus.read(self.dev_addr, 2)

            return int.from_bytes(data, byteorder='big') > 0x0200
        except:
            return False

    def __crc(self, msg):
        poly = 0x31
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
        
    def __compose_command(self, command):
        return command + [self.__crc(command[2:])]

    def start_measure(self):
        command = [0x00, 0x10, 0x03, 0x00 ]
        command = self.__compose_command(command)
        self.i2cbus.write(self.dev_addr, command)
    
    def stop_measure(self):
        # Stop measurement
        self.i2cbus.write(self.dev_addr, [0x01, 0x04 ])
    
    def wait_measure(self):
        for i in range(10):
            # Check data ready
            self.i2cbus.write(self.dev_addr, [0x02, 0x02])
            data = self.i2cbus.read(self.dev_addr, 3)
            if data[2] != self.__crc(list(data[0:2])):
                raise IOError('CRC unmatch')

            if (data[1] == 1):
                return

            time.sleep(0.1) 

        raise IOError('Timeeout measurement')

    def parse_value(self, data):
        for i in range(20):
            if (data[(i*3)+2] != self.__crc(list(data[(i*3):((i*3)+2)]))):
                raise IOError('CRC unmatch')

        value = []
        for i in range(10):
            value.append(
                struct.unpack('>f', data[(i*6):((i*6)+2)] + data[((i*6)+3):((i*6)+5)])[0]
            )
        return value
    
    def get_value(self):
        if not self.is_init:
            self.init()

        self.wait_measure()

        self.i2cbus.write(self.dev_addr, [0x03, 0x00])
        data = self.i2cbus.read(self.dev_addr, 60)

        return self.parse_value(data)

    def get_value_map(self):
        value = self.get_value()

        label = [
            'mass_pm1r0', 'mass_pm2r5', 'mass_pm4r0', 'mass_pm10r0',
            'num_pm0r5', 'num_pm1r0', 'num_pm2r5', 'num_pm4r0', 'num_pm10r0',
            'typ_size'
        ]

        return { label[i]: value[i] for i in range(10) }


if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.sps30
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    sps30 = sensor.sps30.SPS30(I2C_BUS)

    ping = sps30.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(sps30.get_value_map())
