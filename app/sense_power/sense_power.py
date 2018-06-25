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

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

from dev.bp35a1 import BP35A1
from meter.echonetenergy import EchonetEnergy
from meter.echonetenergy import get_pan_info

import b_route_config

logger = logging.getLogger("sense_power")
log_handler = logging.handlers.TimedRotatingFileHandler(
    '/tmp/sense_power.log', when='D', interval=1, backupCount=3
)
log_handler.formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s :%(message)s')
log_handler.level = logging.DEBUG

logger.addHandler(log_handler)

echonet_if = BP35A1('/dev/ttyS0', False)

power = 0
try:
    energy_meter = EchonetEnergy(
        echonet_if,
        b_route_config.b_id,
        b_route_config.b_pass,
        log_handler
    )

    pan_info = get_pan_info(energy_meter)
    energy_meter.connect(pan_info)
    power = energy_meter.get_current_energy()
except:
    echonet_if.reset()
    echonet_if.reset()
    logger.error(traceback.format_exc())
    sys.stderr.write(traceback.format_exc())
    exit(-1)

# 値があまりに大きい場合は，エラー扱いにする
if power > 10000:
    exit(-1)
    
print(json.dumps({ 'power': power }))
