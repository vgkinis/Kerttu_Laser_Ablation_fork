import linear_stage
import time


ls = linear_stage.LinearStage(json_path="linear_stage.json")
ls.read_json()
ports = (list(list_ports.comports()))
port_name = list(map(lambda p : p["ttyACM" in p.device], ports))[0]
serial_port = "/dev/" + port_name
ls.start_serial(serial_port)

operating_time = 1 # in minutes

# Result files
motor_name = "iHSS57-36-10"
timezone = "Europe/Copenhagen"
dir_result = os.path.join(os.getcwd(),"Results")
time_stamp = datetime.datetime.now(pytz.timezone(timezone))
filename = os.path.join(dir_result,"run_test_" + str(time_stamp) + "_" + motor_name + ".csv")

# Start keeping the time
start_t = time.time()
new_t = time.time()

while (new_t - start_t)/60 < operating_time:
	new_t = time.time()
	with open(filename,"a+") as f:
		writer = csv.writer(f, delimiter=",")
		try:
			if ls.ser.in_waiting > 0:
				line = ser.readline()
				data = line.decode("utf-8")
				data = data.split(";")
				if len(data) == 3:
                    loop_time, abs_pos_stp, velocity_delay_micros = float(data[0])*10**(-3), float(data[1]), float(data[2])
                    abs_pos_mm = ls.stp_to_mm(abs_pos_stp)
                    print("Loop_time", "{:11.4f}".format(loop_time), "Absolute position stp", "{:6.0f}".format(abs_pos_stp), "Absolute position mm", "{:4.0f}".format(abs_pos_mm), "Velocity delay", "{:7.1f}".format(velocity_delay_micros), "us")
                    writer.writerow(["{:11.4f}".format(loop_time), "{:6.0f}".format(abs_pos_stp), "{:4.0f}".format(abs_pos_mm), "{:7.1f}".format(velocity_delay_micros)])
