#!/usr/bin/env python
# -*- coding: utf-8 -*-

import serial
import pprint
   
class BP35A1:
    def __init__(self, port, debug=False):
        self.ser = serial.Serial(
            port=port,
            baudrate=115200,
            timeout=1
        )
        self.opt = None
        self.debug = debug
        self.__send_command('SKRESET')
       
    def get_option(self):
        ret = self.__send_command('ROPT')
        val = int(ret, 16)

        self.opt = val

    def set_id(self, b_id):
        command = 'SKSETRBID {0}'.format(b_id)
        self.__send_command(command)
        
    def set_password(self, b_pass):
        command = 'SKSETPWD {0:X} {1}'.format(len(b_pass), b_pass)
        self.__send_command(command)

    def scan_channel(self, start_duration=3):
        duration = start_duration
        pan_info = None
        while True:
            command = 'SKSCAN 2 {0:X} {1}'.format((1 << 32) - 1, duration)
            self.__send_command(command)
            
            while True:
                line = self.ser.readline()
                # スキャン完了
                if line.startswith('EVENT 22'):
                    break
                # メータ発見
                if line.startswith('EVENT 20'):
                    pan_info = self.__parse_pan_desc()

            if pan_info != None:
                return pan_info

            duration += 1
            if duration > 7:
                return None

    def connect(self, pan_desc):
        command = 'SKSREG S2 {0}'.format(pan_desc['Channel'])
        self.__send_command(command)
        
        command = 'SKSREG S3 {0}'.format(pan_desc['Pan ID'])
        self.__send_command(command)

        command = 'SKLL64 {0}'.format(pan_desc['Addr'])
        ipv6_addr = self.__send_command_raw(command)

        command = 'SKJOIN {0}'.format(ipv6_addr)

        self.__send_command(command)

        while True:
            line = self.ser.readline()
            # 接続失敗
            if line.startswith('EVENT 24'):
                return None
            # 接続成功
            if line.startswith('EVENT 25'):
                return ipv6_addr

    def recv_udp(self, ipv6_addr, wait_count=10):
        for i in xrange(wait_count):
            line = self.ser.readline().rstrip()
            if line == '':
                continue

            line = line.split(' ', 9)
            if line[0] != 'ERXUDP':
                continue
            if line[1] == ipv6_addr:
                return line[8]
        return None

    def send_udp(self, ipv6_addr, port, data, handle=1, security=True):
        command = 'SKSENDTO {0} {1} {2:04X} {3} {4:04X} {5}'.format(
            handle,
            ipv6_addr,
            port,
            1 if security else 2,
            len(data),
            data
        )
        self.__send_command_raw(
            command,
            lambda command: ' '.join(command.split(' ', 7)[0:6])
        )
        status = 0
        while self.ser.readline().rstrip() != 'OK':
            None
        
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

    def __send_command_raw(self, command, echo_back=lambda command: command):
        self.ser.write(command + "\r")
        # NOTE: echo_back はコマンドからエコーバック文字列を生成する関数．
        # デフォルトはコマンドそのもの．
        self.__expect(echo_back(command))

        return self.ser.readline().rstrip()
    
    def __send_command(self, command):
        if self.debug:
            pprint.pprint('SEND: ' + command)
        ret = self.__send_command_raw(command)
        ret = ret.split(' ', 1)

        if ret[0] != 'OK':
            raise Exception("Status is not OK.\nrst: %s" %
                            ret[0])

        return None if len(ret) == 1 else ret[1]

    def __expect(self, text):
        line = self.ser.readline()
        if line.rstrip() != text:
            raise Exception("Echo back is wrong.\nexp: %s\nrst: %s" %
                            (text, line.rstrip()))
