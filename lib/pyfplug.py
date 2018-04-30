#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pyFPlug - F-Plug library for Python

Copyright (C) 2014 SUNAGA Takahiro

This software is released under the MIT License.
http://opensource.org/licenses/mit-license.php

"""

import serial
import time
import datetime
import sys
from struct import *

def hexdump(s):
    print hexdump_str(s)

def hexdump_str(s):
    result = []
    for ch in s:
        b = unpack('B', ch)[0]
        result.append('{0:0>2X}'.format(b))
    return ' '.join(result)

class UnknownState(Exception):
    pass


def struct_num_values(fmt):
    sz = calcsize(fmt)
    return len(unpack(fmt, "\0" * sz))

COMM_WAIT_DEFAULT = 0.1

class FPlugDevice:
    
    def __init__(self, port, timeout = 10, debug = False, ntry = 4, retry_wait = 2, comm_wait = COMM_WAIT_DEFAULT):
        assert 0 < ntry < 10
        self.port = port
        
        last_error = None
        for i in range(ntry):
            try:
                self.sfile = serial.Serial(self.port, 9600, timeout = timeout)
                break
            except serial.serialutil.SerialException, e:
                last_error = e
            time.sleep(retry_wait)
        if last_error:
            raise last_error
            
        self.tid = 100
        self.debug = debug
        self.comm_wait_dur = comm_wait
    
    
    def set_comm_wait(self, comm_wait):
        self.comm_wait_dur = comm_wait
    
    def close(self):
        self.sfile.close()
        self.sfile = None
        self.port = None
    
    def _sfile_read(self, *params):
        time.sleep(self.comm_wait_dur)
        return self.sfile.read(*params)

    def _sfile_write(self, *params):
        time.sleep(self.comm_wait_dur)
        return self.sfile.write(*params)

    def _sfile_set_timeout(self, timeout):
        self.sfile.timeout = timeout

    def clear_recv(self, timeout):
        self.ensure_done(timeout)

    def ensure_done(self, timeout = None):
        if not timeout and not self.debug:
            return
        current_timeout = self.sfile.timeout
        try:
            self.sfile.timeout = 1
            remain = self._sfile_read(1024)
            if remain:
                print "!! BUFFER REMAIN !!:", hexdump_str(remain)
            
        finally:
            self._sfile_set_timeout(current_timeout)

    def read(self, nmax, nthru = 0):
        if nthru:
            thrustr = self._sfile_read(nthru)
            if self.debug:
                print "READ thru:", hexdump_str(thrustr)
            if len(thrustr) < nthru:
                if self.debug:
                    print "Cannot read thru data"
                return None
        rstr = self._sfile_read(nmax)
        if self.debug:
            print "READ:", hexdump_str(rstr)
        return rstr

    def read_byte(self, nthru = 0):
        ch = self.read(1, nthru)
        if ch:
            return unpack('B', ch)[0]
        else:
            return None
            
    def read_format(self, fmt, nthru = 0):
        fmt = '<' + fmt
        sz = calcsize(fmt)
        read_data = self.read(sz, nthru = nthru)
        if len(read_data) < sz:
            return (None,) * struct_num_values(fmt)
        return unpack(fmt, read_data)

    def send_command(self, fmt, **params):
        self.tid += 1
        byte_template = fmt.split(' ')
        fmt = "<"
        data = []
        for elem in byte_template:
            if ':' in elem:
                varname, fmtchar = elem.split(':')
                fmt += fmtchar
                data.append(params[varname])
            elif len(elem) == 2:
                fmt += 'B'
                data.append(int(elem, 16))
            elif len(elem) == 4:
                fmt += 'H'
                data.append(int(elem, 16))
            else:
                raise Exception('Unknown format')
        sending_data = pack(fmt, *data)
        if self.debug:
            print "packing:", (fmt, data)
            print "sending:", hexdump_str(sending_data)
        ntry = 20
        while True:
            try:
                # self.sfile.sendBreak(1.0)
                self.sfile.write(sending_data)
                break
            except serial.serialutil.SerialException, e:
                if ntry <= 0:
                    raise e
                ntry -= 1
                if self.debug:
                    print "Retry send:", ntry 
                time.sleep(0.5)

    def plug_init(self):
        """ (1.1 Plug Initialize Request) """
        now = datetime.datetime.now()
        self.send_command(
            "10 81 tid:H 0E F0 00 00 22 00 61 02 97 02 hour:B minute:B 98 04 year:H month:B day:B",
            tid = self.tid,
            hour = now.hour,
            minute = now.minute,
            year = now.year,
            month = now.month,
            day = now.day
        )
        esv = self.read_byte(nthru = 10)
        if esv == 0x71:
            self.read(5)
            
            # BUG of F-Plug?: too long message of 0x00 * 6
            self.read(6)

            self.ensure_done()
            return True

        elif esv == 0x51:
            self.read(11)
            self.ensure_done()
            return False
        else:
            raise UnknownState("ESV={0}".format(esv))
        
    
    def get_prop_value(self, prop_class_code, epc1, pdc1, value_format = 'h', remain_size = None):
        self.send_command(
            "10 81 tid:H 0E F0 00 00 prop_class_code:B 00 62 01 epc1:B pdc1:B",
            tid = self.tid,
            prop_class_code = prop_class_code,
            epc1 = epc1,
            pdc1 = pdc1
        )
        esv = self.read_byte(10)
        if esv == 0x72:
            _opc, _epc1, _pdc1, value = self.read_format('BBB' + value_format)
            if remain_size:
                self._sfile_read(remain_size)
            self.ensure_done()
            return value
        elif esv == 0x52:
            self.read(3)
            if remain_size:
                self._sfile_read(remain_size)
            self.ensure_done()
            return None
        else:
            raise UnknownState("ESV = {0}".format(esv))
        
    
    def get_temperature(self):
        """
            (2.3 Get temperature)
            Returns: temp in degree(float) or None (failure)
        """
        pval = self.get_prop_value(0x11, epc1 = 0xE0, pdc1 = 0x00)
        return float(pval) / 10.0 if pval else None
        
    def get_humidity(self):
        """
            (2.6 Get humidity)
            Returns: humidity % or None (failure)
        """
        return self.get_prop_value(0x12, epc1 = 0xE0, pdc1 = 0x00)
        
    def get_illuminance(self):
        """
            (2.9 Get illuminance)
            Returns: illuminance or None (failure)
        """
        return self.get_prop_value(0x0D, epc1 = 0xE0, pdc1 = 0x00)

    def get_power_realtime(self):
        """
            (2.12 Get power real-time)
            Returns: power or None (failure)
        """
        pval = self.get_prop_value(0x22, epc1 = 0xE2, pdc1 = 0x02)
        
        return float(pval) / 10.0 if pval is not None else None
    

    def get_data_dict(self):
        return {
            'temperature': self.get_temperature(),
            'humidity': self.get_humidity(),
            'illuminance': self.get_illuminance(),
            'power': self.get_power_realtime(),
        }

    def get_prop_histry24(self, req_kind, dt, struct, vfunc):
        self.send_command(
            "10 82 tid:H req_kind:B hour:B minute:B year:H month:B day:B",
            tid = self.tid,
            req_kind = req_kind,
            hour = dt.hour,
            minute = dt.minute,
            year = dt.year,
            month = dt.month,
            day = dt.day
        )
        is_fail = self.read_byte(nthru = 5)
        result = []
        for i in range(24):
            v_tuple = self.read_format(struct)
            if not is_fail:
                result.append(vfunc(*v_tuple))
        self.ensure_done()
        if is_fail:
            return None
        else:
            return result

    def get_acc_power(self):
        """ (2.1 get accumulated power value ) """
        return self.get_prop_histry24(
            0x11,
            datetime.datetime.now(),
            'HB',
            lambda val, err: None if err else val
        )
    
    def get_power_data_history(self, time = None):
        """ (2.16 get accumulated power value in past ) """
        return self.get_prop_histry24(
            0x16,
            time,
            'HB',
            lambda val, err: None if err else val
        )

    def get_misc_data_history(self, time = None):
        """ (2.16 get data history ) """
        return self.get_prop_histry24(
            0x17,
            time,
            'HBH',
            lambda vt, vh, vi: (
                None if vt == 0xEEEE else float(vt) / 10.0,
                None if vh == 0xEE else vh,
                None if vi == 0xEEEE else vi
            )
        )

    def dump_all(self):
        while True:
            wlen = self.sfile.inWaiting()
            if wlen == 0:
                time.sleep(1)
                continue
            
            hexdump(self.sfile.read(wlen))
    
    def set_led(self, state = 0):
        self.send_command('05 state:B', state = state)
        _rk, result = self.read_format('BB')
        self.ensure_done()
        return result

    def led_on(self):
        return self.set_led(1)

    def led_off(self):
        return self.set_led(0)


    def set_datetime(self, dt = None):
        if not dt:
            dt = datetime.datetime.now()
        self.send_command(
            "07 hour:B minute:B year:H month:B day:B",
            hour = dt.hour,
            minute = dt.minute,
            year = dt.year,
            month = dt.month,
            day = dt.day - 5
        )
        is_fail = self.read_byte(nthru = 1)
        self.ensure_done()
        if is_fail == 0:
            return True
        elif is_fail == 1:
            return False
        else:
            raise UnknownState()
    
    def clear(self):
        self.comm_wait()
        self.sfile.flush()

def test_fplug_dev():
    dev = FPlugDevice('/dev/rfcomm0', debug = True)
    # print "init:", dev.plug_init()
    

    print "on:", dev.led_on()
    time.sleep(0.5)
    print "off:", dev.led_off()

    print "set_datetime:", dev.set_datetime()
    
    print "TMP:", dev.get_temperature(), "degree C"
    print "HUM:", dev.get_humidity(), "%"
    print "ILL:", dev.get_illuminance(), ""
    print "PWR:", dev.get_power_realtime(), "W"
    
    print "ACC:", dev.get_acc_power()
    
    print "HIST PWR:", dev.get_power_data_history(datetime.datetime.now())
    print "HIST MISC:", dev.get_misc_data_history(datetime.datetime.now())

if __name__ == '__main__':
    test_fplug_dev()

