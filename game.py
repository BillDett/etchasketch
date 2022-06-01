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
# One button moves to next harder level
#
# One button clears the current level
#

class Paddle:

	def __init__(self, chan, mn, mx):
                self.channel = chan
                self.last_read = 0
                self.tolerance = 250
                self.value = mn
                self.min = mn
                self.max = mx
                #print("Paddle " + str(chan) + "- min=" + str(mn) + " max=" + str(mx))


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
    scaled_width = int(maze_width_pixels * 0.8)
    aspect = img.get_height() / img.get_width()
    scaled_height = int(scaled_width * aspect)
    scaledImg = pg.transform.scale(img, (scaled_width, scaled_height))
    x = int((surface.get_width() - scaled_width)/2)
    y = int((surface.get_height() - scaled_height)/2)
    surface.blit(scaledImg, (x,y))


# GPIO
level_button = 6
clear_button = 26
GPIO.setup(level_button, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Tie switch to GND
GPIO.add_event_detect(level_button, GPIO.RISING, bouncetime=200)
GPIO.setup(clear_button, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Tie switch to GND
GPIO.add_event_detect(clear_button, GPIO.RISING, bouncetime=200)

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
red = pg.Color(255, 0, 0)

# Desired width of maze (pixels)
maze_width_pixels = 1400


# Set up pygame
# We use a full screen, but only write within the 'margins' of the aspect_ratio
clock = pg.time.Clock()

screen = pg.display.set_mode(flags=pg.FULLSCREEN)
pg.mouse.set_visible(True)

background = pg.Surface(screen.get_size())
background = background.convert()
orig_width, height = background.get_size()
x_offset = int((orig_width - maze_width_pixels)/2)

print("Original width: " + str(orig_width))
print("X Offset: " + str(x_offset))

#cell_width = 100	# 100 - easy, 50 - hard
#cell_width = 50	# 100 - easy, 50 - hard
cell_width = [150, 100, 75, 50]
current_width = 0


# Overlays
congratsImg = pg.image.load('congrats.png')
sorryImg = pg.image.load('sorry.png')
anotherImg = pg.image.load('tryanother.png')

# Maze stuff
m = Maze(maze_width_pixels, height, cell_width[current_width], x_offset)
m.screen = background
m.generateMaze()

# create the paddles
paddle_x = Paddle(chan0, m.x_offset, m.x_offset+maze_width_pixels)
paddle_y = Paddle(chan1, m.y_offset, height-m.y_offset)

# see where the paddles are before we start drawing
last_x = paddle_x.read_value()
last_y = paddle_y.read_value()

# store list of line segments that make up what we draw with the paddles
traces = []

going = True
while going:
        clock.tick(60)

	# Read the Paddles and save a trace from where we were to where we now are
        current_x = paddle_x.read_value()
        current_y = paddle_y.read_value()
        if (current_x != last_x) or (current_y != last_y):
            the_trace = [(last_x, last_y), (current_x, current_y)]
            traces.append(the_trace)
            print("Saving " + str(the_trace))
        last_x = current_x
        last_y = current_y

        # Clear the background
        screen.blit(background, (0,0))

        m.drawMaze()

        # Draw all the traces
        last_line = None
        for trace in traces:
            last_line = pg.draw.line(background, black, trace[0], trace[1], 2)

        if last_line is not None:
            # Did we collide with a wall?
            idx = last_line.collidelist(m.maze_lines)
            if idx != -1:
                #print("BOING ON WALL " + str(idx))
                overlay(sorryImg, background)

            if last_line.colliderect(m.exit_rect):
                print("YOU GOT OUT!")
                overlay(congratsImg, background)


        # Did they hit the level button? If so, go to next maze
        if GPIO.event_detected(level_button):
            if current_width == len(cell_width)-1:
                current_width = 0
            else:
                current_width = current_width + 1
            traces = []
            background.fill(black)
            m = Maze(maze_width_pixels, height, cell_width[current_width], x_offset)
            m.screen = background
            m.generateMaze()
            m.drawMaze()

        # Did they hit the clear button? If so, clear the paddle lines
        if GPIO.event_detected(clear_button):
            print("Clear!")
            traces = []
            m.drawMaze()

	# Listen for any keystroke- if we got quit signal or 'q', exit app
	# NOTE: This doesn't work if we run this remotely via ssh
        for event in pg.event.get():
                if event.type == pg.QUIT:
                    going = False
                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_q:
                        going = False

        # Update the display
        pg.display.flip()

pg.quit()

		
