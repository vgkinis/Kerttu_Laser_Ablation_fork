import serial

RS232 = serial.Serial('/dev/ttyUSB1',9600, 8, 'N', 1)

def ExecCmd(RS232, command):
	# Send the command with the appropriate <CR> terminator...
	RS232.write(str.encode(command + chr(13)))
	#and collect the response...
	buf = []
	while True:
		if RS232.in_waiting > 0:
			# reading one byte at a time until <CR> is read
			c = RS232.read()
			if c == chr(13):
				break
			else:
				out_hex = ['{:02X}'.format(b) for b in c][0]
				out_dec = int(out_hex, 16)
				# build the response (w/o <CR>)
				buf.append(out_dec)
			#Check if there is an error (first 4 chars = "ERR")...
			print(buf)
			print()
			print()
			print()
	if buf[:4] == "ERR:":
		raise Exception(buf)
	else:
		#No error - return the response string (w/o <CR>)...
		return buf

command = '_Instr_GetStatus'

print(ExecCmd(RS232, command))
