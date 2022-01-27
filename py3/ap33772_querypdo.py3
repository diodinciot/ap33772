#!/usr/bin/env python3

# This program reports all PDO information

from smbus2 import SMBus
from time import sleep

RPI_I2CBUS=1	# Using Raspberry Pi I2C_1
I2C_ADDR=0x51	# I2C address 0x51

class Pdo:
	def __init__(self, word=0x00000000, pdotype="FPDO", id=0):
		self.word=word		# PDO's word contents
		self.pdotype=pdotype	# "FPDO" or "APDO"
		self.id=id		# PDO id/position
		if self.pdotype != "APDO":	# FPDO
			self.Volt=5000
			self.MaxCurr=3000
		else:				# APDO
			self.MaxVolt=21000
			self.MinVolt=3300
			self.MaxCurr=3000

	def display(self):
		print("PDO%d: 0x%.8x %s" %(self.id, self.word, self.pdotype))

class Rdo:
	def __init__(self, word=0x00000000, pdotype="FPDO", id=0):
		self.word=word		# RDO's word contents
		self.pdotype=pdotype	# "FPDO" or "APDO"
		self.id=id		# RDO id/position
		if self.pdotype != "APDO":	# FPDO
			self.RpoOpCurr=3000
			self.RpoMaxOpCurr=3000
		else:				# APDO
			self.RpoOpVolt=5000
			self.RpoOpCurr=3000

	def display(self):
		print("RDO%d: 0x%.8x %s" %(self.id, self.word, self.pdotype))


try:
	# Create i2c object
	i2c=SMBus(RPI_I2CBUS)
	# Dummy write command to flush out unfinished I2C traffic
	#i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x2c, 0xb1, 0x04, 0x10])
	# Read all 28-Byte PDO information
	pdo28b=i2c.read_i2c_block_data(I2C_ADDR, 0x00, 28)

	# Build PDO objects based on the first 28-byte data
	pdolist=list()
	ValidPDOCnt=0	# reset Valid PDO count
	for i in range(0, len(pdo28b), 4):
		p = Pdo()
		pdolist.append(p)
		p.id = int(i/4) + 1
		p.word = 0
		for j in range(4):
			p.word=p.word+(pdo28b[i+j]<<(8*j))	

		# Process only valid PDO which has contents other than 0x00000000
		IS_VALID_PDO=(p.word != 0x00000000)  
		if IS_VALID_PDO:
			#print("PDO ID:%d  0x%.8x" %(i, p))
			ValidPDOCnt+=1

			IS_APDO=((p.word & 0xc0000000)==0xc0000000) 	# APDO bit 31..30 is 0b11
			if IS_APDO:
				print("PDO ID:%d\nPDO=0x%.8x is a APDO" %(i+1, p.word))
				p.pdotype="APDO"
				p.MaxCurr=((p.word&(0x3f<<0))>>0)*50		# bit 6..0, 1LSB is 50mA
				p.MinVolt=((p.word&(0xff<<8))>>8)*100		# bit 15..8, 1LSB is 100mV
				p.MaxVolt=((p.word&(0xff<<17))>>17)*100	# bit 24..17, 1LSB is 100mV
				print("MinVoltage=%dmV\nMaxVoltage=%dmV\nMax Current=%dmA\n" %(p.MinVolt, p.MaxVolt, p.MaxCurr))
			else:
				print("PDO ID:%d\nPDO=0x%.8x is a Fixed PDO" %(i+1, p.word))
				p.pdotype="FPDO"
				p.MaxCurr=((p.word&(0x3ff<<0))>>0)*10	# bit 9..0, 1LSB is 10mA
				p.Volt=((p.word&(0x3ff<<10))>>10)*50	# bit 19..10, 1LSB is 50mV
				print("Voltage=%dmV\nMax Current=%dmA\n" %(p.Volt, p.MaxCurr))

	print("Total %d valid PDOs are detected!" %(ValidPDOCnt))

	# Delete unused PDOs
	for i in range(ValidPDOCnt, 7):
		pdolist.pop(-1)

	# Print all PDO out
	print("PDO List:")
	for p in pdolist:
		p.display()

	# The following command will never be reached due to "while True" command! Actually object closure is done in except condition.
	i2c.close()	
    
except KeyboardInterrupt:
	# If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
	print("Break detected!")
	if i2c:
		i2c.close()
