#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# 環境センシング用スクリプト．
# 以下のセンサを使用して，測定を行います．
# センサの存在は自動検出します．
#
# [センサ一覧]
# - EZO-RDT     : 水温

import os
import sys
import time
import json
import subprocess
import re

json.encoder.FLOAT_REPR = lambda f: ("%.2f" % f)

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

import sensor.ezo_rtd

I2C_ARM_BUS = 0x1       # Raspberry Pi のデフォルトの I2C バス番号
I2C_VC_BUS  = 0x0       # dtparam=i2c_vc=on で有効化される I2C のバス番号
RETRY       = 3         # デバイスをスキャンするときのリトライ回数

def detect_sensor():
    candidate_list = [
        sensor.ezo_rtd.EZO_RTD(I2C_ARM_BUS),
    ]
    sensor_list = []
    for dev in candidate_list:
        for i in range(RETRY):
            if dev.ping():
                sensor_list.append(dev)
                break
            time.sleep(0.1)

    return sensor_list

def scan_sensor(sensor_list):
    value_map = {}
    for sensor in sensor_list:
        for i in range(RETRY):
            try:
                val = sensor.get_value_map()
                value_map.update(val)
                break
            except:
                pass
            time.sleep(0.1)

    return value_map

sensor_list = detect_sensor()
value_map = scan_sensor(sensor_list)

wifi_rssi = subprocess.check_output("sudo iwconfig 2>/dev/null | grep 'Signal level' | sed 's/.*Signal level=\\(.*\\) dBm.*/\\1/'", shell=True)
wifi_rssi = wifi_rssi.rstrip().decode()

wifi_ch = subprocess.check_output("sudo iwlist wlan0 channel | grep Current | sed -r 's/^.*Channel ([0-9]+)\)/\\1/'", shell=True)
try:
    wifi_ch = int(wifi_ch.rstrip().decode())
except:
    # 5GHz
    wifi_ch = 0

if re.compile('-\d+').search(wifi_rssi):
    value_map['wifi_rssi'] = int(wifi_rssi)
    value_map['wifi_ch'] = wifi_ch

print(json.dumps(value_map))
