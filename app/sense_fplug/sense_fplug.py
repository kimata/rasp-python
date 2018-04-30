#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import json

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

from pyfplug import *

DEVICE_LIST = [
    { 'addr': 'B0:99:28:A4:42:6A', 'name': '炊飯器'             },
    { 'addr': 'B0:99:28:A4:65:43', 'name': '電気ポッド'         },
    { 'addr': 'B0:99:28:A4:6D:F3', 'name': '食洗機'             },
    { 'addr': 'B0:99:28:A4:91:36', 'name': '冷蔵庫'             },
    { 'addr': 'B0:99:28:A4:6A:F4', 'name': 'テレビ'             },

    { 'addr': 'B0:99:28:A4:56:E6', 'name': '洗濯機'             },
    { 'addr': 'B0:99:28:A4:76:37', 'name': 'リビングPC'         },
    { 'addr': 'B0:99:28:A4:74:26', 'name': '乾燥除湿機'        },
    { 'addr': 'B0:99:28:A4:79:E4', 'name': 'アイロン'   },
    { 'addr': 'B0:99:28:A4:75:C6', 'name': '書斎ディスプレイ'   },

    { 'addr': 'B0:99:28:A4:58:AC', 'name': '書斎エアコン'   },
]

# Device B0:99:28:A4:8E:18 F-PLUG ストック
# Device B0:99:28:A4:7A:59 F-PLUG ストック
# Device B0:99:28:A4:68:3D F-PLUG ストック


# subprocess.call('sudo rfcomm unbind all', shell=True)

for i, dev in enumerate(DEVICE_LIST):
    try:
        dev_file = '/dev/rfcomm{0}'.format(i)
        if not os.path.exists(dev_file):
            subprocess.call('sudo rfcomm bind {0} {1}'.format(i, dev['addr']), shell=True)

        fplug = FPlugDevice(dev_file)
        print(json.dumps({
            'hostname': dev['name'],
            'power': fplug.get_power_realtime()
        }))
    except:
        None
