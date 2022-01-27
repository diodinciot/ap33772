#!/bin/bash

# This program reports all PDO information and sends out RDO specified by user

RPI_I2CBUS=1    # Using Raspberry Pi I2C_1
I2C_ADDR=0x51   # I2C address 0x51
PDO_ADDR=0x00   # PDO address range 0x00 ~ 0x1b, Starting at 0x00, max is 7 PDOs
ValidPDOCnt=0	# reset Valid PDO count

# Declare PDO array for PDO calls
declare -A PDO

# Define counter to log success/failure information
# cnt is total command count, nackcnt is the i2c not-acknowledged count, and rejcount is reject-by-charger count
TotalCnt=0
NackCnt=0
RejCnt=0

# add sleep time to slow down the automatic RDO request
sleeptime=0.4


echo "#########################################################################"

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
			
			# Save APDO/FixedPDO, voltage and max current information for PDO request
			PDO[$i, 0]="FixedPDO"
			PDO[$i, 1]=$Volt
			PDO[$i, 2]=$MaxCurr
			
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

			# Save APDO/FixedPDO, max voltage, and max current information for PDO request
			PDO[$i, 0]="APDO"
			PDO[$i, 1]=$MaxVolt
			PDO[$i, 2]=$MaxCurr
		fi
		ValidPDOCnt=$(($ValidPDOCnt + 1))
	fi
done 

#sleep $sleeptime

echo Total $ValidPDOCnt valid PDOs are detected!
echo "#########################################################################"
echo Start requesting PDOs
echo 

read -p 'Enter PDO ID: ' PDONUM
i=$(($PDONUM-1))
		
# Reset RDO
RDO=0x00000000

# Process RDO based on different APDO/FixedPDO formats
if [ ${PDO[$i, 0]} != "APDO" ]
then
	# This is a fixed PDO, 
	# Set bit30..28 to position value
	RDO=$(($RDO | ((0x7 & ($i + 1)) << 28)))
	# Set Operating Current in 10mA units, bit19..10
	RDO=$(($RDO | ((${PDO[$i, 2]} / 10) << 10)))
	# Set Max Operating Current in 10mA units, bit9..0
	RDO=$(($RDO | ((${PDO[$i, 2]} / 10) << 0)))
	printf "0x%.4x\n\n" $RDO
	printf "Requesting PDO%d: Fixed PDO: V=%dmV I=%dmA\n" $(($i+1)) $((PDO[$i, 1])) $((PDO[$i, 2]))
else
	# This is a APDO, 
	# Set bit30..28 to position value
	RDO=$(($RDO | ((0x7 & ($i + 1)) << 28)))
	# Set Output Voltage in 20mV units, bit19..9
	read -p 'Enter output voltage(mV) for APDO: ' APDOVOLT
	PDO[$i, 1]=$APDOVOLT
	#echo VOLT11bits=${PDO[$i, 1]}
	RDO=$(($RDO | (((${PDO[$i, 1]} / 20)&0x7ff) << 9)))
	# Set Operating Current in 50mA units, bit6..0
	read -p 'Enter output current(mA) for APDO: ' APDOCURR
	PDO[$i, 2]=$APDOCURR
	RDO=$(($RDO | (((${PDO[$i, 2]} / 50)&0x7f) << 0)))
	printf "0x%.4x\n\n" $RDO
	printf "Requesting PDO%d: APDO V=%dmV I=%dmA\n" $(($i+1)) $((PDO[$i, 1])) $((PDO[$i, 2]))
fi

# Generate RDO by writing 4 bytes RDO information starting from address 0x30
#echo -n set to PDO$(($i++1)) cnt=$cnt" "
#printf "i2cset -y %d 0x%.2x 0x%.2x 0x%.2x 0x%.2x 0x%.2x 0x%.2x %s\n" $RPI_I2CBUS $I2C_ADDR 0x30 $((($RDO>>0) & 0xff)) $((($RDO>>8) & 0xff)) $((($RDO>>16) & 0xff)) $(((RDO>>24) & 0xff)) "i" 
i2cset -y $RPI_I2CBUS $I2C_ADDR 0x30 $((($RDO>>0) & 0xff)) $((($RDO>>8) & 0xff)) $((($RDO>>16) & 0xff)) $(((RDO>>24) & 0xff)) i 
if [ $? != 0 ]
then
	NackCnt=$(($NackCnt + 1))	
fi
sleep $sleeptime # Need some sleeptime for block read/write

# Check if RDO got granted.
status=`i2cget -y 1 0x51 0x1d`
if [ "$status" != "" ]
then
	accept=$(($status & 0x02))
fi
if [ $accept == 0 ]
then
	RejCnt=$(($ReJcnt + 1))
fi

#sleep $sleeptime
voltage=$((`i2cget -y $RPI_I2CBUS $I2C_ADDR 0x20` * 80))
#echo -n voltage=${voltage}mV" "

#sleep $sleeptime
current=$((`i2cget -y $RPI_I2CBUS $I2C_ADDR 0x21` * 24))
#echo -n voltage=${voltage}mA" "

#sleep $sleeptime
temp=`i2cget -y 1 0x51 0x22`
printf "PDO%d: \tNackCnt=%-3d  status=0x%.2x\tRejCnt=%-3d   V=%dmV\tI=%dmA\tT=%dC\n" $(($i+1)) $NackCnt $status $RejCnt $voltage $current $temp

#sleep $sleeptime

