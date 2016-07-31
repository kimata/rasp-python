# coding: utf-8
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
        self.wh = io.open('/dev/i2c-' + str(bus), 'wb', buffering=0)
        self.rh = io.open('/dev/i2c-' + str(bus), 'rb', buffering=0)

    def write(self, dev_addr, reg_addr, param=None):
        fcntl.ioctl(self.wh, self.I2C_SLAVE, dev_addr)
        data=bytearray()
        data.append(reg_addr)
        if type(param) is list:
            data.extend(param)
        elif not param is None:
            data.append(param)
        self.wh.write(data)

    def read(self, dev_addr, reg_addr, count=None):
        fcntl.ioctl(self.wh, self.I2C_SLAVE, dev_addr)
        fcntl.ioctl(self.rh, self.I2C_SLAVE, dev_addr)

        if count is None:
            count = reg_addr
        else:
            self.wh.write(bytearray([reg_addr]))
            
        data = []
        data_str = self.rh.read(count)
        for c in data_str:
            data.append(ord(c))
            
        return data


