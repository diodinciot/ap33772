#!/usr/bin/env python3

# This program reports all PDO information and walks through all PDOs in up and down manner

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
	# Write a reset to start from scratch
	i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x00, 0x00, 0x00, 0x00])
	# Read all 28-Byte PDO information
	while True:
		status=i2c.read_byte_data(I2C_ADDR, 0x1d)
		if (status & 0x05)==0x05:
			break
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
			#print("PDO ID:%d  0x%.8x" %(p.id, p))
			ValidPDOCnt+=1

			IS_APDO=((p.word & 0xc0000000)==0xc0000000) 	# APDO bit 31..30 is 0b11
			if IS_APDO:
				print("PDO ID:%d\nPDO=0x%.8x is a APDO" %(p.id, p.word))
				p.pdotype="APDO"
				p.MaxCurr=((p.word&(0x3f<<0))>>0)*50		# bit 6..0, 1LSB is 50mA
				p.MinVolt=((p.word&(0xff<<8))>>8)*100		# bit 15..8, 1LSB is 100mV
				p.MaxVolt=((p.word&(0xff<<17))>>17)*100	# bit 24..17, 1LSB is 100mV
				print("MinVoltage=%dmV\nMaxVoltage=%dmV\nMax Current=%dmA\n" %(p.MinVolt, p.MaxVolt, p.MaxCurr))
			else:
				print("PDO ID:%d\nPDO=0x%.8x is a Fixed PDO" %(p.id, p.word))
				p.pdotype="FPDO"
				p.MaxCurr=((p.word&(0x3ff<<0))>>0)*10	# bit 9..0, 1LSB is 10mA
				p.Volt=((p.word&(0x3ff<<10))>>10)*50	# bit 19..10, 1LSB is 50mV
				print("Voltage=%dmV\nMax Current=%dmA\n" %(p.Volt, p.MaxCurr))

	print("Total %d valid PDOs are detected!" %(ValidPDOCnt))
	sleep(0.5)

	# Delete unused PDOs
	for i in range(ValidPDOCnt, 7):
		pdolist.pop(-1)

	# Print all PDO out
	print("PDO List:")
	for p in pdolist:
		p.display()

	sleep(1.0)

	# Preparing RDO for later request
	rdolist=list()
	for p in pdolist:
		r=Rdo()
		rdolist.append(r)
		r.id=p.id
		r.pdotype=p.pdotype
		if p.pdotype == "FPDO":	# This is Fixed PDO
			r.RpoOpCurr=p.MaxCurr
			r.RpoMaxOpCurr=p.MaxCurr
			# Set position value bit30..28 
			# Set Operating Current in 10mA units, bit19..10
			# Set Max Operating Current in 10mA units, bit9..0
			r.word = ((r.id & 0x7) << 28) | (int(r.RpoOpCurr/10)<<10 ) | (int(r.RpoMaxOpCurr/10)<<0)
		else:			# This is APDO
			r.RpoOpVolt=p.MaxVolt
			r.RpoOpCurr=p.MaxCurr
			# Set position value bit30..28 
			# Set Output Voltage in 20mV units, bit19..9
                        # Set Operating Current in 50mA units, bit6..0
			r.word = ((r.id & 0x7) << 28) | (int(r.RpoOpVolt/20)<<9 ) | (int(r.RpoMaxOpCurr/50)<<0)

	# Print all RDO out
	print("RDO List:")
	for p in rdolist:
		p.display()

	print("#########################################################################")
	print("Start requesting PDOs")
	print("")

	# RDO submission
	cmdcnt=0
	rejcnt=0
	while True:
		for i in list(range(ValidPDOCnt-1))+list(reversed(range(1, ValidPDOCnt))):
			cmdcnt=cmdcnt+1
			# Request PDO by writing to 0x30~0x33
			i2c.write_i2c_block_data(I2C_ADDR, 0x30, [(rdolist[i].word>>0)&0xff, (rdolist[i].word>>8)&0xff, (rdolist[i].word>>16)&0xff, (rdolist[i].word>>24)&0xff])
			sleep(0.5)
			status = i2c.read_byte_data(I2C_ADDR, 0x1d)
			if (status & 0x02) != 0x02:
				rejcnt=rejcnt+1
			voltage = i2c.read_byte_data(I2C_ADDR, 0x20) * 80	# 80mV per LSB
			current = i2c.read_byte_data(I2C_ADDR, 0x21) * 24	# 24mA per LSB
			temperature = i2c.read_byte_data(I2C_ADDR, 0x22)
			print("PDO%d:\tTotal:%-3d\tstatus:0x%.2x\tRejects=%d\tV=%dmV\tI=%dmA\tT=%dC" %((i+1), cmdcnt, status, rejcnt, voltage, current, temperature))

			#sleep(0.3)

	# The following command will never be reached due to "while True" command! Actually object closure is done in except condition.
	i2c.close()	
    
except KeyboardInterrupt:
	# If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
	print("Break detected! Shut down AP33772")
	if i2c:
		# Disable ap33772
		i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x00, 0x00, 0x00, 0x00])
		i2c.write_i2c_block_data(I2C_ADDR, 0x30, [0x00, 0x00, 0x00, 0x00])
		i2c.close()
