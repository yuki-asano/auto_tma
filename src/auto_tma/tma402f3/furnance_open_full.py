#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from netzsch_instrument.tma402f3.tma402f3_interface import TMA402F3Interface


def main():
    tma_ip = '192.168.0.20'
    tma_if = TMA402F3Interface(tma_ip)
    tma_if.connect_tma()

    try:
        print('Waiting for real motion of TMA')
        input('[Enter] -> start, [Ctrl+c] -> exit ...\n')
    except KeyboardInterrupt:
        print('Exit')
        sys.exit()

    print('furnance_open_full')
    tma_if.furnance_open_full()


if __name__ =='__main__':
    main()
