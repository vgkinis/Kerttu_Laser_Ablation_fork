import serial
import time

ser = serial.Serial('/dev/ttyACM0', 9600, timeout=.1)
time.sleep(2) #give the connection a second to settle

while True:
	usr_steps_nr = input("Enter the number of steps (press x to exit): ")
	ser.write(str.encode(usr_steps_nr))
	if ser.in_waiting > 0:
		line = ser.readline()
		time.sleep(1)
	if usr_steps_nr == "x":
		break
