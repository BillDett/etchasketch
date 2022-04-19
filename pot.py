# SPDX-FileCopyrightText: 2019 Mikey Sklar for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import os
import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D22)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 0
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)

print('Chan 0: Raw ADC Value: ', chan0.value)
print('Chan 0: ADC Voltage: ' + str(chan0.voltage) + 'V')
print('Chan 1: Raw ADC Value: ', chan1.value)
print('Chan 1: ADC Voltage: ' + str(chan1.voltage) + 'V')

last_read_0 = 0       # this keeps track of the last potentiometer value
last_read_1 = 0       # this keeps track of the last potentiometer value
tolerance = 250     # to keep from being jittery we'll only change


def remap_range(value, left_min, left_max, right_min, right_max):
    # this remaps a value from original (left) range to new (right) range
    # Figure out how 'wide' each range is
    left_span = left_max - left_min
    right_span = right_max - right_min

    # Convert the left range into a 0-1 range (int)
    valueScaled = int(value - left_min) / int(left_span)

    # Convert the 0-1 range into a value in the right range.
    return int(right_min + (valueScaled * right_span))

while True:
    # we'll assume that the pot didn't move
    trim_pot_changed_0 = False
    trim_pot_changed_1 = False

    # read the analog pin
    trim_pot_0 = chan0.value
    trim_pot_1 = chan1.value

    # how much has it changed since the last read?
    pot_adjust_0 = abs(trim_pot_0 - last_read_0)
    pot_adjust_1 = abs(trim_pot_1 - last_read_1)

    if pot_adjust_0 > tolerance:
        trim_pot_changed_0 = True
    if pot_adjust_1 > tolerance:
        trim_pot_changed_1 = True

    if trim_pot_changed_0:
        # convert 16bit adc0 (0-65535) trim pot read into 0-100 volume level
        set_volume_0 = remap_range(trim_pot_0, 0, 65535, 0, 100)

        # set OS volume playback volume
        print('Chan 0 = {volume_0}%' .format(volume_0 = set_volume_0))

        # save the potentiometer reading for the next loop
        last_read_0 = trim_pot_0

    if trim_pot_changed_1:
        # convert 16bit adc0 (0-65535) trim pot read into 0-100 volume level
        set_volume_1 = remap_range(trim_pot_1, 0, 65535, 0, 100)

        # set OS volume playback volume
        print('Chan 1 = {volume_1}%' .format(volume_1 = set_volume_1))

        # save the potentiometer reading for the next loop
        last_read_1 = trim_pot_1

    # hang out and do nothing for a half second
    time.sleep(0.5)


