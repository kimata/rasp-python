#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# 環境センシング用スクリプト．
# 以下のセンサを使用して，測定を行います．
# センサの存在は自動検出します．
#
# [センサ一覧]
# - HDC1050     : 温度，湿度
# - LPS25H      : 気圧
# - TSL2561     : 照度
# - K30         : CO2 濃度

import os
import sys
import time
import json

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

import sensor.hdc1050
import sensor.lps25h
import sensor.tsl2561
import sensor.k30

I2C_BUS = 0x1 	# I2C のバス番号 (Raspberry Pi は 0x1)
RETRY   = 3   	# デバイスをスキャンするときのリトライ回数
CO2_MAX = 5000 # CO2 濃度の最大値 (時々異常値を返すのでその対策)

def detect_sensor():
    candidate_list = [
        sensor.hdc1050.HDC1050(I2C_BUS),
        sensor.lps25h.LPS25H(I2C_BUS),
        sensor.tsl2561.TSL2561(I2C_BUS),
        sensor.k30.K30(I2C_BUS),
    ]
    sensor_list = []
    for dev in candidate_list:
        for i in xrange(RETRY):
            if dev.ping():
                sensor_list.append(dev)
                break
            time.sleep(0.1)

    return sensor_list

def scan_sensor(sensor_list):
    value_map = {}
    for sensor in sensor_list:
        for i in xrange(RETRY):
            try:
                val = sensor.get_value_map()
                if sensor.NAME == 'K30' and val['co2'] > CO2_MAX:
                    continue
                if sensor.NAME == 'HDC1050' and val['humi'] == 100:
                    continue
                
                value_map.update(val)
                break
            except:
                pass
            time.sleep(0.1)

    return value_map

sensor_list = detect_sensor()
value_map = scan_sensor(sensor_list)

print(json.dumps(value_map))