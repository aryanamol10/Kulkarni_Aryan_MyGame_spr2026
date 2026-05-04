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
        self.score = 0

    def enter_boss_room(self, door_type):
        boss_room = self.level_map.get(door_type)
        if boss_room:
            print(f"Entering {boss_room}...")
            self.current_level = boss_room
            self.new()

    def load_data(self):
        self.game_dir = path.dirname(__file__)
        self.img_dir  = path.join(self.game_dir, 'images')
        print(f"Loading data for {self.current_level}")

    def new(self):
        self.load_data()

        self.all_sprites       = pg.sprite.Group()
        self.all_floors        = pg.sprite.Group()
        self.all_walls         = pg.sprite.Group()
        self.all_doors         = pg.sprite.Group()
        self.all_enemy_bullets = pg.sprite.Group()
        self.all_traps         = pg.sprite.Group()
        self.all_bosses        = pg.sprite.Group()
        self.all_coins         = pg.sprite.Group()
        self.all_bullets       = pg.sprite.Group()

        map_file = path.join(self.game_dir, f'Levels/{self.current_level}.txt')
        self.map = Map(map_file)

        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):

                # lay floor under every walkable tile
                if tile not in ('1', '.'):
                    Floor(self, col, row)

                if tile == '1':
                    Wall(self, col, row)

                elif tile == '.':
                    Floor(self, col, row)

                elif tile == 'P':
                    self.player = Player(self, col, row, [self.all_sprites])
                    self.camera = Camera(self.map.width, self.map.tileheight * TILESIZE)

                elif tile == 'o':
                    Coin(self, col, row, [self.all_sprites, self.all_coins])

                elif tile == 'T':
                    Trap(self, col, row)

                elif tile == 'E':
                    Enemy(self, col, row, 'E')

                elif tile in ['A', 'B', 'C', 'D']:
                    if self.current_level.lower().startswith('boss'):
                        Enemy(self, col, row, tile)
                    else:
                        Door(self, col, row, tile, [self.all_sprites, self.all_doors])

        if self.first_run:
            intro  = "In a land of doors, there lived a hero seeking the heart of the dungeon."
            intro += "\nEach threshold hides a challenge — choose wisely."
            self.narrative.show([intro])
            self.first_run = False

        if self.current_level.lower().startswith('boss'):
            name      = self.current_level.replace('Boss_', 'Boss ')
            boss_text = f"You open the door to {name}. The air tastes of old battles..."
            boss_text += "\nPrepare yourself."
            self.narrative.show([boss_text])

            if len(self.all_bosses) == 0:
                mid_col = max(1, self.map.tilewidth  // 2)
                mid_row = max(1, self.map.tileheight // 2)
                try:
                    num       = int(self.current_level.split('_')[-1])
                    boss_type = chr(ord('A') + max(0, min(3, num - 1)))
                except Exception:
                    boss_type = 'A'
                Enemy(self, mid_col, mid_row, boss_type)

        self.run()

    def spawn_boss(self, boss_type, col, row):
        bosses = {
            'A': lambda: Enemy(self, col, row, 'A'),
            'B': lambda: Enemy(self, col, row, 'B'),
            'C': lambda: Enemy(self, col, row, 'C'),
            'D': lambda: Enemy(self, col, row, 'D'),
        }
        return bosses.get(boss_type, lambda: None)()

    def run(self):
        while self.running:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            if not (self.narrative and self.narrative.active):
                self.update()
            self.draw()

    def events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.playing = False
                self.running = False

            if self.narrative and self.narrative.active:
                self.narrative.handle_event(event)
                continue

            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.current_level = 'level_1'
                self.new()

            if event.type == pg.MOUSEBUTTONUP:
                self.check_door_click(event.pos)

            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if hasattr(self, 'player'):
                    self.player.attack()

    def update(self):
        self.all_sprites.update()

        if hasattr(self, 'player'):
            for wall in self.all_walls:
                if pg.sprite.spritecollide(self.player, pg.sprite.Group(wall), False):
                    self.player.bounce_back()

        for boss in self.all_bosses:
            if hasattr(self, 'player'):
                if pg.sprite.spritecollide(self.player, pg.sprite.Group(boss), False):
                    self.player.take_damage(5)
                    print(f"Player hit! Health: {getattr(self.player, 'health', 100)}")

        if hasattr(self, 'player') and len(self.all_coins) > 0:
            coins = pg.sprite.spritecollide(self.player, self.all_coins, True)
            if coins:
                self.score += len(coins)
                print(f"Picked up {len(coins)} coin(s). Score: {self.score}")

        if len(self.all_bullets) > 0 and len(self.all_walls) > 0:
            pg.sprite.groupcollide(self.all_bullets, self.all_walls, True, False)

        for bullet in list(self.all_bullets):
            for boss in self.all_bosses:
                if pg.sprite.spritecollide(bullet, pg.sprite.Group(boss), False):
                    bullet.kill()
                    if hasattr(boss, 'take_damage'):
                        boss.take_damage(10)
                        print(f"Boss hit! Health: {getattr(boss, 'health', 0)}")
                    if hasattr(boss, 'health') and boss.health <= 0:
                        boss.kill()

        if hasattr(self, 'camera') and hasattr(self, 'player'):
            self.camera.update(self.player)

    def draw(self):
        self.draw_game_background()

        self.draw_text(f"Level: {self.current_level}", 24, WHITE, WIDTH/2, TILESIZE)
        self.draw_text("Click doors to enter boss room | ESC to return | SPACE to attack", 14, YELLOW, WIDTH/2, TILESIZE + 30)

        if hasattr(self, 'player'):
            self.draw_text(f"Health: {100}", 20, RED,   100, TILESIZE)
            self.draw_text(f"Score: {self.score}",          16, GREEN, 100, TILESIZE + 22)

        self.draw_text(f"Bosses: {len(self.all_bosses)}", 20, YELLOW, WIDTH - 150, TILESIZE)

        if hasattr(self, 'camera'):
            for floor in self.all_floors:
                self.screen.blit(floor.image, self.camera.apply(floor))
            for sprite in self.all_sprites:
                if getattr(sprite, 'is_floor', False):
                    continue
                if sprite in self.all_bullets:
                    continue
                self.screen.blit(sprite.image, self.camera.apply(sprite))
            for bullet in self.all_bullets:
                self.screen.blit(bullet.image, self.camera.apply(bullet))
        else:
            for floor in self.all_floors:
                self.screen.blit(floor.image, floor.rect)
            for sprite in self.all_sprites:
                if getattr(sprite, 'is_floor', False):
                    continue
                if sprite in self.all_bullets:
                    continue
                self.screen.blit(sprite.image, sprite.rect)
            for bullet in self.all_bullets:
                self.screen.blit(bullet.image, bullet.rect)

        if self.narrative and self.narrative.active:
            self.narrative.draw()

        pg.display.flip()

    def draw_game_background(self):
        self.screen.fill((20, 20, 30))
        for x in range(0, WIDTH, TILESIZE):
            pg.draw.line(self.screen, (40, 40, 50), (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, (40, 40, 50), (0, y), (WIDTH, y), 1)

    def check_door_click(self, pos):
        if not hasattr(self, 'camera'):
            world_x, world_y = pos
        else:
            cam     = self.camera.camera
            world_x = pos[0] - cam.left
            world_y = pos[1] - cam.top

        for door in self.all_doors:
            if door.rect.collidepoint((world_x, world_y)):
                try:
                    self.enter_boss_room(door.door_type)
                except Exception:
                    pass
                break

    def draw_text(self, text, size, color, x, y):
        font_name    = pg.font.match_font('arial')
        font         = pg.font.Font(font_name, size)
        text_surface = font.render(text, True, color)
        text_rect    = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

    def title_screen(self):
        title    = TITLE
        subtitle = "Open World Adventure"
        btn_text = "PLAY"

        clock        = pg.time.Clock()
        btn_w, btn_h = 300, 80
        btn_rect     = pg.Rect((WIDTH - btn_w) // 2, (HEIGHT // 2) + 40, btn_w, btn_h)
        stars        = [[pg.Vector2(rand.randint(0, WIDTH), rand.randint(0, HEIGHT)), rand.randint(1, 3)] for _ in range(40)]

        running = True
        while running and self.running:
            clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                    running = False
                if event.type == pg.MOUSEBUTTONDOWN:
                    if btn_rect.collidepoint(event.pos):
                        running = False

            keys = pg.key.get_pressed()
            if keys[pg.K_ESCAPE]:
                self.running = False
                running = False

            hover = btn_rect.collidepoint(pg.mouse.get_pos())

            for i in range(HEIGHT):
                c = 8 + int(80 * (i / HEIGHT))
                pg.draw.line(self.screen, (c, c // 2, c + 20), (0, i), (WIDTH, i))

            for s in stars:
                s[0].y += s[1]
                if s[0].y > HEIGHT:
                    s[0].y = 0
                    s[0].x = rand.randint(0, WIDTH)
                pg.draw.circle(self.screen, (255, 255, 220), (int(s[0].x), int(s[0].y)), s[1])

            title_font = pg.font.Font(pg.font.match_font('arial'), 64)
            title_surf = title_font.render(title, True, (230, 230, 255))
            self.screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

            sub_font = pg.font.Font(pg.font.match_font('arial'), 20)
            sub_surf = sub_font.render(subtitle, True, (200, 200, 220))
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 60)))

            btn_color    = (80, 200, 120) if hover else (50, 150, 90)
            border_color = (255, 255, 255) if hover else (200, 200, 200)
            pg.draw.rect(self.screen, btn_color,    btn_rect, border_radius=12)
            pg.draw.rect(self.screen, border_color, btn_rect, 4, border_radius=12)

            btn_font = pg.font.Font(pg.font.match_font('arial'), 36)
            btn_surf = btn_font.render(btn_text, True, (20, 20, 30))
            self.screen.blit(btn_surf, btn_surf.get_rect(center=btn_rect.center))

            hint_surf = sub_font.render("Click to start or press ESC to quit", True, (180, 180, 200))
            self.screen.blit(hint_surf, hint_surf.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

            pg.display.flip()


if __name__ == "__main__":
    g = Game()
    g.title_screen()
    g.new()
    pg.quit()