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
# TODO: start with a simple maze- if it gets solved, then make the maze more complex
# TODO: Wall collision not working great- new maze being created but no overlay showing and easy to get lost (no lines drawn from paddles)
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


# Show the img scaled correctly centered on the surface
def overlay(img, surface):
    scaled_width = int(surface.get_width() * 0.8)
    aspect = img.get_height() / img.get_width()
    scaled_height = int(scaled_width * aspect)
    scaledImg = pg.transform.scale(img, (scaled_width, scaled_height))
    x = int((surface.get_width() - scaled_width)/2)
    y = int((surface.get_height() - scaled_height)/2)
    surface.blit(scaledImg, (x,y))


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


# Set up pygame
clock = pg.time.Clock()

screen = pg.display.set_mode(flags=pg.FULLSCREEN)
pg.mouse.set_visible(True)

background = pg.Surface(screen.get_size())
background = background.convert()
width, height = background.get_size()

cell_width = 100	# 100 - easy, 50 - hard

# Overlays
congratsImg = pg.image.load('congrats.png')
sorryImg = pg.image.load('sorry.png')
anotherImg = pg.image.load('tryanother.png')

# Maze stuff
m = Maze(width, height, cell_width)
m.screen = background
m.generateMaze()
m.drawMaze()

#overlay(sorryImg, background)

print("We have " + str(len(m.maze_lines)) + " maze lines")

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
        this_line = pg.draw.line(background, black, (last_x, last_y), (current_x, current_y), 2)
        last_x = current_x
        last_y = current_y
        idx = this_line.collidelist(m.maze_lines)
        if idx != -1:
            print("BOING ON WALL " + str(idx))
            overlay(sorryImg, background)
            pg.time.wait(3000)
            m = Maze(width, height, cell_width)
            m.screen = background
            m.generateMaze()
            m.drawMaze()

        if this_line.colliderect(m.exit_rect):
            print("YOU GOT OUT!")

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

		
