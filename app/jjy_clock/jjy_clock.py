#!/usr/bin/python
# coding: utf-8
# 
# JJY タイムコードを出力するスクリプト．
# GPIO に H を出力する事で 40kHz パルスが停止する回路を想定
# しています．

import RPi.GPIO as GPIO
import datetime
import time

# JJY 時刻符号を出力する端子
GPIP_PORT = 4

def set_pin(mode):
    GPIO.output(GPIP_PORT, mode)

def send_bit(bit):
    if bit == -1: # マーカ
        set_pin(1)
        time.sleep(0.2)
        set_pin(0)
        time.sleep(0.799)
    elif bit == 0: # 0
        set_pin(1)
        time.sleep(0.799)
        set_pin(0)
        time.sleep(0.2)
    elif bit == 1: # 1
        set_pin(1)
        time.sleep(0.499)
        set_pin(0)
        time.sleep(0.5)

def send_bcd(num, count, parity=0):
    for i in range(count):
        bit = (num >> ((count-1) - i)) & 0x1
        send_bit(bit)
        parity ^= bit
    return parity

def send_datetime(now):
    now = datetime.datetime.now()
    minute = now.minute
    hour = now.hour
    day = now.toordinal() - datetime.date(now.year, 1, 1).toordinal() + 1
    year = now.year % 100
    wday = now.isoweekday() % 7
    sec = now.second
    usec = now.microsecond

    min_parity = 0
    hour_parity = 0

    ############################################################
    send_bit(-1)
    
    # 10分位のBCD
    min_parity = send_bcd(minute/10, 3, min_parity)
    
    send_bit(0)
    
    # 1分位のBCD
    min_parity = send_bcd(minute%10, 4, min_parity)
    
    send_bit(-1)

    ############################################################
    send_bit(0)
    send_bit(0)
    
    # 10時位のBCD
    hour_parity = send_bcd(hour/10, 2, hour_parity)
    
    send_bit(0)
    
    # 1時位のBCD
    hour_parity = send_bcd(hour%10, 4, hour_parity)
    
    send_bit(-1)
    
    ############################################################
    send_bit(0)
    send_bit(0)
    
    # 累計日数100日位のBCD
    send_bcd(day/100, 2)
    
    send_bit(0)

    # 累計日数10日位のBCD
    send_bcd((day%100) / 10, 4)
    
    send_bit(-1)

    ############################################################
    # 累計日数1日位のBCD    
    send_bcd(day%10, 4)
    
    send_bit(0)
    send_bit(0)
    
    # パリティ
    send_bit(hour_parity)
    send_bit(min_parity)
    
    send_bit(0)
    send_bit(-1)

    ############################################################
    send_bit(0)
    
    # 西暦年10年位のBCD
    send_bcd((year%100)/10, 4)
    
    # 西暦年1年位のBCD
    send_bcd(year%10, 4)
    
    send_bit(-1)

    ############################################################
    # 曜日のBCD
    send_bcd(wday, 3)
    
    send_bit(0)
    send_bit(0)
    send_bit(0)
    send_bit(0)
    send_bit(0)
    send_bit(0)

    # マーカ
    set_pin(1)
    time.sleep(0.2)
    set_pin(0)
    # 0.8 秒残しておき，次回呼び出しタイミングの調整代とする

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIP_PORT, GPIO.OUT)
set_pin(0)

while True:
    now = datetime.datetime.now()
    minute = now.minute
    sec = now.second
    usec = now.microsecond

    # 0 秒になるまで待つ
    time.sleep(180 - (sec + usec/1000000.0))

    send_datetime(now + datetime.timedelta(minutes=1))
