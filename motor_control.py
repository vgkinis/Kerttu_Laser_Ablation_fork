import serial
import time

# Initialize serial
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=.1)
time.sleep(2) #give the connection a second to settle

usr_steps_nr = input("Enter the distance in mm (press x to exit): ")
ser.write(str.encode(usr_steps_nr))

while True:
	line = None
	while ser.in_waiting > 0:
		line = ser.readline()
		#line = int(line)
		print(line)
		print()
		time.sleep(1)
	if line is not None:
		usr_steps_nr = input("Enter the distance in mm (press x to exit): ")
		ser.write(str.encode(usr_steps_nr))
		if usr_steps_nr == "x":
			break
