#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import pprint
import time
    
if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

class ECHONETLite:
    @classmethod
    def parse_frame(cls, frame, is_binary=True):
        pprint.pprint(struct.unpack('B', bytes(frame)))

class BP35A1:
    def __init__(self, ser):
        self.ser = ser
        self.opt = None
        ret = self.__send_command('SKRESET')
       
    def get_option(self):
        ret = self.__send_command('ROPT')
        val = int(ret, 16)

        self.opt = val

    def set_id(self, b_id):
        command = 'SKSETRBID ' + b_id
        self.__send_command(command)
        
    def set_password(self, b_pass):
        command = 'SKSETPWD ' +  format(len(b_pass), 'x') + ' ' + b_pass
        self.__send_command(command)

    def scan_channel(self, start_duration=3):
        duration = start_duration
        pan_desc = None
        while True:
            command = 'SKSCAN 2 ' + format((1 << 32) - 1, 'x') + ' ' + str(duration)
            pprint.pprint(command)
            self.__send_command(command)
            
            while True:
                line = self.ser.readline()
                # スキャン完了
                if line.startswith('EVENT 22'):
                    break
                # メータ発見
                if line.startswith('EVENT 20'):
                    pan_desc = self.__parse_pan_desc()

            if pan_desc != None:
                return pan_desc

            duration += 1
            if duration > 7:
                return None

    def connect(self, pan_desc):
        command = 'SKSREG S2 ' + pan_desc['Channel']
        self.__send_command(command)
        
        command = 'SKSREG S3 ' + pan_desc['Pan ID']
        self.__send_command(command)

        command = 'SKLL64 ' + pan_desc['Addr']
        ipv6_addr = self.__send_command_raw(command)

        command = 'SKJOIN ' + ipv6_addr
        pprint.pprint(command)
        self.__send_command(command)

        while True:
            line = self.ser.readline()
            # 接続失敗
            if line.startswith('EVENT 24'):
                return None
            # 接続成功
            if line.startswith('EVENT 25'):
                pprint.pprint("NG")
                return ipv6_addr

    def receive_udp(self, ipv6_addr):
        line = self.ser.readline().rstrip().split(' ', 9)
        
        if line[0] != 'ERXUDP':
            return None
        if line[1] != ipv6_addr:
            return None

        return line[8]
            
    def __parse_pan_desc(self):
        self.__expect('EPANDESC')
        pan_desc = {}
        for i in xrange(6):
            line = self.ser.readline()

            if not line.startswith('  '):
                raise Exception("Line does not start with space.\nrst: %s" %
                                line)
            line = line.strip().split(':')
            pan_desc[line[0]] = line[1]

        return pan_desc

    def __send_command_raw(self, command):
        self.ser.write(command + "\r")
        
        if not self.__expect(command):
            raise Exception("Echo back is wrong.\nexp: %s\nrst: %s" %
                            (command, line.rstrip()))

        return self.ser.readline().rstrip()
    
    def __send_command(self, command):
        ret = self.__send_command_raw(command)
        ret = ret.split(' ', 1)

        if ret[0] != 'OK':
            raise Exception("Status is not OK.\nrst: %s" %
                            ret[0])

        return None if len(ret) == 1 else ret[1]

    def __expect(self, text):
        line = self.ser.readline()
        return line.rstrip() == text
    

if __name__ == '__main__':
    # TEST Code
    import serial
    import pprint
    
    import pickle
    import os.path

    import meter.bp35a1
    
    import b_route_config

    PAN_DESC_DAT = 'pan_desc.dat'

    # PAN ID の探索は時間がかかるので，キャッシュしておく
    def get_pan_desc(bp35a1):
        if (os.path.exists(PAN_DESC_DAT)):
            with open(PAN_DESC_DAT, mode='rb') as f:
                return pickle.load(f)
        else:
            pan_desc = bp35a1.scan_channel()

            with open(PAN_DESC_DAT, mode='wb') as f:
                pickle.dump(pan_desc, f)

            return pan_desc
    
    ser = serial.Serial(
        port='/dev/ttyAMA0',
        baudrate=115200,
        timeout=1)
    bp35a1 = meter.bp35a1.BP35A1(ser)
    bp35a1.set_id(b_route_config.b_id)
    bp35a1.set_password(b_route_config.b_pass)

    pan_desc = get_pan_desc(bp35a1)

    pprint.pprint(pan_desc)

    ipv6_addr = bp35a1.connect(pan_desc)
    if ipv6_addr == None:
        raise Exception('Faile to connect Wi-SUN')

    val = bp35a1.receive_udp(pan_desc)

    pprint.pprint(val)

    # ser.write("SKVER\r\n")
    # print(ser.readline()) # エコーバック
    # print(ser.readline()) # バージョン


