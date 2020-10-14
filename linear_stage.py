import numpy as np
import serial
import os
import time
import json


class LinearStage():
    """

    """

    def __init__(self, thread_pitch = None, stp_per_rev = None, json_path = None):
        self.thread_pitch = thread_pitch
        self.stp_per_rev = stp_per_rev
        self.json_path = json_path
        return

    def read_json(self):
        if self.json_path:
            with open(self.json_path, "r") as f:
                json_str = f.read()
                json_dict = json.loads(json_str)
                self.thread_pitch = json_dict["thread_pitch"]
                self.stp_per_rev = json_dict["stp_per_rev"]

        return

    def send_cmd(cat, parameter):
        if cat not in ["S", "V", "P", "D", "R"]:
            print("Unkown command category")
        else:
            serial_cmd = cat + parameter + "r"
            ser = serial.Serial('/dev/ttyACM0', 250000, timeout=.1)
            ser.write(serial_cmd)
        return
