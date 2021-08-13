import warnings
warnings.simplefilter('ignore')

import pywemo
import json

devices = pywemo.discover_devices()

for dev in devices:
    if dev.__class__ is not pywemo.ouimeaux_device.insight.Insight:                                                                                                              
        continue

    print(
        json.dumps({
            'hostname': dev.name,
            'power': int(dev.insight_params['currentpower']/1000),
            'self_time': 0,
        }, ensure_ascii=False)
    )

