
import numpy as np
import serial
import os
import time
import json
from serial.tools import list_ports


class Laser():
    """

    """

#--------------------------------- Initializing --------------------------------
    def __init__(self):
        self.rep_rates_kHz = {0:50, 1:100, 2:200, 3:299.625, 4:400, 5:500,
                                6:597.015, 7:707.965, 8:800, 9:898.876, 10:1000}
        self.epoch_time = -999
        self.data_dict = {"rep_rate_kHz": -999,
                        "energy_nJ": -999,
                        "energy_uJ": -999,
                        "status_laser_on_enabled": -999,
                        "status_laser_on_disabled": -999,
                        "status_standby": -999,
                        "status_setup": -999,
                        "status_listen": -999,
                        "status_warning": -999,
                        "status_error": -999,
                        "status_power": -999,
                        "epoch_time": self.epoch_time,
                        }
        self.ping_order_nr = 0
        return



#------------------------------- Serial functions ------------------------------
    def start_serial(self, serial_name):
        try:
            self.ser = serial.Serial(serial_name, 38400, timeout=.1)
            print("Connection is established")
        except Exception as e:
            print(e)
            print("Could not open serial")
        return


    def close_serial(self):
        if self.ser.is_open:
            self.ser.close()
        return

    def serial_read(self):
        while self.ser.in_waiting > 0:
            line = self.ser.readline()
            data = line.decode("utf-8").strip("\n")
            if "Frequency index parameter: " in data:
                rep_rate_nr = int(data.split(": ")[1])
                rep_rate = self.rep_rates_kHz[rep_rate_nr]
                self.data_dict["rep_rate_kHz"] = rep_rate
                self.data_dict["epoch_time"] = self.epoch_time
                #return True
            elif "nJ" in data:
                energy_nJ = float(data.split("nJ")[0].strip(" "))
                energy_uJ = energy_nJ/1000.0
                self.data_dict["energy_nJ"] = energy_nJ
                self.data_dict["energy_uJ"] = energy_uJ
                self.data_dict["epoch_time"] = self.epoch_time
                #return True
            elif "ly_oxp2_dev_status " in data:
                status_dec = int(data.split(" ")[1])
                status_bin = np.binary_repr(status_dec, width=8)
                self.data_dict["status_laser_on_enabled"] = int(status_bin[0])
                self.data_dict["status_laser_on_disabled"] = int(status_bin[1])
                self.data_dict["status_standby"] = int(status_bin[2])
                self.data_dict["status_setup"] = int(status_bin[3])
                self.data_dict["status_listen"] = int(status_bin[4])
                self.data_dict["status_warning"] = int(status_bin[5])
                self.data_dict["status_error"] = int(status_bin[6])
                self.data_dict["status_power"] = int(status_bin[7])
                self.data_dict["epoch_time"] = self.epoch_time
                #return True
        #return False #self.data_dict

    def send_cmd(self, command, print_cmd=True):
        serial_cmd = command + "\n"
        try:
            if print_cmd:
                print("Sending laser command: ", command)
            self.ser.write(str.encode(serial_cmd))
        except Exception as e:
            print(e)
            print("Command %s not sent. Could not open serial" %serial_cmd)
        return

    def ping_laser_module(self):
        if self.ser.in_waiting == 0:
            if self.ping_order_nr == 5:
                self.get_repetition_rate()
                self.ping_order_nr = 0
            self.get_measured_pulse_energy()
            self.get_status()
            self.ping_order_nr += 1

            self.epoch_time = time.time()

#------------------------------- Commands  .......------------------------------
    def go_to_standby(self):
        self.send_cmd('ly_oxp2_standby')

    def go_to_listen(self):
        self.send_cmd('ly_oxp2_listen')

    def enable_laser(self):
        self.send_cmd('ly_oxp2_enabled')

    def enable_AOM_laser(self):
        self.send_cmd('ly_oxp2_output_enable')

    def disable_AOM_laser(self):
        self.send_cmd('ly_oxp2_output_disable')


    def set_pulse_energy(self, energy, unit):
        if unit == "uJ":
            energy_nJ = energy * 1000
            command = 'ly_oxp2_power=' + str(energy_nJ)
            self.send_cmd(command)
        elif unit == "nJ":
            energy_nJ = energy
            command = 'ly_oxp2_power=' + str(energy_nJ)
            self.send_cmd(command)

    def set_repetition_rate(self, freq_nr):
        command = 'e_freq=' + str(freq_nr)
        self.send_cmd(command)

    def get_measured_pulse_energy(self):
        self.send_cmd('e_mlp?', False)

    def get_repetition_rate(self):
        self.send_cmd('e_freq?', False)

    def get_status(self):
        self.send_cmd('ly_oxp2_dev_status?', False)


#--------------------------------- if __main__ ---------------------------------
if __name__ == "__main__":
    laser = Laser()
    ports = (list(list_ports.comports()))
    port_names = list(map(lambda p : p.device, ports))

    laser.start_serial(port_names[0])
    time.sleep(2)

    laser.send_cmd('h?')
    laser.send_cmd('e_freq?')
    while True:
        if laser.ser.in_waiting > 0:
            line = laser.ser.readline()
            data = line.decode("utf-8")
            print(line)
