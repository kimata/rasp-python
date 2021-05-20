#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# KEYENCE のクランプオン式流量センサ FD-Q10C と IO-LINK で通信を行なって
# 流量を取得するライブラリです．

import sys
import os
import time
import struct

if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import dev.ltc2874 as driver

class FD_Q10C:
    NAME                = 'FD-Q10C'

    def __init__(self):
        self.spi = driver.com_open()

    def __del__(self):
        driver.com_close(self.spi)

    def ping(self):
        return True

    def get_value(self):
        try:
            ser = driver.com_start(self.spi)
            flow = driver.isdu_read(self.spi, ser, 0x94, driver.DATA_TYPE_UINT16) * 0.01
            driver.com_stop(self.spi, ser)

            # エーハイムの16/22用パイプの場合，内径14mm なので，内径12.7mの呼び径3/8の
            # 値に対して補正をかける．
            flow *= (14*14) / (12.7*12.7)

            return round(flow, 2)
        except RuntimeError as e:
            driver.com_stop(self.spi, ser, True)
            raise

    def get_value_map(self):
        value = self.get_value()

        return { 'flow': value }

if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.fd_q10c
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    fd_q10c = sensor.fd_q10c.FD_Q10C()

    ping = fd_q10c.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(fd_q10c.get_value_map())
