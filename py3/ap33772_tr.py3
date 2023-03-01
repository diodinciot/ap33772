#!/usr/bin/env python3

# This program changes TR25, TR50, TR75, and TR100 and print the new values out.

from smbus2 import SMBus
from time import sleep

RPI_I2CBUS=1	# Using Raspberry Pi I2C_1
I2C_ADDR=0x51	# I2C address 0x51

try:
	# Create i2c object
	i2c=SMBus(RPI_I2CBUS)

	# Write a reset to start from scratch
	#i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x00, 0x00, 0x00, 0x00])

	#print("#########################################################################")
	# Read TRs
	TR25 = SMBus(RPI_I2CBUS).read_word_data(I2C_ADDR, 0x28)
	TR50 = SMBus(RPI_I2CBUS).read_word_data(I2C_ADDR, 0x2a)
	TR75 = SMBus(RPI_I2CBUS).read_word_data(I2C_ADDR, 0x2c)
	TR100 = SMBus(RPI_I2CBUS).read_word_data(I2C_ADDR, 0x2e)
	print("Original TR25=%d\tTR50=%d\tTR75=%d\tTR100=%d" %(TR25, TR50, TR75, TR100))
	# Write TRs
	SMBus(RPI_I2CBUS).write_word_data(I2C_ADDR, 0x28, 0x1a90<<1)
	SMBus(RPI_I2CBUS).write_word_data(I2C_ADDR, 0x2a, 0x0ad6<<1)
	SMBus(RPI_I2CBUS).write_word_data(I2C_ADDR, 0x2c, 0x0507<<1)
	SMBus(RPI_I2CBUS).write_word_data(I2C_ADDR, 0x2e, 0x0296<<1)
	print("Finished writing")
	# Read TRs
	TR25 = SMBus(RPI_I2CBUS).read_word_data(I2C_ADDR, 0x28)
	TR50 = SMBus(RPI_I2CBUS).read_word_data(I2C_ADDR, 0x2a)
	TR75 = SMBus(RPI_I2CBUS).read_word_data(I2C_ADDR, 0x2c)
	TR100 = SMBus(RPI_I2CBUS).read_word_data(I2C_ADDR, 0x2e)
	print("New TR25=%d\tTR50=%d\tTR75=%d\tTR100=%d" %(TR25, TR50, TR75, TR100))
	i2c.close()
    
except KeyboardInterrupt:
	# If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
	print("Break detected! Shut down AP33772")
	if i2c:
		# Disable ap33772
		i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x00, 0x00, 0x00, 0x00])
		i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x00, 0x00, 0x00, 0x00])
		i2c.close()
