#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SGP40 を使って VOC を取得するライブラリです．

import time
import struct
import os
import pickle
    
if __name__ == '__main__':
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus
from dfrobot.DFRobot_SGP40_VOCAlgorithm import DFRobot_VOCAlgorithm
import pprint

class SGP40:
    NAME                = 'SGP40'
    DEV_ADDR		= 0x59 # 7bit
    DUMP_FILE           = '/dev/shm/voc_algorithm.dump'

    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)
        try:
            if os.path.exists(self.DUMP_FILE):
                with open(self.DUMP_FILE, 'rb') as f:
                    self.voc_algo = pickle.load(f)
                    return
        except:
            pass
        self.voc_algo = DFRobot_VOCAlgorithm()
        self.voc_algo.vocalgorithm_init()

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
            self.i2cbus.write(self.dev_addr, [ 0x36, 0x82 ])
            time.sleep(0.001)
            data = self.i2cbus.read(self.DEV_ADDR, 9)

            self.decode_data(data)

            return True
        except:
            return False

    def decode_data(self, data):
        decoded = b''
        for word in [data[i:i+3] for i in range(0,len(data),3)]:
            if self.crc(word[0:2]) != word[2]:
                raise IOError("ERROR: CRC unmatch.")
            decoded += word[0:2]
        return decoded

    def get_value(self):
        self.i2cbus.write(
            self.dev_addr,
            [ 0x26, 0x0F, 0x80, 0x00, 0xA2, 0x66, 0x66, 0x93 ]
        )
        time.sleep(0.030)
        data = self.i2cbus.read(self.DEV_ADDR, 3)
        raw = struct.unpack('>H', self.decode_data(data))[0]

        voc_index = self.voc_algo.vocalgorithm_process(raw)

        with open(self.DUMP_FILE, 'wb') as f:
            pickle.dump(self.voc_algo, f)

        return voc_index

    def get_value_map(self):
        value = self.get_value()

        return { 'voc_index': value }

    
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.sgp40
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    sgp40 = sensor.sgp40.SGP40(I2C_BUS)

    ping = sgp40.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(sgp40.get_value_map())
