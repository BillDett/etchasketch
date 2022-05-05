import sys
import os
import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import pygame as pg
import RPi.GPIO as GPIO
from mymaze import Maze

# Etch-a-Sketch
#
# Requires two potentiometers wired to your GPIO SPI interface via an MCP3008 chip
#
# Also need a button pulling pin 6 to GND to reset the screen
#

class Paddle:

	def __init__(self, chan, mn, mx):
		self.channel = chan
		self.last_read = 0
		self.tolerance = 250
		self.value = -1
		self.min = mn
		self.max = mx


	def read_value(self):
		# we'll assume that the pot didn't move
		trim_pot_changed = False

		# read the analog pin
		trim_pot = self.channel.value

		# how much has it changed since the last read?
		pot_adjust = abs(trim_pot - self.last_read)

		if pot_adjust > self.tolerance:
			# Map the analog input (0..65535) to the Paddle min/max range
			scaled = trim_pot/65535	# map to 0..1
			self.value = int(self.min + (scaled * (self.max - self.min)))

			# save the potentiometer reading for the next loop
			self.last_read = trim_pot

		return self.value


# GPIO
button = 6
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Tie switch to GND
GPIO.add_event_detect(button, GPIO.RISING, bouncetime=200)

# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D22)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create analog input channels on pin 0 and 1
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)

pg.init()

## Colors
grey = pg.Color(202, 204, 207)
black = pg.Color(0, 0, 0)
white = pg.Color(1, 1, 1)

clock = pg.time.Clock()

screen = pg.display.set_mode(flags=pg.FULLSCREEN)
pg.mouse.set_visible(True)

background = pg.Surface(screen.get_size())
background = background.convert()
#background.fill(grey)
width, height = background.get_size()

# Maze stuff
m = Maze(width, height, 100)
m.screen = background
m.generateMaze()
m.drawMaze()

# create the paddles
paddle_x = Paddle(chan0, 0, width)
paddle_y = Paddle(chan1, 0, height)

# see where the paddles are before we start drawing
last_x = paddle_x.read_value()
last_y = paddle_y.read_value()

going = True
while going:
	clock.tick(60)
	screen.blit(background, (0,0))
	pg.display.flip()

	# Read the Paddles and render a segment from where we were to where we now are
	current_x = paddle_x.read_value()
	current_y = paddle_y.read_value()
	#print('X = {} / Y = {}'.format(current_x, current_y))	
	# Need to think about cursor- probably need a sprite instead
	#cursor = pg.Rect((current_x, current_y), (5,5))
	#pg.draw.ellipse(background, white, cursor)
	pg.draw.line(background, black, (last_x, last_y), (current_x, current_y), 2)
	last_x = current_x
	last_y = current_y

	# Did they hit the 'shake' button? If so, clear screen
	if GPIO.event_detected(button):
                #background.fill(grey)
		m.drawMaze()

	# Listen for any keystroke- if we got quit signal or 'q', exit app
	# NOTE: This doesn't work if we run this remotely via ssh
	for event in pg.event.get():
		if event.type == pg.QUIT:
			going = False
		elif event.type == pg.KEYDOWN:
			if event.key == pg.K_q:
				going = False

pg.quit()

		
