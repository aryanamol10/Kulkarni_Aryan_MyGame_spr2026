import pygame as pg
from settings import *

#Our baseline map, using length bounds through set tilemapping
class Map:
    def __init__(self, filename):
        #creating data for building map using list
        self.data = []


        with open(filename, 'rt') as f:
            for line in f:
                self.data.append(line.strip())

        self.tilewidth = len(self.data[0])
        self.tileheight = len(self.data)
        self.width = self.tilewidth * TILESIZE


#Camera POV which is adjusetd based on player pose
class Camera:
    
    def __init__(self, width, height):
        self.camera = pg.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        # Move an entity's rect by the camera offset
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        # Center the camera on target
        x = -target.rect.centerx + int(WIDTH / 2)
        y = -target.rect.centery + int(HEIGHT / 2)

        # Limit scrolling to map boundaries
        x = min(0, x)  # left
        x = max(-(self.width - WIDTH), x)  # right
        y = min(0, y)  # top
        y = max(-(self.height - HEIGHT), y)  # bottom

        self.camera = pg.Rect(x, y, self.width, self.height)


#This spritesheet class allows us to run through sprite animations with ease
#Easy class to instantiate and run through each action
class Spritesheet:
    def __init__(self, filename):
        self.spritesheet = pg.image.load(filename).convert()
    def get_image(self, x, y, width, height):
        image = pg.Surface((width, height))
        image.blit(self.spritesheet, (0,0), (x,y, width, height))
        new_image = pg.transform.scale(image ,(width, height))
        image = new_image
        return image

# this class creates a countdown timer for a cooldown
class Cooldown:
    def __init__(self, time):
        self.start_time = 0
        # allows us to set property for time until cooldown
        self.time = time
        # self.current_time = self.time
    def start(self):
        self.start_time = pg.time.get_ticks()

    def ready(self):
        # sets current time to 
        current_time = pg.time.get_ticks()
        # if the difference between current and start time are greater than self.time
        # return True
        if current_time - self.start_time >= self.time:
            return True
        return False


    