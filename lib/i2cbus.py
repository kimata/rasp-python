#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Linux で I2C を読み書きするライブラリ．
# Python の標準ライブラリの smbus だと，read 時もレジスタを
# write する必要があり，HDC1050 等のデバイスにアクセスできない
# ので自作．

import io
import fcntl

class I2CBus:
    # ioctl 用 (Linux の i2c-dev.h の定義から引用)
    I2C_SLAVE =      0x0703
    
    def __init__(self, bus):
        self.wh = io.open('/dev/i2c-' + str(bus), mode='wb', buffering=0)
        self.rh = io.open('/dev/i2c-' + str(bus), mode='rb', buffering=0)

    def write(self, dev_addr, reg_addr, param=None):
        fcntl.ioctl(self.wh, self.I2C_SLAVE, dev_addr)
        data=bytearray()
        data.append(reg_addr)
        if type(param) is list:
            data.extend(param)
        elif not param is None:
            data.append(param)
        self.wh.write(data)

    def read(self, dev_addr, count, reg_addr=None):
        fcntl.ioctl(self.wh, self.I2C_SLAVE, dev_addr)
        fcntl.ioctl(self.rh, self.I2C_SLAVE, dev_addr)

        # reg_addr が指定されてた場合の処理
        if not reg_addr is None:
            self.wh.write(bytearray([reg_addr]))
            
        return self.rh.read(count)

