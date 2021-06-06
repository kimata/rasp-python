#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# EZO-pH を使って pH を取得するライブラリです．

import time
import struct
import sys
import traceback
import pprint

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class EZO_PH:
    NAME                = 'EZO-pH'

    DEV_ADDR            = 0x64 # 7bit

    RAM_CO2             = 0x08
    RAM_FIRM            = 0x62
    
    WRITE_RAM           = 0x1 << 4
    READ_RAM            = 0x2 << 4
    WRITE_EE            = 0x3 << 4
    READ_EE             = 0x4 << 4

    RETRY_COUNT         = 5
    
    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)

    def ping(self):
        try:
            self.exec_command('i')
            
            return True
        except:
            return False


    def get_value(self):
        value = self.exec_command('R')

        return float(value[1:].decode().rstrip('\x00'))

    # def exec_cal(self, point, value):
        # value = self.__exec_command(b'R')

        # return float(value[1:].decode().rstrip('\x00'))

    
    def exec_command(self, cmd):
        command = self.__compose_command(cmd.encode())

        self.i2cbus.write(self.dev_addr, command)

        time.sleep(1)

        return self.i2cbus.read(self.DEV_ADDR, 10)
    
    def __compose_command(self, text):
        command = list(struct.unpack('B'*len(text), text))
        return command
    
    def get_value_map(self):
        value = self.get_value()

        return { 'ph': value }
    
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.ezo_ph
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    ezo_ph = sensor.ezo_ph.EZO_PH(I2C_BUS)

    ping = ezo_ph.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(ezo_ph.get_value_map())

