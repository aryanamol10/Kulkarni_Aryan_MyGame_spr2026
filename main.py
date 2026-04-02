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
import random as rand

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
        self.narrative = NarrativeBox(self)
        self.first_run = True
        self.level_map = {
            'A': "Boss_1",
            'B': "Boss_2", 
            'C': "Boss_3",
            'D': "Boss_4"
        }

    def enter_boss_room(self, door_type):
        """Switch to the boss map associated with a door type and restart the level."""
        boss_room = self.level_map.get(door_type)
        if boss_room:
            print(f"Entering {boss_room}...")
            self.current_level = boss_room
            # Restart the level (this will recreate sprites and load the new map)
            self.new()
    
    def load_data(self):
        self.game_dir = path.dirname(__file__)
        self.img_dir = path.join(self.game_dir, 'images')
        # Remove: self.wall_dir = pg.image.load(path.join(self.img_dir, 'wall_art.png')).convert_alpha()
        print(f"Loading data for {self.current_level}")
        
    def new(self):
        self.load_data()
        
        # these are the sprite groups we use
        self.all_sprites = pg.sprite.Group()
        self.all_floors  = pg.sprite.Group()
        self.all_walls   = pg.sprite.Group()
        self.all_doors   = pg.sprite.Group()
        self.all_bosses  = pg.sprite.Group()
        self.all_bullets = pg.sprite.Group()
        
        # Load the current level map
        map_file = path.join(self.game_dir, f'Levels/{self.current_level}.txt')
        self.map = Map(map_file)
        
        # Initialize camera using map dimensions
        map_height = self.map.tileheight * TILESIZE
        self.camera = Camera(self.map.width, map_height)
        
        # Parsing map data
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == '1':
                    self.all_walls.add(Wall(self, col, row))
                elif tile == 'P':
                    self.player = Player(self, col, row)
                    self.all_sprites.add(self.player)
                elif tile in ['A','B','C','D']:
                    # Pass the tile character so the Door knows its type
                    self.all_doors.add(Door(self, col, row, tile))

        # add floors first so they render beneath everything else
        self.all_sprites.add(self.all_floors)
        self.all_sprites.add(self.all_walls)
        self.all_sprites.add(self.all_doors)

        # Prepare and show narratives (intro on first run, or boss flavor)
        if self.first_run:
            intro = "In a land of doors, there lived a hero seeking the heart of the dungeon."
            intro += "\nEach threshold hides a challenge — choose wisely."
            self.narrative.show([intro])
            self.first_run = False

        if self.current_level.lower().startswith('boss'):
            name = self.current_level.replace('Boss_', 'Boss ').replace('Boss', 'Boss')
            boss_text = f"You open the door to {name}. The air tastes of old battles..."
            boss_text += "\nPrepare yourself."
            self.narrative.show([boss_text])

        self.run()

    def spawn_boss(self, boss_type, col, row):
        """Spawn appropriate boss based on type"""
        bosses = {
            'A': lambda: Enemy(self, col * TILESIZE, row * TILESIZE, 'A'),
            'B': lambda: Enemy(self, col * TILESIZE, row * TILESIZE, 'B'),
            'C': lambda: Enemy(self, col * TILESIZE, row * TILESIZE, 'C'),
            'D': lambda: Enemy(self, col * TILESIZE, row * TILESIZE, 'D')
        }
        return bosses.get(boss_type, lambda: None)()

    #running all of our functions here
    def run(self):
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            # let narrative block updates while active
            if not (self.narrative and self.narrative.active):
                self.update()
            self.draw()

    #Checking for actions like keyboard presses
    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False

            # pass events to narrative box first
            if self.narrative and self.narrative.active:
                self.narrative.handle_event(event)
                continue

            # ESC returns to beginning
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.current_level = 'level_1'
                self.new()

            if event.type == pg.MOUSEBUTTONUP:
                self.check_door_click(event.pos)

            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                # Player attack
                if hasattr(self, 'player'):
                    self.player.attack()

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
        
        # Updating camera to follow player
        if hasattr(self, 'camera') and hasattr(self, 'player'):
            self.camera.update(self.player)
    
    def draw(self):
        self.draw_game_background()
        
        # draw the interface here
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

        # draw narrative overlay if active
        if self.narrative and self.narrative.active:
            self.narrative.draw()

        pg.display.flip()

    def draw_game_background(self):
        # leave  grid overlay but do not clear to solid
        # the floor sprites now draw a textured ground
        self.screen.fill((20, 20, 30))   # keep a dark fill in case of gaps
        grid_size = TILESIZE
        for x in range(0, WIDTH, grid_size):
            pg.draw.line(self.screen, (40, 40, 50), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, grid_size):
            pg.draw.line(self.screen, (40, 40, 50), (0, y), (WIDTH, y), 1)

    # Fonts.. can be adjusted as needed
    def draw_text(self, text, size, color, x, y):
        font_name = pg.font.match_font('arial')
        font = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

    def title_screen(self):
        """Display an opening title screen with a Start button."""
        title = TITLE
        subtitle = "A Tiny Dungeon Adventure"
        btn_text = "PLAY"

        clock = pg.time.Clock()
        btn_w, btn_h = 300, 80
        btn_rect = pg.Rect((WIDTH - btn_w) // 2, (HEIGHT // 2) + 40, btn_w, btn_h)

        # Simple animated background stars
        stars = [[pg.Vector2(rand.randint(0, WIDTH), rand.randint(0, HEIGHT)), rand.randint(1, 3)] for _ in range(40)]

        running = True
        while running and self.running:
            dt = clock.tick(FPS) / 1000
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                    running = False
                if event.type == pg.MOUSEBUTTONDOWN:
                    if btn_rect.collidepoint(event.pos):
                        running = False

            mpos = pg.mouse.get_pos()
            hover = btn_rect.collidepoint(mpos)

            # draw gradient background
            for i in range(HEIGHT):
                c = 8 + int(80 * (i / HEIGHT))
                pg.draw.line(self.screen, (c, c // 2, c + 20), (0, i), (WIDTH, i))

            # update & draw stars
            for s in stars:
                s[0].y += s[1]
                if s[0].y > HEIGHT:
                    s[0].y = 0
                    s[0].x = rand.randint(0, WIDTH)
                pg.draw.circle(self.screen, (255, 255, 220), (int(s[0].x), int(s[0].y)), s[1])

            # Title
            title_font = pg.font.Font(pg.font.match_font('arial'), 64)
            title_surf = title_font.render(title, True, (230, 230, 255))
            title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3))
            self.screen.blit(title_surf, title_rect)

            # Subtitle
            sub_font = pg.font.Font(pg.font.match_font('arial'), 20)
            sub_surf = sub_font.render(subtitle, True, (200, 200, 220))
            sub_rect = sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 60))
            self.screen.blit(sub_surf, sub_rect)

            # Start button
            btn_color = (80, 200, 120) if hover else (50, 150, 90)
            border_color = (255, 255, 255) if hover else (200, 200, 200)
            pg.draw.rect(self.screen, btn_color, btn_rect, border_radius=12)
            pg.draw.rect(self.screen, border_color, btn_rect, 4, border_radius=12)

            btn_font = pg.font.Font(pg.font.match_font('arial'), 36)
            btn_surf = btn_font.render(btn_text, True, (20, 20, 30))
            btn_rect_text = btn_surf.get_rect(center=btn_rect.center)
            self.screen.blit(btn_surf, btn_rect_text)

            # small hint
            hint = "Click to start or press ESC to quit"
            hint_surf = sub_font.render(hint, True, (180, 180, 200))
            hint_rect = hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 40))
            self.screen.blit(hint_surf, hint_rect)

            # keyboard shortcuts
            keys = pg.key.get_pressed()
            if keys[pg.K_ESCAPE]:
                self.running = False
                running = False

            pg.display.flip()

if __name__ == "__main__":
    g = Game()
    # Show opening title screen; returns to start the first level when PLAY is clicked
    g.title_screen()
    g.new()
    pg.quit()
