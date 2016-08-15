#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

import sensor.hdc1050
import sensor.lps25h
import sensor.tsl2561
import sensor.k30

I2C_BUS = 0x1 # Raspberry Pi

hdc1050 = sensor.hdc1050.HDC1050(I2C_BUS)
if hdc1050.ping():
    value = hdc1050.get_value()
    print('HDC1050 found.')
    print('    TEMP: %.1f, HUMI: %.1f' % (value['temp'], value['humi']))
else:
    print('HDC1050 NOT found.')

lps25h = sensor.lps25h.LPS25H(I2C_BUS)
if lps25h.ping():
    print('LPS25H found.')
    print('    PRESS: %d' % lps25h.get_value())
else:
    print('LPS25G NOT found.')

tsl2561 = sensor.tsl2561.TSL2561(I2C_BUS)
if tsl2561.ping():
    print('TSL2561 found.')
    print('    LUX: %d' % tsl2561.get_lux())
else:
    print('LPS25G NOT found.')

k30 = sensor.k30.K30(I2C_BUS)
if k30.ping():
    print('K30 found.')
    print('    CO2: %d' % k30.get_value())
else:
    print('K30 NOT found.')
    


    
