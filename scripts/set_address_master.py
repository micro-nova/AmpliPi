# Writing Addresses to Preamp Boards
import serial
ser = serial.Serial ("/dev/serial0")
ser.baudrate = 9600

addr = 0x41, 0x10, 0x0D, 0x0A

ser.write(addr)
ser.close()
