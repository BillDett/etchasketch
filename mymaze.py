import random
import sys
import pygame
#pygame.init()

WHITE = (255,255,255)
GREY = (20,20,20)
BLACK = (0,0,0)
PURPLE = (100,0,100)
RED = (255,0,0)
GREEN = (0,255,0)


class Cell():
    def __init__(self,x,y,m):
        self.maze = m
        self.x = x * self.maze.width
        self.y = y * self.maze.width
        
        self.visited = False
        self.current = False
        self.entry = False
        self.exit = False
        
        self.walls = [True,True,True,True] # top , right , bottom , left
        
        # neighbors
        self.neighbors = []

        self.maze_lines = []

        
        self.top = 0
        self.right = 0
        self.bottom = 0
        self.left = 0
        
        self.next_cell = 0

    
    def draw(self):
        if self.entry:
            pygame.draw.rect(self.maze.screen,WHITE,(self.x,self.y,self.maze.width,self.maze.width))
            self.maze.screen.blit(self.maze.startImg, (self.x,self.y))

        elif self.exit:
            self.maze.exit_rect = pygame.draw.rect(self.maze.screen,WHITE,(self.x,self.y,self.maze.width,self.maze.width))
            self.maze.screen.blit(self.maze.stopImg, (self.x,self.y))
        elif self.visited:
            the_line = None
            pygame.draw.rect(self.maze.screen,WHITE,(self.x,self.y,self.maze.width,self.maze.width))
            if self.walls[0]:
                the_line = pygame.draw.line(self.maze.screen,BLACK,(self.x,self.y),((self.x + self.maze.width),self.y),1) # top
            if self.walls[1]:
                the_line = pygame.draw.line(self.maze.screen,BLACK,((self.x + self.maze.width),self.y),((self.x + self.maze.width),(self.y + self.maze.width)),1) # right
            if self.walls[2]:
                the_line = pygame.draw.line(self.maze.screen,BLACK,((self.x + self.maze.width),(self.y + self.maze.width)),(self.x,(self.y + self.maze.width)),1) # bottom
            if self.walls[3]:
                the_line = pygame.draw.line(self.maze.screen,BLACK,(self.x,(self.y + self.maze.width)),(self.x,self.y),1) # left
            self.maze.maze_lines.append(the_line)  # Remember the bounding Rect for this line for collision detection
    
    def checkNeighbors(self):
        #print("Top; y: " + str(int(self.y / self.maze.width)) + ", y - 1: " + str(int(self.y / self.maze.width) - 1))
        if int(self.y / self.maze.width) - 1 >= 0:
            self.top = self.maze.grid[int(self.y / self.maze.width) - 1][int(self.x / self.maze.width)]
        #print("Right; x: " + str(int(self.x / self.maze.width)) + ", x + 1: " + str(int(self.x / self.maze.width) + 1))
        if int(self.x / self.maze.width) + 1 <= self.maze.cols - 1:
            self.right = self.maze.grid[int(self.y / self.maze.width)][int(self.x / self.maze.width) + 1]
        #print("Bottom; y: " + str(int(self.y / self.maze.width)) + ", y + 1: " + str(int(self.y / self.maze.width) + 1))
        if int(self.y / self.maze.width) + 1 <= self.maze.rows - 1:
            self.bottom = self.maze.grid[int(self.y / self.maze.width) + 1][int(self.x / self.maze.width)]
        #print("Left; x: " + str(int(self.x / self.maze.width)) + ", x - 1: " + str(int(self.x / self.maze.width) - 1))
        if int(self.x / self.maze.width) - 1 >= 0:
            self.left = self.maze.grid[int(self.y / self.maze.width)][int(self.x / self.maze.width) - 1]
        #print("--------------------")
        
        if self.top != 0:
            if self.top.visited == False:
                self.neighbors.append(self.top)
        if self.right != 0:
            if self.right.visited == False:
                self.neighbors.append(self.right)
        if self.bottom != 0:
            if self.bottom.visited == False:
                self.neighbors.append(self.bottom)
        if self.left != 0:
            if self.left.visited == False:
                self.neighbors.append(self.left)
        
        if len(self.neighbors) > 0:
            self.next_cell = self.neighbors[random.randrange(0,len(self.neighbors))]
            return self.next_cell
        else:
            return False


class Maze():

    def __init__(self, w, h, wd):
        global current_cell
        self.size = (w,h)
        self.width = wd
        self.cols = int(self.size[0] / self.width)
        self.rows = int(self.size[1] / self.width)
        self.stack = []
        self.screen = None	# This needs to get set after construction before drawing

        self.exit_rect = 0	# Which cell rect is the exit?

        # Icons for start/stop cells
        self.startImg = pygame.image.load('start.png')
        self.startImg = pygame.transform.scale(self.startImg, (self.width, self.width))
        self.stopImg = pygame.image.load('stop.png')
        self.stopImg = pygame.transform.scale(self.stopImg, (self.width, self.width))

        # Initialize an empty grid
        self.grid = []
        for y in range(self.rows):
            self.grid.append([])
            for x in range(self.cols):
                self.grid[y].append(Cell(x,y,self))


        current_cell = self.grid[0][0]
        self.grid[0][0].entry = True
        self.grid[self.rows-1][self.cols-1].exit = True

    def removeWalls(self, current_cell,next_cell):
        x = int(current_cell.x / self.width) - int(next_cell.x / self.width)
        y = int(current_cell.y / self.width) - int(next_cell.y / self.width)
        if x == -1: # right of current
            current_cell.walls[1] = False
            next_cell.walls[3] = False
        elif x == 1: # left of current
            current_cell.walls[3] = False
            next_cell.walls[1] = False
        elif y == -1: # bottom of current
            current_cell.walls[2] = False
            next_cell.walls[0] = False
        elif y == 1: # top of current
            current_cell.walls[0] = False
            next_cell.walls[2] = False
    
    def generateMaze(self):
        global current_cell
        mazed = False
        while not mazed:
            current_cell.visited = True
            current_cell.current = True
    
            next_cell = current_cell.checkNeighbors()
    
            if next_cell != False:
                current_cell.neighbors = []
            
                self.stack.append(current_cell)
        
                self.removeWalls(current_cell,next_cell)
        
                current_cell.current = False
        
                current_cell = next_cell
    
            elif len(self.stack) > 0:
                current_cell.current = False
                current_cell = self.stack.pop()
        
            elif len(self.stack) == 0:
                mazed = True

    def drawMaze(self):
        if self.screen is None:
            print("Error! Need to set screen first!")
            sys.exit()

        self.maze_lines = []

        for y in range(self.rows):
            for x in range(self.cols):
                self.grid[y][x].draw()





#m = Maze(200, 200, 35)
#screen = pygame.display.set_mode(m.size)
#pygame.display.set_caption("Maze Generator")
#clock = pygame.time.Clock()
#screen.fill(GREY)
#done = False

#m.screen = screen
#m.generateMaze()
#m.drawMaze()

# -------- Main Program Loop -----------
#while not done:

#    for event in pygame.event.get():
#        if event.type == pygame.QUIT:
#            done = True
    
    
#    pygame.display.flip()
    
#    clock.tick(60)

#pygame.quit()
