#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# InfluxDB に記録された外気温と室内気温に基づいて
# 換気扇を自動制御します．

import json
import urllib.request
import RPi.GPIO as GPIO

import pprint

INFLUXDB_HOST = '192.168.2.20:8086'

GPIO_FAN = 15

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def influxdb_get(db, host, name):
    url = 'http://' + INFLUXDB_HOST + '/query'

    params = {
        'db': 'sensor',
        'q': ('SELECT {} FROM "{}" WHERE "hostname" = \'{}\' AND time > now() - {} ' + 
              'ORDER by time desc LIMIT {}').format(name, db, host, '1h', '1')
    }
    data = urllib.parse.urlencode(params).encode("utf-8")

    try:
        with urllib.request.urlopen(url, data=data) as res:
            result = res.read().decode("utf-8")
            return json.loads(result)['results'][0]['series'][0]['values'][0][1]
    except:
        return None

def fan_ctrl(mode):
    GPIO.setup(GPIO_FAN, GPIO.OUT)
    GPIO.output(GPIO_FAN, 1 if mode else 0)

def judge_fan_state(temp_out, temp_room):
    # 温度に基づいてファンの ON/OFF を決める
    if temp_room > 28:
        return True
    elif temp_out is not None:
        if (temp_room - temp_out) > 2:
            return True
        else:
            return False
    else:
        return False

temp_out = influxdb_get('sensor.esp32', 'ESP32-outdoor', 'temp')
temp_room = influxdb_get('sensor.raspberrypi', 'rasp-storeroom', 'temp')

state = judge_fan_state(temp_out, temp_room)

fan_ctrl(state)

print('FAN is {}'.format('ON' if state else 'OFF'))





