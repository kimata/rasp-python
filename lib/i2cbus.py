#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Linux で I2C を読み書きするライブラリ．
# Python の標準ライブラリの smbus だと，read 時もレジスタを
# write する必要があり，HDC1050 等のデバイスにアクセスできない
# ので自作．

import io
import fcntl
import ctypes
import posix
import struct

class I2CMsg(ctypes.Structure):
    _fields_ = [
        ('addr', ctypes.c_uint16),
        ('flags', ctypes.c_ushort),
        ('len', ctypes.c_short),
        ('buf', ctypes.POINTER(ctypes.c_char))
    ]
    
class I2CRdWrData(ctypes.Structure):
    _fields_ = [
        ('msgs', ctypes.POINTER(I2CMsg)),
        ('nmsgs', ctypes.c_int)]

class I2CBus:
    # ioctl 用 (Linux の i2c-dev.h の定義から引用)
    I2C_SLAVE		= 0x0703
    I2C_RDWR 		= 0x0707
    
    I2C_M_RD    	= 0x0001 
    I2C_M_IGNORE_NAK    = 0x1000
    
    def __init__(self, bus):
        self.fd = posix.open('/dev/i2c-%i' % bus, posix.O_RDWR)

    def __create_write_msg(self, dev_addr, write_dat):
        write_len = len(write_dat)
        write_buf = ctypes.create_string_buffer(write_dat, write_len)
        
        return I2CMsg(
            addr=dev_addr, flags=self.I2C_M_IGNORE_NAK,
            len=write_len, buf=write_buf
        )
        
    def read(self, dev_addr, count, reg_addr=None):
        read_buf = ctypes.create_string_buffer(count)
        read_msg = I2CMsg(
            addr=dev_addr, flags=self.I2C_M_RD|self.I2C_M_IGNORE_NAK,
            len=count, buf=read_buf
        )
        msgs = None
        if (reg_addr == None):
            msgs = (read_msg,)
        else:
            write_dat = bytes(bytearray([reg_addr]))
            write_msg = self.__create_write_msg(dev_addr, write_dat)
            msgs = (write_msg, read_msg)

        self.__send(*msgs)
            
        return b''.join(
            ctypes.string_at(msg.buf, msg.len)
            for msg in msgs if (msg.flags & self.I2C_M_RD)
        )

    def write(self, dev_addr, reg_addr, *param):
        write_dat = bytes(bytearray([reg_addr]) + bytearray(param))
        write_msg = self.__create_write_msg(dev_addr, write_dat)
        self.__send(write_msg)
        
    def __send(self, *msgs):
        nmsgs = len(msgs)
        rdwr_data = I2CRdWrData(
            msgs=(I2CMsg*nmsgs)(*msgs),
            nmsgs=nmsgs
        )
        fcntl.ioctl(self.fd, self.I2C_RDWR, rdwr_data)
        


        
                                            


    
    # def __init__(self, bus):
    #     # self.wh = io.open('/dev/i2c-' + str(bus), mode='wb', buffering=0)
    #     # self.rh = io.open('/dev/i2c-' + str(bus), mode='rb', buffering=0)
        

    # def write(self, dev_addr, reg_addr, param=None):
    #     fcntl.ioctl(self.wh, self.I2C_SLAVE, dev_addr)
    #     data=bytearray()
    #     data.append(reg_addr)
    #     if type(param) is list:
    #         data.extend(param)
    #     elif not param is None:
    #         data.append(param)
    #     self.wh.write(data)

    # def read(self, dev_addr, count, reg_addr=None):
    #     fcntl.ioctl(self.wh, self.I2C_SLAVE, dev_addr)
    #     fcntl.ioctl(self.rh, self.I2C_SLAVE, dev_addr)
        
    #     # reg_addr が指定されてた場合の処理
    #     if not reg_addr is None:
    #         self.wh.write(bytearray([reg_addr]))
            
    #     return self.rh.read(count)

