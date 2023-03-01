#!/usr/bin/env python3

# This program reports voltage, current, and temperature information

from smbus2 import SMBus
from time import sleep

RPI_I2CBUS=1	# Using Raspberry Pi I2C_1
I2C_ADDR=0x51	# I2C address 0x51

try:
	# Create i2c object
	i2c=SMBus(RPI_I2CBUS)

	# Dummy write command to flush out unfinished I2C traffic
	#i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x2c, 0xb1, 0x04, 0x10])

	while True:
		#print("#########################################################################")
		# Read voltage addr 0x20, LSB=80mV
		#voltage = SMBus(RPI_I2CBUS).read_byte_data(I2C_ADDR, 0x20) * 80
		# Read current addr 0x21, LSB=24mA
		#current = SMBus(RPI_I2CBUS).read_byte_data(I2C_ADDR, 0x21) * 24 
		# Read temperature addr 0x22
		temperature = i2c.read_byte_data(I2C_ADDR, 0x22)
		#print("voltage=%dmV\tcurrent=%dmA\ttemperature=%dC" %(voltage, current, temperature))
		print("temperature=%dC" %(temperature))
		sleep(0.5)

	i2c.close()
    
except KeyboardInterrupt:
	# If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
	print("Break detected! Shut down AP33772")
	if i2c:
		# Disable ap33772
		i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x00, 0x00, 0x00, 0x00])
		i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x00, 0x00, 0x00, 0x00])
		i2c.close()
