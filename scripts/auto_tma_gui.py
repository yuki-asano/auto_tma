#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import rospy
from auto_tma.auto_tma_main import main
from netzsch_tma402f3.tma402f3_interface import TMA402F3Interface
from std_msgs.msg import Bool

# connect to tma
tma_ip = '192.168.0.20'
tma_if = TMA402F3Interface(tma_ip)
tma_if.connect_tma()


def on_run():
    def worker():
        try:
            main(
                tma_auto=var_tma_auto.get(),
                tare_force=var_tare_force.get(),
                measure_mode=int(entry_num_measure.get()),
                number_of_sample=int(entry_num_sample.get()),
                gui_log_cb=write_log
            )

            messagebox.showinfo("Result", "Process finished")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    threading.Thread(target=worker, daemon=True).start()


def pub_measure_finished():
    pub = rospy.Publisher("/measure_finished", Bool, queue_size=1, latch=True)
    rospy.loginfo("Publishing /measure_finished = True")
    pub.publish(True)


# tk
root = tk.Tk()
root.title("AutoTMA GUI")
root.geometry("800x400")


# devide frame
left_frame = tk.Frame(root, width=300, padx=10, pady=10)
left_top_frame = tk.Frame(left_frame)
left_bottom_frame = tk.Frame(left_frame)
center_frame = tk.Frame(root, width=300, padx=10, pady=10)
right_frame = tk.Frame(root, padx=10, pady=10)

left_frame.pack(side="left", fill="y")
left_top_frame.pack(side="top", fill="y")
left_bottom_frame.pack(side="bottom", fill="y")
center_frame.pack(side="left", fill="y")
right_frame.pack(side="right", fill="y", expand=True)


# define TMA control function (left top)
tk.Label(left_top_frame, text="TMA control function", font=("Arial", 12, "bold")).pack(anchor="w")
tk.Button(left_top_frame, text="furnance_open_full", command=tma_if.furnance_open_full).pack(anchor="w")
tk.Button(left_top_frame, text="furnance_close_full", command=tma_if.furnance_close_full).pack(anchor="w")
tk.Button(left_top_frame, text="init_pushrod_for_sample_set", command=tma_if.init_pushrod_for_sample_set).pack(anchor="w")
tk.Button(left_top_frame, text="reset_tma", command=tma_if.reset_tma).pack(anchor="w")

# define TMA button (left bottom)
tk.Label(left_bottom_frame, text="TMA control panel", font=("Arial", 12, "bold"), anchor="w").grid(row=0, column=0)
tk.Button(left_bottom_frame, text="furnance_open", command=tma_if.furnance_open_full).grid(row=1, column=0, pady=5)  # full open instead open during pushing
tk.Button(left_bottom_frame, text="furnance_close", command=tma_if.furnance_close_full).grid(row=1, column=1, pady=5)  # full close instead close during pushing

tk.Button(left_bottom_frame, text="pushrod_up_slow", command=tma_if.pushrod_up_slow).grid(row=2, column=0, pady=5)
tk.Button(left_bottom_frame, text="pushrod_up", command=tma_if.pushrod_up).grid(row=2, column=1, pady=5)
tk.Button(left_bottom_frame, text="pushrod_stop", command=tma_if.pushrod_stop).grid(row=3, column=1)
tk.Button(left_bottom_frame, text="pushrod_down_slow", command=tma_if.pushrod_down_slow).grid(row=4, column=0, pady=5)
tk.Button(left_bottom_frame, text="pushrod_down", command=tma_if.pushrod_down).grid(row=4, column=1, pady=5)

tk.Button(left_bottom_frame, text="tare_force", command=tma_if.tare_force).grid(row=5, column=1, pady=5)


# define auto_tma exp (center)
tk.Label(center_frame, text="AutoTMA", font=("Arial", 12, "bold")).pack(anchor="w")
var_tma_auto = tk.BooleanVar(value=True)
var_tare_force = tk.BooleanVar(value=True)

tk.Checkbutton(center_frame, text="TMA auto move", variable=var_tma_auto).pack(anchor="w")
tk.Checkbutton(center_frame, text="tare force", variable=var_tare_force).pack(anchor="w")

# measure_mode
tk.Label(center_frame, text="measure_mode(0:AUTO, 1:MANUAL, 2:SKIP)").pack(anchor="w")
entry_num_measure = tk.Entry(center_frame)
entry_num_measure.insert(0, "0")
entry_num_measure.pack(anchor="w")

# number of samples
tk.Label(center_frame, text="number_of_sample").pack(anchor="w")
entry_num_sample = tk.Entry(center_frame)
entry_num_sample.insert(0, "2")
entry_num_sample.pack(anchor="w")

# Run button
tk.Button(center_frame, text="Run", command=on_run).pack(anchor="w")

# finish measure button
tk.Label(center_frame, text="For manual measurement", font=("Arial", 11)).pack(anchor="w", pady=(20, 0))
tk.Button(center_frame, text="Finish measurement", command=pub_measure_finished).pack(anchor="w")


# define log display (right)
tk.Label(right_frame, text="Log", font=("Arial", 11)).pack(anchor="w", pady=(20, 0))
log_text = scrolledtext.ScrolledText(
    right_frame,
    width=60,
    height=20,
    state="disabled"
)
log_text.pack(fill="both", expand=True, pady=10)

def write_log(message):
    log_text.configure(state="normal")
    log_text.insert("end", message + "\n")
    log_text.see("end")  # auto scrole
    log_text.configure(state="disabled")



if __name__ == "__main__":
    rospy.init_node("auto_tma", disable_signals=True)  # init ros
    root.mainloop()
