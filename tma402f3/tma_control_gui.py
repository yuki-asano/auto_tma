#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, scrolledtext
import sys
import io
from netzsch_instrument.tma402f3.tma402f3_interface import TMA402F3Interface


class TMAControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TMA Control GUI")
        self.tma_ip = '192.168.0.20'
        self.tma_if = TMA402F3Interface(self.tma_ip)

        # connect to tma
        self.tma_if.connect_tma()

        # define button
        self.btn_tma_open = tk.Button(root, text="furnance_open_full", command=self.tma_if.furnance_open_full)
        self.btn_tma_open.pack(pady=10)

        self.btn_tma_close = tk.Button(root, text="furnance_close_full", command=self.tma_if.furnance_close_full)
        self.btn_tma_close.pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = TMAControlGUI(root)
    root.mainloop()
