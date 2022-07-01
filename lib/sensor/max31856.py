#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MAXIM の MAX31856 を使って，温度計測を行うラブラリです．

import spidev
import time
import struct


if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))


class MAX31856:
    NAME = "MAX31856"

    def __init__(self):
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1000000
        spi.mode = 1

        self.spi = spi
        self.init()

    def init(self, avg_sel="ave16", tc_type="T", noise_filter="60Hz"):
        self.avg_sel = avg_sel
        self.tc_type = tc_type
        self.noise_filter = noise_filter

    def reg_write(self, reg, val):
        self.spi.xfer2([reg | 0x80, val])

    def reg_read(self, reg, size=1):
        return self.spi.xfer2([reg] + ([0x00] * size))[1:]

    def ping(self):
        try:
            # NOTE: CR1 レジスタは初期値が 0x03 で，0x00 で使うこともないので，
            # デバイスの存在確認に使う．
            return self.reg_read(0x01)[0] != 0x00
        except:
            return False

    def get_value(self):
        avg_sel_map = {
            "ave1": 0b000,
            "ave2": 0b001,
            "ave4": 0b010,
            "ave8": 0b011,
            "ave16": 0b100,
        }
        tc_type_map = {
            "B": 0b0000,
            "E": 0b0001,
            "J": 0b0010,
            "K": 0b0011,
            "N": 0b0100,
            "R": 0b0101,
            "S": 0b0110,
            "T": 0b0111,
        }
        oneshot = 1
        noise_filter_map = {
            "60Hz": 0,
            "50Hz": 1,
        }

        self.reg_write(
            0x01,
            (avg_sel_map[self.avg_sel] << 4) | (tc_type_map[self.tc_type] << 0),
        )
        self.reg_write(
            0x00, (oneshot << 6) | (noise_filter_map[self.noise_filter] << 0)
        )

        time.sleep(0.8)

        return (
            struct.unpack(">i", bytes(self.reg_read(0x0C, 3) + [0x00]))[0] >> 8
        ) / 4096.0

    def get_value_map(self):
        value = self.get_value()

        return {"temp": value}


if __name__ == "__main__":
    # TEST Code
    import pprint
    import sensor.max31856

    max31856 = sensor.max31856.MAX31856()

    ping = max31856.ping()
    print("PING: %s" % ping)

    if ping:
        pprint.pprint(max31856.get_value_map())
