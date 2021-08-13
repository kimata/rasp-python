#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# スマートメータモニタ用スクリプト．
# 現在の使用電力の測定を行います．

import os
import sys
import time
import json
import traceback
import logging
import logging.handlers
import gzip
import subprocess
import re

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

from dev.bp35a1 import BP35A1
from meter.echonetenergy import EchonetEnergy
from meter.echonetenergy import get_pan_info

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
        '/dev/shm/sense_power.log',
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


import b_route_config

logger = get_logger()

echonet_if = BP35A1('/dev/ttyS0', False)

power = 0
energy_meter = None

try:
    energy_meter = EchonetEnergy(
        echonet_if,
        b_route_config.b_id,
        b_route_config.b_pass
    )

    pan_info = get_pan_info(energy_meter)
    energy_meter.connect(pan_info)
    power = energy_meter.get_current_energy()
    energy_meter.disconnect()
except:
    if not energy_meter is None:
        energy_meter.disconnect()
    time.sleep(1)
    echonet_if.reset()
    time.sleep(1)
    echonet_if.reset()

    logger.error(traceback.format_exc())
    sys.stderr.write(traceback.format_exc())
    exit(-1)

# 値があまりに大きい場合は，エラー扱いにする
if power > 10000:
    logger.error('Value is too big: %d' % (power))
    exit(-1)

value_map = { 'power': power }

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
logger.info('[SUCCESS] Power: {}'.format(power))

exit(0)
