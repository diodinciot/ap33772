#!/usr/bin/env python3

from smbus2 import SMBus, i2c_msg
from time import sleep
RPI_I2CBUS=1	# Using Raspberry Pi I2C_1
I2C_ADDR=0x51	# I2C address 0x51
PDO_ADDR=0x00	# PDO address range 0x00 ~ 0x1b, Starting at 0x00, max is 7 PDOs
ValidPDOCnt=0	# reset Valid PDO count

try:
	# Create i2c object
	i2c=SMBus(RPI_I2CBUS)
	# Dummy write command to flush out unfinished I2C traffic
	i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x2c, 0xb1, 0x04, 0x10])
	# search through 7 PDOs
	for i in range(7):
		# Read PDO info with 4-byte long
		B0=i2c.read_byte_data(I2C_ADDR, 4*i)
		B1=i2c.read_byte_data(I2C_ADDR, 4*i+1)
		B2=i2c.read_byte_data(I2C_ADDR, 4*i+2)
		B3=i2c.read_byte_data(I2C_ADDR, 4*i+3)
		PDO=B3<<24 | B2<<16 | B1<<8 | B0
		#print("PDO=0x%.8x 0x%.2x 0x%.2x 0x%.2x 0x%.2x" %(PDO, B3, B2, B1, B0))

		IS_VALID_PDO=(PDO != 0x00000000)
		if IS_VALID_PDO:
			#print("PDO" + str(i+1))
			#print("PDO ID:%d  0x%.8x" %(i, PDO))
			ValidPDOCnt+=1

			IS_APDO=((PDO & 0xc0000000)==0xc0000000)
			if IS_APDO:
				print("PDO ID:%d\nPDO=0x%.8x is a APDO" %(i+1, PDO))
				MaxCurr=((PDO&(0x3f<<0))>>0)*50		# bit 6..0, 1LSB is 50mA
				MinVolt=((PDO&(0xff<<8))>>8)*100	# bit 15..8, 1LSB is 100mV
				MaxVolt=((PDO&(0xff<<17))>>17)*100	# bit 24..17, 1LSB is 100mV
				print("MinVoltage=%dmV\nMaxVoltage=%dmV\nMax Current=%dmA\n" %(MinVolt, MaxVolt, MaxCurr))
			else:
				print("PDO ID:%d\nPDO=0x%.8x is a Fixed PDO" %(i+1, PDO))
				MaxCurr=((PDO&(0x3ff<<0))>>0)*10	# bit 9..0, 1LSB is 10mA
				Volt=((PDO&(0x3ff<<10))>>10)*50	# bit 19..10, 1LSB is 50mV
				print("Voltage=%dmV\nMax Current=%dmA\n" %(Volt, MaxCurr))

	print("Total %d valid PDOs are detected!" %(ValidPDOCnt))
	i2c.close()
    
except KeyboardInterrupt:
	# If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
	print("Break detected!")
	if i2c:
		i2c.close()
