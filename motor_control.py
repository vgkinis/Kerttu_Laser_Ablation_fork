import serial
import time

# Initialize serial
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=.1)
time.sleep(2) #give the connection a second to settle
real_pos = None
last_abs_pos = 0

usr_pos_str = input("Enter the distance in mm (press x to exit): ")
ser.write(str.encode(usr_pos_str))
usr_pos = int(usr_pos_str)

while True:
	if ser.in_waiting > 0:
		abs_pos = ser.readline()
		abs_pos = int(abs_pos)
		print("Position is ", abs_pos)
	if (abs_pos-last_abs_pos) == usr_pos:
		usr_pos_str = input("Enter the distance in mm (press x to exit): ")
		ser.write(str.encode(usr_pos_str))
		usr_pos = int(usr_pos_str)
		last_abs_pos = abs_pos
		ser.flushInput()
		if usr_pos_str == "x":
			break
