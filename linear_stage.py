import numpy as np
import serial
import os
import time
import json


class LinearStage():
    """

    """

#--------------------------------- Initializing --------------------------------
    def __init__(self, thread_pitch = None, stp_per_rev = None, json_path = None):
        self.thread_pitch = thread_pitch
        self.stp_per_rev = stp_per_rev
        self.json_path = json_path
        self.velocity_delay_micros = None
        self.ser = serial.Serial()
        self.loop_time = None

        self.sent_pos_stp = None
        self.sent_pos_mm = None

        self.abs_pos_stp = 0
        self.abs_pos_mm = 0

        self.last_abs_pos_stp = 0
        self.last_abs_pos_mm = 0

        self.direction = 1
        return


    def read_json(self):
        if self.json_path:
            with open(self.json_path, "r") as f:
                json_str = f.read()
                json_dict = json.loads(json_str)
                self.thread_pitch = json_dict["thread_pitch"]
                self.stp_per_rev = json_dict["stp_per_rev"]
        return


#------------------------------- Serial functions ------------------------------
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
                self.abs_pos_mm = self.stp_to_mm(self.abs_pos_stp)
                data_str = "Loop_time", "{:11.4f}".format(self.loop_time), "Absolute position stp", "{:6.0f}".format(self.abs_pos_stp), "Absolute position mm", "{:4.0f}".format(self.abs_pos_mm), "Velocity delay", "{:7.1f}".format(self.velocity_delay_micros), "us"
                return str(data_str)
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

#--------------------------------- Conversions ---------------------------------

    def stp_to_mm(self, stp):
        return int((self.thread_pitch*stp)/self.stp_per_rev)

    def mm_to_stp(self, mm):
        return int((mm * self.stp_per_rev)/self.thread_pitch)

#--------------------------------- Set & Get -----------------------------------

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
        self.sent_pos_mm = pos_mm
        stp = self.mm_to_stp(pos_mm)
        self.sent_pos_stp = stp
        self.send_cmd("S", abs(self.sent_pos_stp))
        return


    def move_stp(self, stp):
        self.sent_pos_stp = stp
        self.sent_pos_mm = self.stp_to_mm(self.sent_pos_stp)
        self.send_cmd("S", abs(self.sent_pos_stp))
        return


    def reset_position(self):
        return

    def check_if_ready(self):
        if self.sent_pos_mm == None and self.sent_pos_stp == None:
            print("Ready! No positions have been sent.")
            return True
        elif (self.abs_pos_stp-self.last_abs_pos_stp) == self.sent_pos_stp:
            self.last_abs_pos_mm = self.abs_pos_mm
            self.last_abs_pos_stp = self.abs_pos_stp

            self.sent_pos_stp = None
            self.sent_pos_mm = None
            print("Ready! Position reached.")
            return True
        else:
            return False


#--------------------------------- if __main__ ---------------------------------
if __name__ == "__main__":
    ls = LinearStage(json_path="linear_stage.json")
    ls.read_json()
    ls.start_serial("/dev/ttyACM0")
    time.sleep(2)

    ls.set_velocity_delay_micros(1000)
    time.sleep(2)
    while True:
        if ls.check_if_ready():
            usr_pos_mm = int(input("Enter the distance in mm:"))
            if usr_pos_mm > 0:
                if ls.direction != 1:
                    ls.set_direction(1)
                    ls.direction = 1
                    time.sleep(2)
            else:
                if ls.direction != 0:
                    ls.set_direction(0)
                    ls.direction = 0
                    time.sleep(2)
            ls.ser.flushInput()
            ls.sent_pos_mm = usr_pos_mm
            ls.sent_pos_stp = ls.mm_to_stp(ls.sent_pos_mm)
            ls.move_stp(ls.sent_pos_stp)
        serial_data = ls.serial_read()
        if serial_data: print(serial_data)
