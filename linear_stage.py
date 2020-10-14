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
        self.ser = serial.Serial()
        return


    def read_json(self):
        if self.json_path:
            with open(self.json_path, "r") as f:
                json_str = f.read()
                json_dict = json.loads(json_str)
                self.thread_pitch = json_dict["thread_pitch"]
                self.stp_per_rev = json_dict["stp_per_rev"]
        return


    def start_serial(self, serial_name):
        try:
            self.ser = serial.Serial(serial_name, 9600, timeout=.1)
            print("Connection is established")
        except:
            print("Could not open serial")
        return


    def close_serial(self):
        if self.ser.is_open:
            self.ser.close()
        return

    def _serial_read(self):
        line = self.ser.readline()
        print(line)

    def send_cmd(self, cat, parameter):
        if cat not in ["S", "V", "P", "D", "R"]:
            print("Unkown command category: %s" %cat)
        else:
            serial_cmd = cat + str(parameter) + "r"
            try:
                self.ser.write(str.encode(serial_cmd))
                print("Sending command: ", serial_cmd)
            except:
                print("Command %s not sent. Could not open serial" %serial_cmd)
        return


    def set_velocity_mm(self, velocity_mm):
        self.velocity_delay_micros = 1e6/((velocity_mm*self.stp_per_rev)/self.thread_pitch)
        self.send_cmd("V", str(self.velocity_delay_micros))
        return


    def set_velocity_stp(self, velocity_stp):
        self.velocity_delay_micros = 1e6/velocity_stp
        self.send_cmd("V", str(self.velocity_delay_micros))
        return


    def set_velocity_delay_micros(self, velocity_delay_micros):
        self.velocity_delay_micros = velocity_delay_micros
        self.send_cmd("V", str(self.velocity_delay_micros))
        return


    def get_velocity(self):
        return


    def set_direction(self, direction):
        self.send_cmd("D", str(direction))
        return


    def get_direction(self):
        return


    def get_current_position(self):
        return


    def move_mm(self, pos_mm):
        stp = pos_mm * self.thread_pitch * self.stp_per_rev
        self.send_cmd("S", stp)
        return


    def move_stp(self, stp):
        self.send_cmd("S", stp)
        return


    def reset_position(self):
        return



if __name__ == "__main__":
    ls = LinearStage(json_path="linear_stage.json")
    ls.read_json()
    ls.start_serial("/dev/ttyACM1")
    ls.move_mm(4)
    time.sleep(1.3)
    ls._serial_read()
