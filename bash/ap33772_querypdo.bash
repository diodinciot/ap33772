#!/bin/bash

# This program reports all PDO information

RPI_I2CBUS=1    # Using Raspberry Pi I2C_1
I2C_ADDR=0x51   # I2C address 0x51
PDO_ADDR=0x00   # PDO address range 0x00 ~ 0x1b, Starting at 0x00, max is 7 PDOs
ValidPDOCnt=0	# reset Valid PDO count

for i in {0..6}
do
	# Read PDO info 4-byte or 32-bit long each
	PDO=$(( (`i2cget -y $RPI_I2CBUS $I2C_ADDR $(($PDO_ADDR+4*$i+3))` << 24) 
		| (`i2cget -y $RPI_I2CBUS $I2C_ADDR $(($PDO_ADDR+4*$i+2))` << 16) 
		| (`i2cget -y $RPI_I2CBUS $I2C_ADDR $(($PDO_ADDR+4*$i+1))` << 8) 
		| (`i2cget -y $RPI_I2CBUS $I2C_ADDR $(($PDO_ADDR+4*$i))`) ))

	# If PDO reads all zero data, it's not a valid PDO. Only processing valide PDO
	IS_VALID_PDO=$(( $PDO != 0x00000000 ))
	if [ $IS_VALID_PDO == 1 ]
	then
		# Check if this is regular PDO or APDO, Bit31..30==11 is APDO, Bit31..30==00 is PDO
		IS_APDO=$(( ($PDO & 0xc0000000) == 0xc0000000 ))
		if [ $IS_APDO != 1 ]
		then
			# Print out Fixed PDO information
			printf "PDO ID:%d\nPDO=0x%.8x is a %s\n" $(($i+1)) $PDO "Fixed PDO"

			# Find out profiles for Fixed PDO, refer to Table 5 of AP33772 Sink Controller EVB User Guide Section 5.3
			MaxCurr=$(( (($PDO & (0x3ff<<0))>>0) * 10 ))    # bit 9..0, 1LSB is 10mA
			Volt=$(( (($PDO & (0x3ff<<10))>>10) * 50 )) # bit 19..10, 1LSB is 50mV
			echo Voltage=$(($Volt))mV
			echo Max Current=$(($MaxCurr))mA
			echo
		else
			# Print out APDO information
			printf "PDO ID:%d\nPDO=0x%.8x is a %s\n" $(($i+1)) $PDO "APDO"

			# Find out profiles for APDO, refer to Table 6 of AP33772 Sink Controller EVB User Guide Section 5.3
			MaxCurr=$(( (($PDO & (0x3f<<0))>>0) * 50 ))    # bit 6..0, 1LSB is 50mA
			MinVolt=$(( (($PDO & (0xff<<8))>>8) * 100 ))   # bit 15..8, 1LSB is 100mV
			MaxVolt=$(( (($PDO & (0xff<<17))>>17) * 100 )) # bit 24..17, 1LSB is 100mV
			echo Min Voltage=$(($MinVolt))mV
			echo Max Voltage=$(($MaxVolt))mV
			echo Max Current=$(($MaxCurr))mA
			echo
		fi
		ValidPDOCnt=$(($ValidPDOCnt + 1))
	fi
done 

echo Total $ValidPDOCnt valid PDOs are detected!
