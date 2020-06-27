#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import json

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

from pyfplug import *
from fplug_list import *

# subprocess.call('sudo rfcomm unbind all', shell=True)

for i, dev in enumerate(DEVICE_LIST):
    try:
        dev_file = '/dev/rfcomm{0}'.format(i)
        if not os.path.exists(dev_file):
            subprocess.call('sudo rfcomm bind {0} {1}'.format(i, dev['addr']), shell=True)

        fplug = FPlugDevice(dev_file)
        print(json.dumps({
            'hostname': dev['name'],
            'power': fplug.get_power_realtime(),
            'self_time': 0,
        })
    except:
        None
