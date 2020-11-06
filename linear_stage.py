import numpy as np
import serial
import os
import time
import json
from serial.tools import list_ports


class LinearStage():
    """

    """

#--------------------------------- Initializing --------------------------------
    def __init__(self, thread_pitch = None, stp_per_rev = None, json_path = None):
        self.thread_pitch = thread_pitch
        self.stp_per_rev = stp_per_rev
        self.json_path = json_path
        self.ser = serial.Serial()
        self.loop_time = None

        self.sent_pos_stp = None
        self.sent_pos_mm = None

        self.abs_pos_stp = 0
        self.abs_pos_mm = 0

        self.last_abs_pos_stp = 0
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
        try:
            line = line.decode("utf-8")
            if ";" in line:
                data = line.split(";")
                if len(data) == 5:
                    self.loop_time, self.abs_pos_stp, steps_to_do, velocity_delay_micros, direction = float(data[0])*10**(-3), float(data[1]), float(data[2]), float(data[3]), int(data[4])
                    self.abs_pos_mm = self.stp_to_mm(self.abs_pos_stp)
                    #data_str = "Loop_time", "{:11.4f}".format(self.loop_time), "Absolute position stp", "{:6.0f}".format(self.abs_pos_stp), "Absolute position mm", "{:4.0f}".format(self.abs_pos_mm), "Velocity delay", "{:7.1f}".format(velocity_delay_micros), "us"
                    return data
        except UnicodeDecodeError:
            print("Couldn't decode the serial input.")
            return None

    def send_cmd(self, cat, parameter):
        """ Sends a command for one of the following categories: S - steps,
        V - velocity, P - position, D - direction, R - reset, H - halt"""
        if cat not in ["S", "V", "P", "D", "R", "H"]:
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
        velocity_delay_micros = 1e6/((velocity_mm*self.stp_per_rev)/self.thread_pitch)
        self.send_cmd("V", str(velocity_delay_micros))
        return


    def set_velocity_stp(self, velocity_stp):
        velocity_delay_micros = 1e6/velocity_stp
        self.send_cmd("V", str(velocity_delay_micros))
        return


    def set_velocity_delay_micros(self, velocity_delay_micros):
        velocity_delay_micros = velocity_delay_micros
        self.send_cmd("V", str(velocity_delay_micros))
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
    ports = (list(list_ports.comports()))
    port_name = list(map(lambda p : p["ttyACM" in p.device], ports))[0]
    serial_port = "/dev/" + port_name
    ls.start_serial(serial_port)
    # time.sleep(2)
    ls.serial_read()
