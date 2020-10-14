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
        self.velocity_delay_micros = None
        return

    def read_json(self):
        if self.json_path:
            with open(self.json_path, "r") as f:
                json_str = f.read()
                json_dict = json.loads(json_str)
                self.thread_pitch = json_dict["thread_pitch"]
                self.stp_per_rev = json_dict["stp_per_rev"]

        return

    def send_cmd(self, cat, parameter):
        if cat not in ["S", "V", "P", "D", "R"]:
            print("Unkown command category: %s" %cat)
        else:
            serial_cmd = cat + str(parameter) + "r"
            try:
                ser = serial.Serial('/dev/ttyACM0', 250000, timeout=.1)
                ser.write(serial_cmd)
            except:
                print("Command %s not sent. Could not open serial" %serial_cmd)
        return

    def set_velocity_mm(self, velocity_mm):
        self.velocity_delay_micros = 1/((velocity_mm*self.stp_per_rev)/self.thread_pitch)
        serial_cmd = "V" + str(velocity_delay_micros) + "r"
        send_cmd("V", str(velocity_delay_micros))
        return

    def set_velocity_stp(self, velocity_stp):
        self.velocity_delay_micros = self.thread_pitch/velocity_stp
        send_cmd("V", str(velocity_delay_micros))
        return

    def set_velocity_delay_micros(self, velocity_delay_micros):
        self.velocity_delay_micros = velocity_delay_micros
        send_cmd("V", str(self.velocity_delay_micros))
        return

    def get_velocity(self):
        return

    def set_direction(self, direction):
        serial_cmd = "D" + str(direction) + "r"
        send_cmd("D", str(direction))
        return

    def get_direction(self):
        return

    def get_current_position(self):
        return

    def move_mm(self, pos_mm):
        stp = pos_mm * self.thread_pitch * self.stp_per_rev
        serial_cmd = "S" + str(stp) + "r"
        send_cmd(serial_cmd)
        return

    def move_stp(self, stp):
        serial_cmd = "S" + str(stp) + "r"
        send_cmd(serial_cmd)
        return

    def reset_position(self):
        return
