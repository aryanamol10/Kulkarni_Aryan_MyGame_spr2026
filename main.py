# game engine using template from Chris Bradfield's "Making Games with Python & Pygame"
# 
'''
Main file responsible for game loop including input, update, and draw methods.
Door-based level progression system with boss fights.
'''

import pygame as pg
import sys
from os import path
from settings import *
from sprites import *
from utils import *

class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        self.playing = True
        self.game_cooldown = Cooldown(5000)
        self.current_level = "level_1"
        self.level_map = {
            'A': "boss_A",
            'B': "boss_B", 
            'C': "boss_C",
            'D': "boss_D"
        }
    
    def load_data(self):
        self.game_dir = path.dirname(__file__)
        self.img_dir = path.join(self.game_dir, 'images')
        # Remove: self.wall_dir = pg.image.load(path.join(self.img_dir, 'wall_art.png')).convert_alpha()
        print(f"Loading data for {self.current_level}")
        
    def new(self):
        self.load_data()
        
        # sprite groups
        self.all_sprites = pg.sprite.Group()
        self.all_floors  = pg.sprite.Group()    # <‑‑ new
        self.all_walls   = pg.sprite.Group()
        self.all_doors   = pg.sprite.Group()
        self.all_bosses  = pg.sprite.Group()
        self.all_bullets = pg.sprite.Group()
        
        # Load the current level map
        map_file = path.join(self.game_dir, f'{self.current_level}.txt')
        self.map = Map(map_file)
        
        # Initialize camera using map dimensions
        map_height = self.map.tileheight * TILESIZE
        self.camera = Camera(self.map.width, map_height)
        
        # Parse map data
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == '.':
                    self.all_floors.add(Floor(self, col, row))           # <‑‑ floor
                elif tile == '1':
                    self.all_walls.add(Wall(self, col, row))
                elif tile == 'P':
                    self.player = Player(self, col, row)
                    self.all_sprites.add(self.player)
                elif tile in self.level_map:
                    self.all_doors.add(Door(self, col, row, tile))
                elif tile in ['A', 'B', 'C', 'D']:
                    boss = self.spawn_boss(tile, col, row)
                    if boss:
                        self.all_bosses.add(boss)
                        self.all_sprites.add(boss)

        # add floors first so they render beneath everything else
        self.all_sprites.add(self.all_floors)
        self.all_sprites.add(self.all_walls)
        self.all_sprites.add(self.all_doors)
        
        self.run()

    def spawn_boss(self, boss_type, col, row):
        """Spawn appropriate boss based on type"""
        bosses = {
            'A': lambda: Enemy(self, col * TILESIZE, row * TILESIZE, speed=2, health=50),
            'B': lambda: Enemy(self, col * TILESIZE, row * TILESIZE, speed=3, health=75),
            'C': lambda: Enemy(self, col * TILESIZE, row * TILESIZE, speed=2.5, health=60),
            'D': lambda: Enemy(self, col * TILESIZE, row * TILESIZE, speed=3.5, health=100)
        }
        return bosses.get(boss_type, lambda: None)()

    def run(self):
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pg.MOUSEBUTTONUP:
                self.check_door_click(event.pos)
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    # Return to main level
                    self.current_level = "level_1"
                    self.new()
                if event.key == pg.K_SPACE:
                    # Player attack
                    if hasattr(self, 'player'):
                        self.player.attack()

    def check_door_click(self, mouse_pos):
        """Check if player clicked on a door to enter boss room"""
        for door in self.all_doors:
            door_screen_pos = self.camera.apply(door)
            door_rect = door.image.get_rect(topleft=door_screen_pos)
            
            if door_rect.collidepoint(mouse_pos):
                # Get door type (A, B, C, D) from door_type attribute
                boss_room = self.level_map.get(door.door_type)
                if boss_room:
                    print(f"Entering {boss_room}...")
                    self.current_level = boss_room
                    self.new()
                door.animate()

    def update(self):
        self.all_sprites.update()
        
        # Check player collision with walls
        if hasattr(self, 'player'):
            for wall in self.all_walls:
                if pg.sprite.spritecollide(self.player, pg.sprite.Group(wall), False):
                    self.player.bounce_back()
        
        # Check player collision with bosses
        for boss in self.all_bosses:
            if hasattr(self, 'player'):
                if pg.sprite.spritecollide(self.player, pg.sprite.Group(boss), False):
                    self.player.take_damage(5)
                    print(f"Player hit! Health: {getattr(self.player, 'health', 100)}")
        
        # Check bullets hitting bosses
        for bullet in self.all_bullets:
            for boss in self.all_bosses:
                if pg.sprite.spritecollide(bullet, pg.sprite.Group(boss), False):
                    bullet.kill()
                    if hasattr(boss, 'take_damage'):
                        boss.take_damage(10)
                        print(f"Boss hit! Boss health: {getattr(boss, 'health', 0)}")
                    # Remove dead bosses
                    if hasattr(boss, 'health') and boss.health <= 0:
                        boss.kill()
        
        # Update camera to follow player
        if hasattr(self, 'camera') and hasattr(self, 'player'):
            self.camera.update(self.player)
    
    def draw(self):
        self.draw_game_background()
        
        # Draw UI
        self.draw_text(f"Level: {self.current_level}", 24, WHITE, WIDTH/2, TILESIZE)
        self.draw_text("Click doors to enter boss room | ESC to return | SPACE to attack", 14, YELLOW, WIDTH/2, TILESIZE + 30)
        
        if hasattr(self, 'player'):
            player_health = getattr(self.player, 'health', 100)
            self.draw_text(f"Health: {player_health}", 20, RED, 100, TILESIZE)
        
        # Count remaining bosses
        boss_count = len(self.all_bosses)
        self.draw_text(f"Bosses: {boss_count}", 20, YELLOW, WIDTH - 150, TILESIZE)
        
        # Draw all sprites with camera offset
        if hasattr(self, 'camera'):
            for sprite in self.all_sprites:
                self.screen.blit(sprite.image, self.camera.apply(sprite))
            # Draw bullets separately if they exist
            for bullet in self.all_bullets:
                self.screen.blit(bullet.image, self.camera.apply(bullet))
        else:
            self.all_sprites.draw(self.screen)
            self.all_bullets.draw(self.screen)
        
        pg.display.flip()

    def draw_game_background(self):
        # leave the transparent grid overlay but do not clear to solid
        # the floor sprites now draw a textured ground
        self.screen.fill((20, 20, 30))   # keep a dark fill in case of gaps
        grid_size = TILESIZE
        for x in range(0, WIDTH, grid_size):
            pg.draw.line(self.screen, (40, 40, 50), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, grid_size):
            pg.draw.line(self.screen, (40, 40, 50), (0, y), (WIDTH, y), 1)

    def draw_text(self, text, size, color, x, y):
        font_name = pg.font.match_font('arial')
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

if __name__ == "__main__":
    g = Game()

while g.running:
    g.new()

pg.quit()





