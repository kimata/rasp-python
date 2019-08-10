#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import pprint

class ECHONETLite:
    UDP_PORT							= 3610
    
    EHD1 							= 0x10
    class EHD2:
        FORMAT1 						= 0x81
        FORMAT2 						= 0x82

    class ESV:
        # プロパティ値書き込み要求(応答不要)
        PROP_WRITE_NO_RES					= 0x60
        # プロパティ値書き込み要求(応答要)
        PROP_WRITE						= 0x61
        # プロパティ値読み出し要求
        PROP_READ						= 0x62
        # プロパティ値通知要求
        PROP_NOTIFY						= 0x62
        # プロパティ値書き込み・読み出し要求
        PROP_WRITE_READ						= 0x6E

    class EOJ:
        # 住宅・設備関連機器クラスグループ
        CLASS_GROUP_HOUSING 					= 0x02
        # 管理・操作関連機器クラスグループ
        CLASS_GROUP_MANAGEMENT 					= 0x05

        class HOUSE_CLASS_GROUP:
            # 低圧スマート電力量メータクラス
            LOW_VOLTAGE_SMART_METER				= 0x88
        class MANAGEMENT_CLASS_GROUP:
            # コントローラ
            CONTROLLER						= 0xFF

    class EPC:
        class LOW_VOLTAGE_SMART_METER:
            # 動作状態
            STATUS						= 0x80
            # 積算電力量有効桁数
            EFFECTIVE_DIGITS_OF_CUMULATIVE_ENERGY		= 0xD7
            # 積算電力量計測値(正方向計測値)
            CUMULATIVE_ENERGY_NORMAL_DIRECTION			= 0xE0
            # 積算電力量計測値(逆方向計測値)
            CUMULATIVE_ENERGY_REVERSE_DIRECTION			= 0xE3
            # 積算電力量単位(正方向、逆方向計測値)
            CUMULATIVE_ENERGY_UNIT				= 0xE1
            # 瞬時電力計測値
            INSTANTANEOUS_ENERGY				= 0xE7
            # 瞬時電流計測値
            INSTANTANEOUS_CURRENT				= 0xE8
            # 定時積算電力量計測値(正方向計測値)
            CUMULATIVE_ENERGY_FIXED_TIME_NORMAL_DIRECTION 	= 0xEA
            # 定時積算電力量計測値(逆方向計測値)
            CUMULATIVE_ENERGY_FIXED_TIME_REVERSE_DIRECTION	= 0xEB

    @classmethod
    def parse_frame(cls, packet):
        frame = {}

        if (packet is None) or (len(packet) < 10):
            raise Exception('Invalid Packet: too short')

        # ヘッダ
        frame['EHD1'] = struct.unpack('B', packet[0:1])[0]
        frame['EHD2'] = struct.unpack('B', packet[1:2])[0]
        frame['TID'] = struct.unpack('>H', packet[2:4])[0]
        if (frame['EHD2'] == cls.EHD2.FORMAT1):
            frame['EDATA'] = cls.parse_data(packet[4:])

        cls.validate_header(frame)

        return frame
        
    @classmethod
    def validate_header(cls, frame):
        if frame['EHD1'] != cls.EHD1:
            raise Exception('Invalid EHD1: %d' % frame['EHD1'])
        if (frame['EHD2'] != cls.EHD2.FORMAT1) and \
           (frame['EHD2'] != cls.EHD2.FORMAT2):
            raise Exception('Invalid EHD2: %d' % frame['EHD2'])

    @classmethod
    def parse_data(cls, packet):
        data = {}
        data['SEOJ'] = struct.unpack('>I', b'\00' + packet[0:3])[0]
        data['DEOJ'] = struct.unpack('>I', b'\00' + packet[3:6])[0]
        data['ESV'] = struct.unpack('B', packet[6:7])[0]
        data['OPC'] = struct.unpack('B', packet[7:8])[0]

        prop_list = []
        packet = packet[8:]
        for i in range(data['OPC']):
            prop = {}
            prop['EPC'] = struct.unpack('B', packet[0:1])[0]
            prop['PDC'] = struct.unpack('B', packet[1:2])[0]
            if prop['PDC'] == 0:
                prop['EDT'] = None
            else:
                prop['EDT'] = packet[2:(2+prop['PDC'])]
            prop_list.append(prop)
        data['prop_list'] = prop_list

        return data

    @classmethod
    def parse_inst_list(cls, packet):
        count = struct.unpack('B', packet[0:1])[0]
        packet = packet[1:]

        inst_list = []
        for i in range(count):
            inst_info = {}
            inst_info['class_group_code'] = struct.unpack('B', packet[0:1])[0]
            inst_info['class_code'] = struct.unpack('B', packet[1:2])[0]
            inst_info['instance_code'] = struct.unpack('B', packet[2:3])[0]
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

    @classmethod
    def build_frame(cls, edata, tid=1):
        return struct.pack('2B', cls.EHD1, cls.EHD2.FORMAT1) + \
            struct.pack('>H', tid) + edata

    @classmethod
    def build_edata(cls, seoj, deoj, esv, prop_list):
        seoj_data = struct.pack('>I', seoj)[1:]
        deoj_data = struct.pack('>I', deoj)[1:]
        
        esv_data = struct.pack('B', esv)
        opc_data = struct.pack('B', len(prop_list))
        
        edata = seoj_data + deoj_data + esv_data + opc_data
        for prop in prop_list:
            prop_data = cls.build_prop(prop['EPC'], prop['PDC'],
                                       prop.get('EDT'))
            edata += prop_data
            
        return edata
    
    @classmethod
    def build_eoj(cls, class_group_code, class_code, instance_code=0x1):
        return (class_group_code << 16) | (class_code << 8) | instance_code
    
    @classmethod
    def build_prop(cls, epc, pdc, edt):
        prop = struct.pack('2B', epc, pdc)
        if pdc != 0:
            prop += edt

        return prop
