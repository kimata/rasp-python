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
            'power': round(dev.insight_params['currentpower']/1000.0, 3),
            'self_time': 0,
        }, ensure_ascii=False)
    )

