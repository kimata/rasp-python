#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# InfluxDB に記録された外気温と室内気温に基づいて
# 換気扇を自動制御します．

import subprocess
import sys
import logging
import logging.handlers
import gzip
import pathlib
import yaml
import os
import influxdb_client

FLUX_QUERY = """
from(bucket: "{bucket}")
    |> range(start: -{period})
    |> filter(fn:(r) => r._measurement == "{measure}")
    |> filter(fn: (r) => r.hostname == "{hostname}")
    |> filter(fn: (r) => r["_field"] == "{param}")
    |> aggregateWindow(every: 3m, fn: mean, createEmpty: false)
    |> exponentialMovingAverage(n: 3)
    |> sort(columns: ["_time"], desc: true)
    |> limit(n: 1)
"""

CONFIG_PATH = "./config.yml"


def load_config():
    path = str(pathlib.Path(os.path.dirname(__file__), CONFIG_PATH))
    with open(path, "r") as file:
        return yaml.load(file, Loader=yaml.SafeLoader)


class GZipRotator:
    def namer(name):
        return name + ".gz"

    def rotator(source, dest):
        with open(source, "rb") as fs:
            with gzip.open(dest, "wb") as fd:
                fd.writelines(fs)
        os.remove(source)


def get_logger():
    logger = logging.getLogger()
    log_handler = logging.handlers.RotatingFileHandler(
        "/dev/shm/fan_control.log",
        encoding="utf8",
        maxBytes=1 * 1024 * 1024,
        backupCount=10,
    )
    log_handler.formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s :%(message)s",
        datefmt="%Y/%m/%d %H:%M:%S %Z",
    )
    log_handler.namer = GZipRotator.namer
    log_handler.rotator = GZipRotator.rotator

    logger.addHandler(log_handler)
    logger.setLevel(level=logging.INFO)

    return logger


def get_db_value(
    config,
    hostname,
    measure,
    param,
):
    client = influxdb_client.InfluxDBClient(
        url=config["influxdb"]["url"],
        token=config["influxdb"]["token"],
        org=config["influxdb"]["org"],
    )

    query_api = client.query_api()

    table_list = query_api.query(
        query=FLUX_QUERY.format(
            bucket=config["influxdb"]["bucket"],
            measure=measure,
            hostname=hostname,
            param=param,
            period="1h",
        )
    )

    return table_list[0].records[0].get_value()


def fan_ctrl(config, mode):
    subprocess.call("sudo gpio mode 1 pwm", shell=True)
    subprocess.call("sudo gpio pwm-ms", shell=True)
    subprocess.call(
        "sudo gpio pwmc {}".format(int(19200 / 100 / config["pwm"]["khz"])), shell=True
    )
    subprocess.call("sudo gpio pwmr 100", shell=True)
    subprocess.call(
        "sudo gpio pwm 1 {}".format(100 - config["pwm"]["duty_on"]), shell=True
    )
    subprocess.call("sudo gpio -g mode {} out".format(config["gpio"]["sw"]), shell=True)
    subprocess.call(
        "sudo gpio -g write {} {}".format(config["gpio"]["sw"], 1 if mode else 0),
        shell=True,
    )


def judge_fan_state(temp_out, temp_room, volt_batt):
    # 温度とバッテリー電圧に基づいてファンの ON/OFF を決める
    if (temp_room is None) or (volt_batt is None):
        return False

    # バッテリー電圧が低い場合は止める
    if volt_batt < 13.0:
        return False

    if temp_room > 35:
        return True
    elif temp_out is not None:
        if (temp_room - temp_out) > 5:
            return True

    return False


config = load_config()
logger = get_logger()

temp_out = get_db_value(config, "ESP32-outdoor-1", "sensor.esp32", "temp")
temp_room = get_db_value(config, "rasp-storeroom", "sensor.rasp", "temp")
volt_batt = get_db_value(config, "rasp-storeroom", "sensor.rasp", "battery_voltage")

if len(sys.argv) == 1:
    state = judge_fan_state(temp_out, temp_room, volt_batt)
else:
    state = sys.argv[1].lower() == "on"

fan_ctrl(config, state)

print("FAN is {}".format("ON" if state else "OFF"))

logger.info(
    "FAN: {} (temp_out: {:.2f}, temp_room: {:.2f})".format(
        "ON" if state else "OFF",
        temp_out if temp_out is not None else 0.0,
        temp_room if temp_room is not None else 0.0,
    )
)
