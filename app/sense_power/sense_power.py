#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# スマートメータモニタ用スクリプト．
# 現在の使用電力の測定を行います．

import os
import sys
import time
import json

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

from dev.bp35a1 import BP35A1
from meter.echonetenergy import EchonetEnergy
from meter.echonetenergy import get_pan_info

import b_route_config

echonet_if = BP35A1('/dev/ttyS0', False)
energy_meter = EchonetEnergy(
    echonet_if,
    b_route_config.b_id,
    b_route_config.b_pass
)
pan_info = get_pan_info(energy_meter)
energy_meter.connect(pan_info)

print(
    json.dumps({ "power": energy_meter.get_current_energy()})
)