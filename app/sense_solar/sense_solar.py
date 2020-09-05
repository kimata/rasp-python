#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# 太陽電池の発電量センシング用スクリプト．
# 以下のセンサを使用して，測定を行います．
# センサの存在は自動検出します．
#
# [センサ一覧]
# - SHT-35      : 温度，湿度
# - INA226      : 電圧，電流，電力

import os
import sys
import re
import time
import json
import subprocess
import logging
import logging.handlers
import gzip
import traceback

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

json.encoder.FLOAT_REPR = lambda f: ("%.2f" % f)

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

import sensor.sht35
import sensor.ina226
import sensor.sps30
import sensor.ads1015


I2C_ARM_BUS = 0x1       # Raspberry Pi のデフォルトの I2C バス番号
I2C_VC_BUS  = 0x0       # dtparam=i2c_vc=on で有効化される I2C のバス番号
RETRY   = 3           # デバイスをスキャンするときのリトライ回数

SHT35_DEV_ADDR          = 0x44 # SHT-35 の I2C デバイスアドレス
INA226_PANEL_DEV_ADDR   = 0x40 # 発電電力計測用 INA226 の I2C デバイスアドレス
INA226_CHARGE_DEV_ADDR  = 0x41 # 充電電力計測用 INA226 の I2C デバイスアドレス
INA226_BATTERY_DEV_ADDR = 0x42 # 出力電力計測用 INA226 の I2C デバイスアドレス

class GZipRotator:
    def namer(name):
        return name + '.gz'

    def rotator(source, dest):
        with open(source, 'rb') as fs:
            with gzip.open(dest, 'wb') as fd:
                fd.writelines(fs)
        os.remove(source)

def get_logger():
    logger = logging.getLogger()
    log_handler = logging.handlers.RotatingFileHandler(
        '/dev/shm/sense_solar.log',
        encoding='utf8', maxBytes=1*1024*1024, backupCount=10,
    )
    log_handler.formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s %(name)s :%(message)s',
        datefmt='%Y/%m/%d %H:%M:%S %Z'
    )
    log_handler.namer = GZipRotator.namer
    log_handler.rotator = GZipRotator.rotator

    logger.addHandler(log_handler)
    logger.setLevel(level=logging.INFO)

    return logger

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

def i2c_bus_reset():
    logger.warning('Reset I2C bus')

    # NOTE: 状況を記録しておく
    logger.warning('sudo gpio readall')
    logger.warning(subprocess.check_output('sudo gpio readall', shell=True).decode())
    logger.warning('sudo i2cdetect -y 1')
    logger.warning(subprocess.check_output('sudo i2cdetect -y 1', shell=True).decode())

    GPIO.setwarnings(False)
    GPIO.setup(2, GPIO.IN)
    GPIO.setup(3, GPIO.OUT)
    if GPIO.input(2) == GPIO.LOW:
        logger.warning('increment SCL')
        for i in range(20):
            GPIO.output(3, GPIO.LOW)
            time.sleep(0.001)
            GPIO.output(3, GPIO.HIGH)
            time.sleep(0.001)

            if (GPIO.input(2) == GPIO.HIGH):
                break
    subprocess.run('sudo gpio -g mode 2 alt0', shell=True)
    subprocess.run('sudo gpio -g mode 3 alt0', shell=True)

logger = get_logger()

value_map = scan_sensor(
    [
        sensor.sht35.SHT35(I2C_VC_BUS, SHT35_DEV_ADDR),
        sensor.ina226.INA226(I2C_ARM_BUS, INA226_PANEL_DEV_ADDR, 'panel_'),
        sensor.ina226.INA226(I2C_ARM_BUS, INA226_CHARGE_DEV_ADDR, 'charge_'),
        sensor.ina226.INA226(I2C_ARM_BUS, INA226_BATTERY_DEV_ADDR, 'battery_'),
        sensor.sps30.SPS30(I2C_VC_BUS),
        sensor.ads1015.ADS1015(I2C_VC_BUS),
    ]
)

logger.info(json.dumps(value_map))

try:
    mvolt = value_map['mvolt']
    del value_map['mvolt']

    value_map['solar_rad'] = round(mvolt / 6.98 * 1000, 2)
    if value_map['solar_rad'] < 0:
        value_map['solar_rad'] = 0.0

    if value_map['solar_rad'] < 1:
        value_map['power_efficiency'] = 0.0
    else:
        power_efficiency = 100.0 * value_map['panel_power'] / (value_map['solar_rad'] * (0.455-0.05)*(0.510-0.05)*2)
        value_map['power_efficiency'] = round(power_efficiency, 2)

    charge_efficiency = 0.0
    if (value_map['panel_power'] > 0):
        charge_efficiency = 100.0 * value_map['charge_power'] / value_map['panel_power']
        if charge_efficiency > 100:
            charge_efficiency = 100.0

    value_map['solar_rad'] = round(solar_rad, 2)
    value_map['power_efficiency'] = round(power_efficiency, 2)
    value_map['charge_efficiency'] = round(charge_efficiency, 2)
except Exception as e:
    logger.warning(traceback.format_exc())
    i2c_bus_reset()

rssi = subprocess.check_output("sudo iwconfig 2>/dev/null | grep 'Signal level' | sed 's/.*Signal level=\\(.*\\) dBm.*/\\1/'", shell=True)
rssi = rssi.rstrip().decode()

if re.compile('-\d+').search(rssi):
    value_map['wifi_rssi'] = int(rssi)

print(json.dumps(value_map))
