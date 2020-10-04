#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# InfluxDB に記録された外気温と室内気温に基づいて
# 換気扇を自動制御します．

import json
import urllib.request
import subprocess
import sys
import time
import logging
import logging.handlers
import gzip

PWM_KHZ = 25
PWM_DUTY_ON = 30

GPIO_SW = 15

INFLUXDB_HOST = '192.168.2.20:8086'

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
        '/dev/shm/fan_control.log',
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
    subprocess.call('sudo gpio mode 1 pwm', shell=True)
    subprocess.call('sudo gpio pwm-ms', shell=True)
    subprocess.call('sudo gpio pwmc {}'.format(int(19200 / 100 / PWM_KHZ)), shell=True)
    subprocess.call('sudo gpio pwmr 100', shell=True)
    subprocess.call('sudo gpio pwm 1 {}'.format(100 - PWM_DUTY_ON), shell=True)
    subprocess.call('sudo gpio -g mode {} out'.format(GPIO_SW), shell=True)
    subprocess.call('sudo gpio -g write {} {}'.format(GPIO_SW, 1 if mode else 0), shell=True)

def judge_fan_state(temp_out, temp_room, volt_batt):
    # 温度とバッテリー電圧に基づいてファンの ON/OFF を決める
    if (temp_room is None) or (volt_batt is None):
        return False

    # バッテリー電圧が低い場合は止める
    if volt_vatt < 12:
        return False

    if temp_room > 35:
        return True
    elif temp_out is not None:
        if (temp_room - temp_out) > 5:
            return True

    return False


logger = get_logger()

temp_out = influxdb_get('sensor.esp32', 'ESP32-outdoor', 'temp')
temp_room = influxdb_get('sensor.raspberrypi', 'rasp-storeroom', 'temp')
volt_batt = influxdb_get('sensor.raspberrypi', 'rasp-storeroom', 'battery_voltage')

if len(sys.argv) == 1:
    state = judge_fan_state(temp_out, temp_room, volt_batt)
else:
    state = sys.argv[1].lower() == 'on'

fan_ctrl(state)

print('FAN is {}'.format('ON' if state else 'OFF'))

logger.info('FAN: {} (temp_out: {:.2f}, temp_room: {:.2f})'.format(
    'ON' if state else 'OFF',
    temp_out if temp_out is not None else 0.0,
    temp_room if temp_room is not None else 0.0,
))
