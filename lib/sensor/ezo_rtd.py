#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# EZO-RTD を使って水温を取得するライブラリです．

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

class EZO_RTD:
    NAME                = 'EZO-RTD'

    DEV_ADDR		= 0x66 # 7bit

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

        return { 'temp': value }
    
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.ezo_rtd
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    ezo_rtd = sensor.ezo_rtd.EZO_RTD(I2C_BUS)

    ping = ezo_rtd.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(ezo_rtd.get_value_map())

