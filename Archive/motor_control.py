import serial
import time

# Initialize serial
ser = serial.Serial('/dev/ttyACM0', 250000, timeout=.1)
time.sleep(2) #give the connection a second to settle
abs_pos = 0
last_abs_pos = 0

usr_pos_str = input("Enter the distance in mm (press x to exit): ")
ser.write(str.encode(usr_pos_str))
usr_pos = int(usr_pos_str)

while True:
	if ser.in_waiting > 0:
		line = ser.readline()
		data = line.decode("utf-8")
		data = data.split(";")
		if len(data) == 3:
			loop_time, abs_pos, speed = float(data[0])*10**(-3), float(data[1]), float(data[2])
			abs_pos = int(abs_pos)
			print("Loop_time", "{:11.4f}".format(loop_time), "Absolute position", "{:4.0f}".format(abs_pos), "speed", "{:7.1f}".format(speed), "us")
	if (abs_pos-last_abs_pos) == usr_pos:
		usr_pos_str = input("Enter the distance in mm (press x to exit): ")
		if usr_pos_str == "x":
			break
		ser.write(str.encode(usr_pos_str))
		usr_pos = int(usr_pos_str)
		last_abs_pos = abs_pos
		ser.flushInput()
