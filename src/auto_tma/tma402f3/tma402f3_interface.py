#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
################################################################################################
                              WARNING

This program directly switches the relayes of the PLC unit KV-7500 for external control of the TMA.
Each relay apply the voltage to the circuit for TMA control.
Be careful to modify this program and values for safety use.
#################################################################################################
'''

import os
import sys
import time
import yaml
import netzsch_instrument
from plcpy.plc_interface_keyence import PLCInterfaceKeyence

src_file_dir = os.path.dirname(os.path.abspath(__file__))
#pkg_dir = os.path.join(src_file_dir, '../..')
yaml_path = os.path.join(src_file_dir, 'config/plc_config_tma402f3.yaml')

try:
    with open(yaml_path, 'r') as yml:
        cfg = yaml.safe_load(yml)
        tma_cfg = cfg['tma402f3']
except FileNotFoundError as e:
    print(e)
    sys.exit(1)

safety_switch     = tma_cfg['safety_switch']
furnance_close    = tma_cfg['furnance_close']
furnance_open     = tma_cfg['furnance_open']
pushrod_up        = tma_cfg['pushrod_up']
pushrod_up_slow   = tma_cfg['pushrod_up_slow']
pushrod_stop      = tma_cfg['pushrod_stop']
pushrod_down_slow = tma_cfg['pushrod_down_slow']
pushrod_down      = tma_cfg['pushrod_down']
tare_force        = tma_cfg['tare_force']


class TMA402F3Interface(PLCInterfaceKeyence):
    def __init__(self, tma_ip):
        super().__init__(host=tma_ip)


    def connect_tma(self):
        self.open()
        time.sleep(0.1)


    # base command
    def pushrod_up(self):
        print('pushrod_up')
        self.write_bool(pushrod_up, 1)
        time.sleep(0.1)
        self.write_bool(pushrod_up, 0)


    def pushrod_up_slow(self):
        print('pushrod_up_slow')
        self.write_bool(pushrod_up_slow, 1)
        time.sleep(0.1)
        self.write_bool(pushrod_up_slow, 0)


    def pushrod_stop(self):
        print('pushrod_stop')
        self.write_bool(pushrod_stop, 1)
        time.sleep(0.1)
        self.write_bool(pushrod_stop, 0)


    def pushrod_down_slow(self):
        print('pushrod_down_slow')
        self.write_bool(pushrod_down_slow, 1)
        time.sleep(0.1)
        self.write_bool(pushrod_down_slow, 0)


    def pushrod_down(self):
        print('pushrod_down')
        self.write_bool(pushrod_down, 1)
        time.sleep(0.1)
        self.write_bool(pushrod_down, 0)


    def tare_force(self):
        print('tare_force')
        self.write_bool(tare_force, 1)
        time.sleep(0.1)
        self.write_bool(tare_force, 0)
        print(' wait until end (about 65 sec)')  # it takes 65sec from the top (max)
        time.sleep(65)


    # function
    def furnance_close_sec(self, t):
        print('furnance_close')
        self.write_bool(safety_switch, 1)
        self.write_bool(furnance_close, 1)
        print(' wait {} sec'.format(t))
        time.sleep(t)
        print(' furnance stop')
        self.write_bool(safety_switch, 0)
        self.write_bool(furnance_close, 0)


    def furnance_open_sec(self, t):
        print('furnance_open')
        self.write_bool(safety_switch, 1)
        self.write_bool(furnance_open, 1)
        print(' wait {} sec'.format(t))
        time.sleep(t)
        print(' furnance stop')
        self.write_bool(safety_switch, 0)
        self.write_bool(furnance_open, 0)


    def furnance_close_full(self):
        print('furnance_close_full')
        self.furnance_close_sec(8)


    def furnance_open_full(self):
        print('furnance_open_full')
        self.furnance_open_sec(8)


    def pushrod_up_sec(self, t):
        self.pushrod_up()
        print(' wait {} sec'.format(t))
        time.sleep(t)
        self.pushrod_stop()


    def pushrod_up_slow_sec(self, t):
        self.pushrod_up_slow()
        print(' wait {} sec'.format(t))
        time.sleep(t)
        self.pushrod_stop()


    def pushrod_down_sec(self, t):
        self.pushrod_down()
        print(' wait {} sec'.format(t))
        time.sleep(t)
        self.pushrod_stop()


    def pushrod_down_slow_sec(self, t):
        self.pushrod_down_slow()
        print(' wait {} sec'.format(t))
        time.sleep(t)
        self.pushrod_stop()


    # tare_force + pushrodの位置をサンプル挿入に適切な位置へ移動
    def init_pushrod_for_sample_set(self, tare_force=True):
        print('init_pushrod_for_sample_set')
        if tare_force:
            self.tare_force()
        else:
            print('skip tare_force')
            self.pushrod_down_sec(27)  # Pushrod moves to the bottom
        time.sleep(1)
        self.pushrod_up_sec(27)  # Pushrod moves from the bottom to the top until contact to the holder. It takes 27sec. 28sだとぎりぎり, 30sはぶつかる
        time.sleep(1)
        self.pushrod_down_sec(9)  # Best pushrod position: distance between the top surface of the holder and top surface of the pushrod is 15mm. 9sだと15mmでOK. 11sだと18mm.
