#!/usr/bin/env python3

from smbus2 import SMBus, i2c_msg
from time import sleep

RPI_I2CBUS=1	# Using Raspberry Pi I2C_1
I2C_ADDR=0x51	# I2C address 0x51
PDO_ADDR=0x00	# PDO address range 0x00 ~ 0x1b, Starting at 0x00, max is 7 PDOs
ValidPDOCnt=0	# reset Valid PDO count

class Pdo:
	def __init__(self, word=0x00000000, pdotype="FPDO", id=0):
		self.word=word		# PDO's word contents
		self.pdotype=pdotype	# "FPDO" or "APDO"
		self.id=id		# PDO id/position
		if self.pdotype != "APDO":	# FPDO
			self.Volt=3000
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




cmdcnt=0
rejcnt=0

pdolist=[Pdo(), Pdo(), Pdo(), Pdo(), Pdo(), Pdo(), Pdo()]
rdolist=[Rdo(), Rdo(), Rdo(), Rdo(), Rdo(), Rdo(), Rdo()]

try:
	# Create i2c object
	i2c=SMBus(RPI_I2CBUS)
	# Dummy write command to flush out unfinished I2C traffic
	i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x2c, 0xb1, 0x04, 0x10])
	# search through 7 PDOs
	print("#########################################################################")
	print("Start querying PDOs")
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
			pdolist[i].word=PDO
			pdolist[i].id=(i+1)

			IS_FPDO=((PDO & 0xc0000000)!=0xc0000000)
			if IS_FPDO:
				print("PDO ID:%d\nPDO=0x%.8x is a Fixed PDO" %(i+1, PDO))
				MaxCurr=((PDO&(0x3ff<<0))>>0)*10	# bit 9..0, 1LSB is 10mA
				Volt=((PDO&(0x3ff<<10))>>10)*50	# bit 19..10, 1LSB is 50mV
				print("Voltage=%dmV\nMax Current=%dmA\n" %(Volt, MaxCurr))
				pdolist[i].pdotype="FPDO"
				pdolist[i].MaxCurr=MaxCurr
				pdolist[i].Volt=Volt

			else:
				print("PDO ID:%d\nPDO=0x%.8x is a APDO" %(i+1, PDO))
				MaxCurr=((PDO&(0x3f<<0))>>0)*50		# bit 6..0, 1LSB is 50mA
				MinVolt=((PDO&(0xff<<8))>>8)*100	# bit 15..8, 1LSB is 100mV
				MaxVolt=((PDO&(0xff<<17))>>17)*100	# bit 24..17, 1LSB is 100mV
				print("Min Voltage=%dmV\nMax Voltage=%dmV\nMax Current=%dmA\n" %(MinVolt, MaxVolt, MaxCurr))
				pdolist[i].pdotype="APDO"
				pdolist[i].MaxCurr=MaxCurr
				pdolist[i].MinVolt=MinVolt
				pdolist[i].MaxVolt=MaxVolt
				
	# Delete unused PDOs
	for i in range(ValidPDOCnt, 7):
		pdolist.pop(-1)


	print("Total %d valid PDOs are detected!" %(ValidPDOCnt))

	# Print all PDO out
	print("PDO List:")
	for p in pdolist:
		p.display()

	#print("pdolist:" , pdolist)


	# Preparing RDO for later 
	for p in pdolist:
		if p.pdotype == "FPDO":	# This is Fixed PDO
			rdolist[p.id-1].id=p.id
			rdolist[p.id-1].pdotype=p.pdotype
			rdolist[p.id-1].RpoOpCurr=p.MaxCurr
			rdolist[p.id-1].RpoMaxOpCurr=p.MaxCurr
			# Set position value bit30..28 
			# Set Operating Current in 10mA units, bit19..10
			# Set Max Operating Current in 10mA units, bit9..0
			rdolist[p.id-1].word = ((p.id & 0x7) << 28) | (int(rdolist[p.id-1].RpoOpCurr/10)<<10 ) | (int(rdolist[p.id-1].RpoMaxOpCurr/10)<<0)
		else:			# This is APDO
			rdolist[p.id-1].id=p.id
			rdolist[p.id-1].pdotype=p.pdotype
			rdolist[p.id-1].RpoOpVolt=p.MaxVolt
			rdolist[p.id-1].RpoOpCurr=p.MaxCurr
			# Set position value bit30..28 
			# Set Output Voltage in 20mV units, bit19..9
                        # Set Operating Current in 50mA units, bit6..0
			rdolist[p.id-1].word = ((p.id & 0x7) << 28) | (int(rdolist[p.id-1].RpoOpVolt/20)<<9 ) | (int(rdolist[p.id-1].RpoMaxOpCurr/50)<<0)


	# Delete unused RDOs
	for i in range(ValidPDOCnt, 7):
		rdolist.pop(-1)

	# Print all RDO out
	print("RDO List:")
	for p in rdolist:
		p.display()

	#print("rdolist:" , rdolist)

	print("#########################################################################")
	print("Start requesting PDOs")
	print("")

	# RDO submission
	while True:
		for i in list(range(ValidPDOCnt-1))+list(reversed(range(1, ValidPDOCnt))):
			cmdcnt=cmdcnt+1
			# Request PDO from 0x30~0x33
			i2c.write_i2c_block_data(I2C_ADDR, 0x30, [(rdolist[i].word>>0)&0xff, (rdolist[i].word>>8)&0xff, (rdolist[i].word>>16)&0xff, (rdolist[i].word>>24)&0xff])
			sleep(0.5)
			status = i2c.read_byte_data(I2C_ADDR, 0x1d)
			if (status & 0x02) != 0x02:
				rejcnt=rejcnt+1
			voltage = i2c.read_byte_data(I2C_ADDR, 0x20) * 80
			current = i2c.read_byte_data(I2C_ADDR, 0x21) * 24
			temperature = i2c.read_byte_data(I2C_ADDR, 0x22)
			print("PDO%d:\tTotal:%-3d\tstatus:0x%.2x\tRejects=%d\tV=%dmV\tI=%dmA\tT=%dC" %((i+1), cmdcnt, status, rejcnt, voltage, current, temperature))

			#sleep(0.3)

	# The following command will never be reached due to "while True" command! Actually object closure is done in except condition.
	i2c.close()	
    
except KeyboardInterrupt:
	# If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
	print("Break detected!")
	if i2c:
		i2c.close()
