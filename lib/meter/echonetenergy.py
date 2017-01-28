#!/usr/bin/env python
# -*- coding: utf-8 -*-

import struct
import pickle
import os.path

if __name__ == '__main__':
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from proto.echonetlite import ECHONETLite
   
class EchonetEnergy:
    def __init__(self, echonet_if, b_id, b_pass, debug=False):
        echonet_if.set_id(b_id)
        echonet_if.set_password(b_pass)
        
        self.echonet_if = echonet_if
        self.ipv6_addr = None
        
    def get_pan_info(self):
        return self.echonet_if.scan_channel()        

    def connect(self, pan_info):
        self.ipv6_addr = self.echonet_if.connect(pan_info)
        if self.ipv6_addr == None:
            raise Exception('Faile to connect Wi-SUN')

        recv_packet = self.echonet_if.recv_udp(self.ipv6_addr)

        frame = ECHONETLite.parse_frame(recv_packet)

        # インスタンスリスト
        inst_list = ECHONETLite.parse_inst_list(
            frame['EDATA']['prop_list'][0]['EDT'])

        # 低圧スマート電力量メータクラスがあるか確認
        is_meter_exit = ECHONETLite.check_class(
            inst_list, 0x02, 0x88)
    
        if not is_meter_exit:
            raise Exception('Meter not fount')
        
    def get_current_energy(self):
        meter_eoj = ECHONETLite.build_eoj(
            ECHONETLite.EOJ.CLASS_GROUP_HOUSING,
            ECHONETLite.EOJ.HOUSE_CLASS_GROUP.LOW_VOLTAGE_SMART_METER
        )

        edata  = ECHONETLite.build_edata(
            ECHONETLite.build_eoj(
                ECHONETLite.EOJ.CLASS_GROUP_MANAGEMENT,
                ECHONETLite.EOJ.MANAGEMENT_CLASS_GROUP.CONTROLLER
            ),
            meter_eoj,
            ECHONETLite.ESV.PROP_READ,
            [
                {
                    'EPC': ECHONETLite.EPC.LOW_VOLTAGE_SMART_METER.INSTANTANEOUS_ENERGY,
                    'PDC': 0,
                }
            ]
        )
        send_packet = ECHONETLite.build_frame(edata)

        while True:
            self.echonet_if.send_udp(self.ipv6_addr, ECHONETLite.UDP_PORT, send_packet)
            recv_packet = self.echonet_if.recv_udp(self.ipv6_addr)
            frame = ECHONETLite.parse_frame(recv_packet)
            
            if frame['EDATA']['SEOJ'] != meter_eoj:
                continue
            for prop in frame['EDATA']['prop_list']:
                if prop['EPC'] != \
                   ECHONETLite.EPC.LOW_VOLTAGE_SMART_METER.INSTANTANEOUS_ENERGY:
                    continue
                return struct.unpack('>I', prop['EDT'])[0]

PAN_DESC_DAT = '/tmp/pan_desc.dat'

# PAN ID の探索 (キャッシュ付き)
def get_pan_info(energy_meter):
    if (os.path.exists(PAN_DESC_DAT)):
        with open(PAN_DESC_DAT, mode='rb') as f:
            try:
                return pickle.load(f)
            except:
                pass

    pan_info = energy_meter.get_pan_info()
    
    with open(PAN_DESC_DAT, mode='wb') as f:
        pickle.dump(pan_info, f)
            
    return pan_info

if __name__ == '__main__':
    # TEST Code
    import pprint

    from dev.bp35a1 import BP35A1
    from meter.echonetenergy import EchonetEnergy

    # b_route_config.py に以下の変数を定義しておく．
    # - b_id	: B ルート ID
    # - b_pass	: B ルートパスワード
    import b_route_config

    # True だとデバッグ出力有り
    echonet_if = BP35A1('/dev/ttyS0', True)
    energy_meter = EchonetEnergy(
        echonet_if,
        b_route_config.b_id,
        b_route_config.b_pass
    )
    pan_info = get_pan_info(energy_meter)
    energy_meter.connect(pan_info)

    while True:
        print(energy_meter.get_current_energy())
