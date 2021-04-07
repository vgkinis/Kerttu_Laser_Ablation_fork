
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


    def send_cmd(self):
        return


#--------------------------------- if __main__ ---------------------------------
if __name__ == "__main__":
    laser = Laser()
    if "COM" in port_names[0]:
        serial_ports = port_names
    else:
        serial_ports = list(map(lambda p : "/dev/" + p, port_names))

    laser.start_serial(serial_ports[0])
    time.sleep(2)

    command = 'h'
    laser.ser.write(str.encode(command + "\n"))
    while True:
        if laser.ser.in_waiting > 0:
            line = ser.readline()
            data = line.decode("utf-8")
            print(data)
