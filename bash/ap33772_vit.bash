#!/bin/bash
RPI_I2CBUS=1    # Using Raspberry Pi I2C_1
I2C_ADDR=0x51   # I2C address 0x51

sleeptime=0.3

voltdata=`i2cget -y $RPI_I2CBUS $I2C_ADDR 0x20`
voltage=$((voltdata * 80))
#echo voltage=${voltage}mV" "
sleep $sleeptime

currdata=`i2cget -y $RPI_I2CBUS $I2C_ADDR 0x21`
current=$((currdata * 24))
#echo current=${current}mA" "
sleep $sleeptime

temp=`i2cget -y 1 0x51 0x22`
printf "voltage=%dmV current=%dmA temperature=%dC\n" $voltage $current $temp
sleep $sleeptime

