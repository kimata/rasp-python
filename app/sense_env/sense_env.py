#!/usr/bin/env python3
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
import subprocess
import re

json.encoder.FLOAT_REPR = lambda f: ("%.2f" % f)

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

import sensor.hdc1050
import sensor.sht31
import sensor.sht21
import sensor.lps25h
import sensor.lps22hb
import sensor.tsl2561
import sensor.apds9250
import sensor.ccs811
import sensor.k30
import sensor.veml6075
import sensor.veml7700
import sensor.scd4x

I2C_ARM_BUS = 0x1       # Raspberry Pi のデフォルトの I2C バス番号
I2C_VC_BUS  = 0x0       # dtparam=i2c_vc=on で有効化される I2C のバス番号
RETRY       = 3         # デバイスをスキャンするときのリトライ回数
CO2_MAX     = 5000      # CO2 濃度の最大値 (時々異常値を返すのでその対策)

def detect_sensor():
    candidate_list = [
        sensor.k30.K30(I2C_ARM_BUS),
        sensor.k30.K30(I2C_VC_BUS),
        sensor.hdc1050.HDC1050(I2C_ARM_BUS),
        sensor.sht31.SHT31(I2C_ARM_BUS),
        sensor.sht21.SHT21(I2C_ARM_BUS),
        sensor.lps25h.LPS25H(I2C_ARM_BUS),
        sensor.lps22hb.LPS22HB(I2C_ARM_BUS),
        sensor.tsl2561.TSL2561(I2C_ARM_BUS),
        sensor.apds9250.APDS9250(I2C_ARM_BUS),
        sensor.ccs811.CCS811(I2C_ARM_BUS),
        sensor.scd4x.SCD4x(I2C_ARM_BUS),
        sensor.veml7700.VEML7700(I2C_ARM_BUS),
        sensor.veml6075.VEML6075(I2C_VC_BUS),
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
                if sensor.NAME == 'K30' and val['co2'] > CO2_MAX:
                    continue
                if sensor.NAME == 'HDC1050' and val['humi'] == 100:
                    continue
                if (sensor.NAME == 'LPS22HB' or sensor.NAME == 'LPS25H') and \
                   (val['press'] < 900 or val['press'] > 1100):
                    continue
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
