#!/usr/bin/env python
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
    def __call__(self, source, dest):
        os.rename(source, dest)
        f_in = open(dest, 'rb')
        f_out = gzip.open("%s.gz" % dest, 'wb')
        f_out.writelines(f_in)
        f_out.close()
        f_in.close()
        os.remove(dest)

import b_route_config

logger = logging.getLogger()
log_handler = logging.handlers.RotatingFileHandler(
    '/tmp/sense_power.log',
    encoding='utf8', maxBytes=10*1024*1024, backupCount=10,
)
log_handler.formatter = logging.Formatter(
    fmt='%(asctime)s %(levelname)s %(name)s :%(message)s',
    datefmt='%Y/%m/%d %H:%M:%S %Z'
)
log_handler.formatter.converter = time.gmtime
log_handler.rotator = GZipRotator()

logger.addHandler(log_handler)
logger.setLevel(level=logging.INFO)


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

rssi = subprocess.check_output("sudo iwconfig 2>/dev/null | grep 'Signal level' | sed 's/.*Signal level=\\(.*\\) dBm.*/\\1/'", shell=True)
rssi = rssi.rstrip().decode()

if re.compile('-\d+').search(rssi):
    value_map['wifi_rssi'] = int(rssi)

print(json.dumps(value_map))
logger.info('[SUCCESS] Power: {}'.format(power))

exit(0)
