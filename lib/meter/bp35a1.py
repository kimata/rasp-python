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
    def parse_frame(cls, packet, is_binary=True):
        frame = {}

        # ヘッダ
        frame['EHD1'] = struct.unpack('B', packet[0])[0]
        frame['EHD2'] = struct.unpack('B', packet[1])[0]
        frame['TID'] = struct.unpack('>H', packet[2:4])[0]
        if (frame['EHD2'] == 0x81):
            frame['EDATA'] = cls.parse_data(packet[4:])

        cls.validate_header(frame)

        return frame
        
    @classmethod
    def validate_header(cls, frame):
        if frame['EHD1'] != 0x10:
            raise Exception('Invalid EHD1: %d' %frame['EHD1'])
        if (frame['EHD2'] != 0x81) and (frame['EHD2'] != 0x82):
            raise Exception('Invalid EHD2: %d' %frame['EHD2'])

    @classmethod
    def parse_data(cls, packet):
        data = {}
        data['SEOJ'] = struct.unpack('>I', chr(0) + packet[0:3])[0]
        data['DEOJ'] = struct.unpack('>I', chr(0) + packet[3:6])[0]
        data['ESV'] = struct.unpack('B', packet[6])[0]
        data['OPC'] = struct.unpack('B', packet[7])[0]

        prop_list = []
        packet = packet[8:]
        for i in xrange(data['OPC']):
            prop = {}
            prop['EPC'] = struct.unpack('B', packet[0])[0]
            prop['PDC'] = struct.unpack('B', packet[1])[0]
            prop['EDT'] = packet[2:(2+prop['PDC'])]
            prop_list.append(prop)
        data['prop_list'] = prop_list

        return data

    @classmethod
    def parse_inst_list(cls, packet):
        count = struct.unpack('B', packet[0])[0]
        packet = packet[1:]

        inst_list = []
        for i in xrange(count):
            inst_info = {}
            inst_info['class_group_code'] = struct.unpack('B', packet[0])[0]
            inst_info['class_code'] = struct.unpack('B', packet[1])[0]
            inst_info['instance_code'] = struct.unpack('B', packet[2])[0]
            inst_list.append(inst_info)
            packet = packet[3:]

        return inst_list

    @classmethod
    def check_class(cls, inst_list, class_group_code, class_code):
        for inst_info in inst_list:
            if (inst_info['class_group_code'] == class_group_code) and \
               (inst_info['class_code'] == class_code):
                return True

        return False
    
class BP35A1:
    def __init__(self, ser):
        self.ser = ser
        self.opt = None
        # ret = self.__send_command('SKRESET')
       
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

        self.__send_command(command)

        while True:
            line = self.ser.readline()
            # 接続失敗
            if line.startswith('EVENT 24'):
                return None
            # 接続成功
            if line.startswith('EVENT 25'):
                pprint.pprint('OK')
                return ipv6_addr

    def recv_udp(self, ipv6_addr):
        while True:
            line = self.ser.readline().rstrip()
            if line == '':
                continue

            line = line.split(' ', 9)
            if line[0] != 'ERXUDP':
                continue
            if line[1] == ipv6_addr:
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

    packet = bp35a1.recv_udp(ipv6_addr)

    frame = meter.bp35a1.ECHONETLite.parse_frame(packet)

    # インスタンスリスト
    inst_list = meter.bp35a1.ECHONETLite.parse_inst_list(
        frame['EDATA']['prop_list'][0]['EDT'])

    # 低圧スマート電力量メータクラスがあるか確認
    is_meter_exit = meter.bp35a1.ECHONETLite.check_class(
        inst_list, 0x02, 0x88)

    if not is_meter_exit:
        raise Exception('Meter not fount')

            
    pprint.pprint(frame)
    pprint.pprint(inst_list)


    # ser.write("SKVER\r\n")
    # print(ser.readline()) # エコーバック
    # print(ser.readline()) # バージョン


