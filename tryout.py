'''
Main file responsible for game loop including input, update, and draw methods.
'''

import pygame as pg
import sys
from os import path
from settings import *
from sprites import *
from utils import *

#import settings


# the game class that will be instantiated in order to run the game
class Game:
    def __init__(self):
        #setting up pygame screen using tuple value for width height
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        #pg.display.set_icon(IMAGE)
        #pg.display.set_allow_screensaver=True
        self.clock = pg.time.Clock()
        #self.load_data()


    # method is a function tied to a Class
    def load_data(self):
        pass

    def new(self):
        pass

    def run(self):
        pass

    def events(self):
        #stuff that happens with peripherals
        #touchscreen, microphone, keystrokes
        pass

if __name__ == "__main__":
    print("hey")



g = Game()


