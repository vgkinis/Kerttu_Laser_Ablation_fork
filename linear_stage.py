
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
    def __init__(self, thread_pitch = None, stp_per_rev = None, stage_length = None, json_path = None):
        self.thread_pitch = thread_pitch
        self.stp_per_rev = stp_per_rev
        self.stage_length = stage_length
        self.json_path = json_path
        self.ser = serial.Serial()
        self.loop_time = None

        self.sent_pos_stp = None
        self.sent_pos_mm = None

        self.abs_pos_stp = 0
        self.abs_pos_mm = 0

        self.event_code = None

        self.count_range_start = None

        return


    def read_json(self):
        if self.json_path:
            with open(self.json_path, "r") as f:
                json_str = f.read()
                json_dict = json.loads(json_str)
                self.thread_pitch = json_dict["thread_pitch"]
                self.stp_per_rev = json_dict["stp_per_rev"]
                self.stage_length = json_dict["stage_length"]
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

        if "s" in line and "r" in line:
            idx_s = line.index("s")
            idx_r = line.index("r")
            if idx_s < idx_r:
                line = line[idx_s+1 : idx_r]
                data = line.split(";")
                self.loop_time, self.abs_pos_stp, dis_stp, spd_us, direction, self.event_code = float(data[0])*10**(-3), float(data[1]), float(data[2]), float(data[3]), int(data[4]), int(data[5])
                self.abs_pos_mm = self.stp_to_mm(self.abs_pos_stp)
                data_dict = {"loop_time": self.loop_time,
                                "pos_steps": self.abs_pos_stp,
                                "pos_rev": self.stp_to_rev(self.abs_pos_stp),
                                "pos_mm": self.abs_pos_mm,
                                "dis_steps": dis_stp,
                                "dis_mm": self.stp_to_mm(dis_stp),
                                "dis_rev": self.stp_to_rev(dis_stp),
                                "spd_us/step": spd_us,
                                "spd_step/s": self.us_stp_to_stp_s(spd_us),
                                "spd_rev/s": self.us_stp_to_rev_s(spd_us),
                                "spd_mm/s": self.us_stp_to_mm_s(spd_us),
                                "direction": direction,
                                "event_code": self.event_code,
                                }
                return data_dict
            else:
                return "failed 2 if", line
        else:
            return "failed 1 if", line


    def send_cmd(self, cat, parameter=""):
        """ Sends a command for one of the following categories: S - steps,
        V - velocity (speed), P - position, D - direction, R - reset,
        E - event code, A - absolute position, "W" - write from Arduino"""
        if cat not in ["S", "V", "P", "D", "R", "E", "A", "W"]:
            print("Unkown command category: %s" %cat)
        else:
            serial_cmd = cat + str(parameter) + "r"
            try:
                self.ser.write(str.encode(serial_cmd))
                if "W" not in serial_cmd:
                    print("Sending command: ", serial_cmd)
            except:
                print("Command %s not sent. Could not open serial" %serial_cmd)
        return

#--------------------------------- Conversions ---------------------------------

    # Functions for distance
    def stp_to_mm(self, stp):
        return int((self.thread_pitch*stp)/self.stp_per_rev)

    def mm_to_stp(self, mm):
        return int((mm * self.stp_per_rev)/self.thread_pitch)

    def stp_to_rev(self, stp):
        return int(stp/self.stp_per_rev)

    def rev_to_stp(self, rev):
        return int(rev*self.stp_per_rev)

    # Functions for speed
    def us_stp_to_mm_s(self, us_stp):
        return self.us_stp_to_rev_s(us_stp)*self.thread_pitch

    def mm_s_to_us_stp(self, mm_s):
        return 1e6/((mm_s*self.stp_per_rev)/self.thread_pitch)

    def us_stp_to_stp_s(self, us_stp):
        return 1/(us_stp*1e-6)

    def stp_s_to_us_stp(self, stp_s):
        return 1e6/stp_s

    def us_stp_to_rev_s(self, us_stp):
        return self.us_stp_to_stp_s(us_stp)/self.stp_per_rev

    def rev_s_to_us_stp(self, rev_s):
        return 1e6/(self.thread_pitch*self.stp_per_rev)

