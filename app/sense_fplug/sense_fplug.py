#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import traceback
import json
import logging
import logging.handlers
import gzip
import warnings

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "lib"))

from pyfplug import *
from fplug_list import *
from bt_rssi import *


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
        "/dev/shm/sense_fplug.log",
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


logger = get_logger()

subprocess.call("sudo rfcomm unbind all", shell=True)

is_all_fail = True

for i, dev in enumerate(DEVICE_LIST[os.uname()[1]]):
    try:
        logger.info("DEVICE: {0} {1}".format(dev["name"], dev["addr"]))
        dev_file = "/dev/rfcomm{0}".format(i)
        if not os.path.exists(dev_file):
            subprocess.call(
                "sudo rfcomm bind {0} {1}".format(i, dev["addr"]), shell=True
            )

        btrssi = BluetoothRSSI(dev["addr"])
        rssi = -100
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            rssi = btrssi.request_rssi()[0]
        fplug = FPlugDevice(dev_file, comm_wait=0.2)

        result = json.dumps(
            {
                "hostname": dev["name"],
                "power": fplug.get_power_realtime(),
                "temp": fplug.get_temperature(),
                "humi": fplug.get_humidity(),
                "rssi": rssi,
                "self_time": 0,
            },
            ensure_ascii=False,
        )

        logger.info(result)
        print(result)

        is_all_fail = False
    except:
        logger.warning(traceback.format_exc())
        pass


if is_all_fail:
    logger.warning("Restart the Bluetooth service because the error persists.")
    cmd = "sudo /etc/init.d/bluetooth restart"

    logger.warning(cmd)
    logger.warning(os.popen(cmd).read())
