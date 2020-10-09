import serial
import time
import os
import csv
import pytz
import os
import datetime

# Open serial communication
ser = serial.Serial('/dev/ttyACM0', 250000, timeout=.1)
#time.sleep(2)

operating_time = 4 # in minutes

stage = int(input("Enter the length of the stage 150 or 1200 (or 0 for no stage): "))
vref = input("Enter the value of Vref: ").replace(".","")

# Position variables
abs_pos = 0
last_abs_pos = 0
if stage == 150:
	pos = -25
else:
	pos = -150
dir_change = True

# Result files
timezone = "Europe/Copenhagen"
dir_result = os.path.join(os.getcwd(),"Results")
time_stamp = datetime.datetime.now(pytz.timezone(timezone))
filename = os.path.join(dir_result,"run_test_" + str(time_stamp) + "_V" + vref + "_s" + str(stage) + ".csv")

# Start keeping the time
start_t = time.time()
new_t = time.time()

# Send the first position
ser.write(str.encode(str(pos)))

while (new_t - start_t)/60 < operating_time:
	new_t = time.time()
	with open(filename,"a+") as f:
		writer = csv.writer(f, delimiter=",")
		try:
			if ser.in_waiting > 0:
				line = ser.readline()
				data = line.decode("utf-8")
				data = data.split(";")
				if len(data) == 3:
					loop_time, abs_pos, speed = float(data[0])*10**(-3), float(data[1]), float(data[2])
					abs_pos = int(abs_pos)
					writer.writerow(["{:11.4f}".format(loop_time), "{:4.0f}".format(abs_pos), "{:7.1f}".format(speed)])
					print("Loop_time", "{:11.4f}".format(loop_time), "Absolute position", "{:4.0}".format(abs_pos), "speed", "{:7.1f}".format(speed), "us")

			if (abs_pos-last_abs_pos) == pos:
				if dir_change == False:
					dir_change = True
				else:
					pos *= -1
					dir_change = False

				ser.write(str.encode(str(pos)))
				last_abs_pos = abs_pos
				ser.flushInput()

				print("Time passed in minutes: ", (new_t - start_t)/60)
				print("Absolute position", abs_pos, "reached.")
				print()
		except:
			continue