#--------------------------------- Set & Get -----------------------------------

    def set_speed(self, spd, unit):
        spd = float(spd)
        if unit == "us/step":
            self.send_cmd("V", str(spd))
        elif unit == "step/s":
            self.send_cmd("V", str(self.stp_s_to_us_stp(spd)))
        elif unit == "mm/s":
            self.send_cmd("V", str(self.mm_s_to_us_stp(spd)))
        elif unit == "rev/s":
            self.send_cmd("V", str(self.rev_s_to_us_stp(spd)))

    def move_dis(self, dis, unit):
        dis = float(dis)
        if unit == "steps":
            self.sent_pos_stp = dis
            self.sent_pos_mm = self.stp_to_mm(self.sent_pos_stp)
            self.send_cmd("S", abs(self.sent_pos_stp))
        elif unit == "mm":
            self.sent_pos_mm = dis
            stp = self.mm_to_stp(dis)
            self.sent_pos_stp = stp
            self.send_cmd("S", abs(self.sent_pos_stp))
        elif unit == "rev":
            self.sent_pos_stp = rev_to_stp(dis)
            self.sent_pos_mm = self.stp_to_mm(self.sent_pos_stp)
            self.send_cmd("S", abs(self.sent_pos_stp))

    def move_pos(self, pos, unit):
        pos = float(pos)
        if unit == "steps":
            pos_stp = pos
        elif unit == "mm":
            pos_stp = self.mm_to_stp(pos)
        elif unit == "rev":
            pos_stp = self.rev_to_stp(pos)

        if self.abs_pos_stp != pos_stp:
            dis = abs(self.abs_pos_stp - pos_stp)
            if pos_stp < self.abs_pos_stp:
                self.set_dir(str(-1))
            else:
                self.set_dir(str(1))
            self.move_dis(dis, "steps")


    def set_dir(self, direction):
        self.send_cmd("D", str(direction))


    def set_event_code(self, code):
        self.send_cmd("E", str(code))

    def set_abs_pos_stp(self, val):
        self.send_cmd("A", str(val))

    def ping_arduino(self):
        self.send_cmd("W")


    def get_velocity(self):
        return


    def get_direction(self):
        return


    def get_current_position(self):
        return


    def calibrate_sys(self):
        if self.event_code == 0:
            self.set_event_code(4)
            self.set_dir(-1)
            self.move_dis(self.stage_length, "mm")
        elif self.event_code == 2:
            self.set_event_code(4)
            self.set_dir(1)
            self.count_range_start = self.abs_pos_stp
            self.move_dis(self.stage_length, "mm")
        elif self.event_code == 1 and self.count_range_start != None:
            full_ls_range = abs(self.abs_pos_stp - self.count_range_start)
            half_ls_range = abs(full_ls_range)/2
            print()
            print("full_ls_range", full_ls_range)
            print("half_ls_range", half_ls_range)
            print()
            self.set_dir(-1)
            self.count_range_start = None
            new_abs_pos = half_ls_range
            self.set_abs_pos_stp(new_abs_pos)
            self.set_event_code(0)
            dis = abs(new_abs_pos - 0)
            self.move_dis(dis, "steps")
        return


    def reset_sys(self):
        self.set_event_code(0)
        time.sleep(2)
        self.send_cmd("R")

    def discrete_meas(self, n, delta_x_mm, pause_t):
        self.send_cmd("W")
        data_dict = self.serial_read()
        move_t = delta_x_mm/data_dict["spd_mm/s"]
        delta_t = move_t + pause_t

        for i in range(n):
            self.move_dis(delta_x_mm, "mm")
            time.sleep(delta_t)




#--------------------------------- if __main__ ---------------------------------
if __name__ == "__main__":
    ls = LinearStage(json_path="linear_stage.json")
    ls.read_json()
    ports = (list(list_ports.comports()))
    port_name = list(map(lambda p : p["ttyACM" in p.device], ports))[0]
    serial_port = "/dev/" + port_name
    ls.start_serial(serial_port)
    time.sleep(2)

    #ls.send_cmd("S", str(5000))
    #ls.send_cmd("W")
    #print(ls.serial_read())
    ls.discrete_meas(3, 40, 5)
