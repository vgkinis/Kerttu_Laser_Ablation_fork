
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
        return



#------------------------------- Serial functions ------------------------------
    def start_serial(self, serial_name):
        try:
            self.ser = serial.Serial(port_name, 38400, timeout=.1)
            print("Connection is established")
        except:
            print("Could not open serial")
        return


    def close_serial(self):
        if self.ser.is_open:
            self.ser.close()
        return

    def serial_read(self):
        return

    def send_cmd(self, command):
        serial_cmd = command + "\n"
        try:
            self.ser.write(str.encode(serial_cmd))
        except:
            print("Command %s not sent. Could not open serial" %serial_cmd)
        return

#------------------------------- Commands  .......------------------------------
    def go_to_standby(self):
        self.send_cmd('ly_oxp2_standby')

    def go_to_listen(self):
        self.send_cmd('ly_oxp2_listen')

    def go_to_laser_on(self):
        self.send_cmd('ly_oxp2_output_enable')

    def set_pulse_energy(self, energy, unit):
        if unit == "uJ":
            energy_nJ = energy * 1000
            command = 'ly_oxp2_power=' + str(energy_nJ)
            self.send_cmd(command)
        elif unit == "nJ":
            energy_nJ = energy_nJ
            command = 'ly_oxp2_power=' + str(energy_nJ)
            self.send_cmd(command)

    def get_measured_pulse_energy(self):
        self.send_cmd('e_mlp?')

    def set_repetition_rate(self, freq):
        rep_rates_kHz = {0:50, 1:100, 2:200, 3:299.625, 4:400, 5:500,
                                6:597.015, 7:707.965, 8:800, 9:898.876, 10:1000}

        command = list(rep_rates_kHz.keys())[list(rep_rates_kHz.values()).index(freq)]
        self.send_cmd(command)


#--------------------------------- if __main__ ---------------------------------
if __name__ == "__main__":
    laser = Laser()
    if "COM" in port_names[0]:
        serial_ports = port_names
    else:
        serial_ports = list(map(lambda p : "/dev/" + p, port_names))

    laser.start_serial(serial_ports[0])
    time.sleep(2)

    laser.send_cmd('h')
    while True:
        if laser.ser.in_waiting > 0:
            line = ser.readline()
            data = line.decode("utf-8")
            print(data)
