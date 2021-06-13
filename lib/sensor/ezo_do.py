#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# EZO-DO を使って pH を取得するライブラリです．

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

class EZO_DO:
    NAME                = 'EZO-DO'

    DEV_ADDR		= 0x68 # 7bit
    
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

        return round(float(value[1:].decode().rstrip('\x00')), 3)

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

        return { 'do': value }
    
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.ezo_do
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    ezo_do = sensor.ezo_do.EZO_DO(I2C_BUS)

    ping = ezo_do.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(ezo_do.get_value_map())
#        pprint.pprint(ezo_do.exec_command('Cal'))
        # pprint.pprint(ezo_ph.exec_command('Cal,?'))
