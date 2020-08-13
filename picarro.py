import serial

ser = serial.Serial(
		port = '/dev/ttyACM0',
		baudrate = 9600,
		parity = serial.PARITY_NONE,
		stopbits = serial.STOPBITS_ONE,
		bytesize = serial.EIGHTBITS
)

def ExecCmd(command):
	#send the command with the appropriate <CR> terminator...
	RS232.write(command + chr(13))
	#and collect the response...
	buf = ""
	while True:
		# reading one byte at a time until <CR> is read
		c = RS232.Read(1)
		if c == chr(13):
			break
		else:
			# build the response (w/o <CR>)
			buf = buf + c
		#Check if there is an error (first 4 chars = "ERR")...
		if buf[:4] == "ERR:":
			raise Exception(buf)
		else:
			#No error - return the response string (w/o <CR>)...
			return buf

command = list(bytes(b'_Meas_GetConc'))
command.append(13)

print(ExecCmd(13))
