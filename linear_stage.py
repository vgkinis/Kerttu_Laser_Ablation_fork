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
        self.loop_time = None
        self.abs_pos_stp = 0
        self.abs_pos_mm = 0
        self.last_abs_pos_mm = 0
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

    def serial_read(self):
        line = self.ser.readline()
        line = line.decode("utf-8")
        if ";" in line:
            data = line.split(";")
            if len(data) == 3:
                self.loop_time, self.abs_pos_stp, self.velocity_delay_micros = float(data[0])*10**(-3), float(data[1]), float(data[2])
                self.abs_pos_mm = int((self.thread_pitch*self.abs_pos_stp)/self.stp_per_rev)
                data_str = "Loop_time", "{:11.4f}".format(self.loop_time), "Absolute position", "{:4.0f}".format(self.abs_pos_mm), "velocity delay", "{:7.1f}".format(self.velocity_delay_micros), "us"
                return data_str
        return line

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
        stp = (pos_mm * self.stp_per_rev)/self.thread_pitch
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
    ls.start_serial("/dev/ttyACM0")
    time.sleep(2)

    usr_pos_str = input("Enter the distance in mm (press x to exit): ")
    usr_pos = int(usr_pos_str)
    ls.move_mm(usr_pos)
    while True:
        serial_data = ls.serial_read()
        if serial_data: print(serial_data)

        if (ls.abs_pos_mm-ls.last_abs_pos_mm) == usr_pos:
            usr_pos_str = input("Enter the distance in mm (press x to exit): ")
            if usr_pos_str == "x":
                break
            usr_pos = int(usr_pos_str)
            ls.move_mm(usr_pos)
            ls.last_abs_pos_mm = ls.abs_pos_mm
            ls.ser.flushInput()
