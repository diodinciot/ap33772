#!/usr/bin/env python3

from smbus2 import SMBus, i2c_msg
from time import sleep

RPI_I2CBUS=1	# Using Raspberry Pi I2C_1
I2C_ADDR=0x51	# I2C address 0x51
PDO_ADDR=0x00	# PDO address range 0x00 ~ 0x1b, Starting at 0x00, max is 7 PDOs
ValidPDOCnt=0	# reset Valid PDO count

# Create i2c object
i2c=SMBus(RPI_I2CBUS)

try:
	# Create i2c object
	i2c=SMBus(RPI_I2CBUS)

	# Dummy write command to flush out unfinished I2C traffic
	i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x2c, 0xb1, 0x04, 0x10])

	#print("#########################################################################")
	# Read voltage addr 0x20, LSB=80mV
	voltage = SMBus(RPI_I2CBUS).read_byte_data(I2C_ADDR, 0x20) * 80
	# Read current addr 0x21, LSB=24mA
	current = SMBus(RPI_I2CBUS).read_byte_data(I2C_ADDR, 0x21) * 24 
	# Read temperature addr 0x22
	temperature = i2c.read_byte_data(I2C_ADDR, 0x22)
	print("voltage=%dmV\tcurrent=%dmA\ttemperature=%dC" %(voltage, current, temperature))
	i2c.close()
    
except KeyboardInterrupt:
	# If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
	print("Break detected!")
	i2c.close()
