import pygame as pg


WIDTH = 800
HEIGHT = 600
TITLE = "My cool game..."
FPS = 60
TILESIZE = 32

#player vals
PLAYER_SPEED = 300
PLAYER_ACCEL = 0.5
PLAYER_FRICTION = -0.12
#Collision through TILESIZE length
PLAYER_HIT_RECT = pg.Rect(0,0, TILESIZE, TILESIZE)


#RGB
BLUE = (0,0,255)
WHITE = (255,255,255)
GREEN = (0,255,0)
RED = (255,0,0)
