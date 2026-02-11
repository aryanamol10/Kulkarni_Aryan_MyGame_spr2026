# game engine using template from Chris Bradfield's "Making Games with Python & Pygame"
# 
'''
Main file responsible for game loop including input, update, and draw methods.

Tools for game development.

# creating pixel art:
https://www.piskelapp.com/

# free game assets:
https://opengameart.org/

# free sprite sheets:
https://www.kenney.nl/assets

# sound effects:
https://www.bfxr.net/
# music:
https://incompetech.com/music/royalty-free/


'''

import pygame as pg
import sys
from os import path
from settings import *
from sprites import *
from utils import *
# import settings


class Camera:
    """A simple camera to follow the player by offsetting sprite blits.

    The camera stores a rect representing the offset to apply to sprite.rects.
    """
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


# the game class that will be instantiated in order to run the game...
class Game:
    def __init__(self):
        pg.init()
        # setting up pygame screen using tuple value for width height
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        self.playing = True
        self.player_lis = []
        self.game_cooldown = Cooldown(5000)
    
    # a method is a function tied to a Class

    def load_data(self):

        #Accesses the file system or operating system
        self.game_dir = path.dirname(__file__)

        #creates an insantiation of Map class with text file of l1(not created)
        self.map = Map(path.join(self.game_dir, 'level1.txt'))

        print("Data is loaded")
        
    def new(self):
        self.load_data()
        self.all_sprites = pg.sprite.Group()
        self.all_walls = pg.sprite.Group()
        self.all_mobs = pg.sprite.Group()
        self.all_coins = pg.sprite.Group()
        # Initialize camera using map dimensions
        map_height = self.map.tileheight * TILESIZE
        self.camera = Camera(self.map.width, map_height)
        #self.player = Player(self, 15, 15)
        #self.all_sprites.add(*self.player_lis, *self.enemy_lis)

        for row, tiles in enumerate(self.map.data):
            for col, tile, in enumerate(tiles):
                if tile == '1':
                    #call class constructor without giving value
                    self.all_walls.add(Wall(self, col, row))
                if tile == 'P':
                    self.player = Player(self, col, row)
                if tile == 'E':
                    self.all_mobs.add(Enemy(self, 15, 15))
                if tile == 'C':
                    self.all_coins.add(Enemy(self, 15, 15))

        self.run()

    def run(self):
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()
            self.seek_until()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pg.MOUSEBUTTONUP:
                print("i can get mouse input")
                print(event.pos)

    def quit(self):
        pass

    def update(self):
        self.all_sprites.update()
        # update camera to follow the player (if available)
        if hasattr(self, 'camera') and hasattr(self, 'player'):
            self.camera.update(self.player)


    def seek_until(self):
        for mob in self.all_mobs:
            mob.seek(self.player.pos.x, self.player.pos.x)
    
    def draw(self):
        self.screen.fill(BLUE)
        self.draw_text("Hello World", 24, WHITE, WIDTH/2, TILESIZE)
        #self.draw_text(str(self.dt), 24, WHITE, WIDTH/2, HEIGHT/4)
        #self.draw_text(str(self.enemy_check), 24, WHITE, WIDTH/2, HEIGHT/4)
        # self.draw_text(str(self.game_cooldown.time), 24, WHITE, WIDTH/2, HEIGHT/.5)
        self.draw_text(str(self.game_cooldown.ready()), 24, WHITE, WIDTH/2, HEIGHT/3)
        #for t in self.player.trace:
        #    pg.draw.rect(self.screen, GREEN, (t[0], t[1], TILESIZE, TILESIZE)
        #for bullet in self.player.trace_bullet:
        #    pg.draw.rect(self.screen, GREEN, bullet)
        # Draw sprites with camera offset so world scrolls with the player
        if hasattr(self, 'camera'):
            for sprite in self.all_sprites:
                self.screen.blit(sprite.image, self.camera.apply(sprite))
        else:
            self.all_sprites.draw(self.screen)
        pg.display.flip()


    def draw_text(self, text, size, color, x, y):
        font_name = pg.font.match_font('arial')
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x,y)
        self.screen.blit(text_surface, text_rect)

if __name__ == "__main__":
    g = Game()

while g.running:
    g.new()


pg.quit()


    

    
