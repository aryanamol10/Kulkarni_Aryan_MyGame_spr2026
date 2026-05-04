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
        self.fps_counter = 0
        self.fps_timer = 0
        self.created_floors = set()  # Track created floor positions to avoid duplicates
        self.background_surface = None  # Cache background for performance
        self.font_cache = {}  # Cache fonts for better performance

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
                # Only create floor sprites near the player spawn area to reduce sprite count
                # This dramatically reduces the number of sprites from thousands to dozens
                if tile == 'P':
                    # Create floors in a small area around the player spawn
                    for r in range(max(0, row-5), min(len(self.map.data), row+6)):
                        for c in range(max(0, col-8), min(len(tiles), col+9)):
                            if self.map.data[r][c] not in ('1', 'P') and (r, c) not in self.created_floors:
                                Floor(self, c, r)
                                self.created_floors.add((r, c))

                if tile == '1':
                    Wall(self, col, row)

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
            self.fps_timer += self.dt
            self.fps_counter += 1

            # Update FPS display every second
            if self.fps_timer >= 1.0:
                self.current_fps = self.fps_counter
                self.fps_counter = 0
                self.fps_timer = 0

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
        # Update all sprites - this is essential for player movement and game logic
        self.all_sprites.update()

        # Only check collisions if player exists
        if hasattr(self, 'player') and self.player.health > 0:
            # Use group collision methods instead of individual loops (much faster)
            # Player vs Bosses collision
            boss_hits = pg.sprite.spritecollide(self.player, self.all_bosses, False, collided=collide_hit_rect)
            if boss_hits:
                self.player.take_damage(5)
                # Only print occasionally to avoid spam
                if pg.time.get_ticks() % 1000 < 50:  # Print roughly once per second
                    print(f"Player hit! Health: {self.player.health}")

            # Player vs Coins collision
            coins_collected = pg.sprite.spritecollide(self.player, self.all_coins, True, collided=collide_hit_rect)
            if coins_collected:
                self.score += len(coins_collected)
                if pg.time.get_ticks() % 1000 < 50:  # Print roughly once per second
                    print(f"Picked up {len(coins_collected)} coin(s). Score: {self.score}")

        # Bullet vs Wall collisions (group vs group is efficient)
        if self.all_bullets and self.all_walls:
            pg.sprite.groupcollide(self.all_bullets, self.all_walls, True, False, collided=collide_hit_rect)

        # Bullet vs Boss collisions (optimized)
        if self.all_bullets and self.all_bosses:
            bullet_boss_hits = pg.sprite.groupcollide(self.all_bullets, self.all_bosses, True, False, collided=collide_hit_rect)
            for boss in bullet_boss_hits.values():
                for b in boss:  # Each boss might be hit by multiple bullets
                    if hasattr(b, 'take_damage'):
                        b.take_damage(10)
                        if pg.time.get_ticks() % 1000 < 50:  # Print roughly once per second
                            print(f"Boss hit! Health: {getattr(b, 'health', 0)}")
                        if hasattr(b, 'health') and b.health <= 0:
                            b.kill()

        # Update camera
        if hasattr(self, 'camera') and hasattr(self, 'player'):
            self.camera.update(self.player)

    def draw(self):
        self.draw_game_background()

        self.draw_text(f"Level: {self.current_level}", 24, WHITE, WIDTH/2, TILESIZE)
        self.draw_text("Click doors to enter boss room | ESC to return | SPACE to attack", 14, YELLOW, WIDTH/2, TILESIZE + 30)

        if hasattr(self, 'player'):
            self.draw_health_bar()
            self.draw_text(f"Score: {self.score}", 16, GREEN, 100, TILESIZE + 22)

        self.draw_text(f"Bosses: {len(self.all_bosses)}", 20, YELLOW, WIDTH - 150, TILESIZE)
        self.draw_text(f"FPS: {getattr(self, 'current_fps', FPS)}", 16, WHITE, WIDTH - 150, TILESIZE + 25)
        self.draw_text(f"Sprites: {len(self.all_sprites)}", 16, WHITE, WIDTH - 150, TILESIZE + 40)

        # Optimized culling-based drawing for maximum performance
        if hasattr(self, 'camera'):
            # Define culling area (screen + small buffer to prevent pop-in)
            cam_left = self.camera.camera.left - 50
            cam_right = self.camera.camera.right + 50
            cam_top = self.camera.camera.top - 50
            cam_bottom = self.camera.camera.bottom + 50

            # Draw floors within culling area only
            for floor in self.all_floors:
                floor_rect = self.camera.apply(floor)
                if (floor_rect.right >= cam_left and floor_rect.left <= cam_right and
                    floor_rect.bottom >= cam_top and floor_rect.top <= cam_bottom):
                    self.screen.blit(floor.image, floor_rect)

            # Draw all non-floor sprites within culling area (excluding bullets)
            for sprite in self.all_sprites:
                if not getattr(sprite, 'is_floor', False) and sprite not in self.all_bullets:
                    sprite_rect = self.camera.apply(sprite)
                    if (sprite_rect.right >= cam_left and sprite_rect.left <= cam_right and
                        sprite_rect.bottom >= cam_top and sprite_rect.top <= cam_bottom):
                        self.screen.blit(sprite.image, sprite_rect)

            # Draw bullets (always draw these as they're fast-moving and few in number)
            for bullet in self.all_bullets:
                self.screen.blit(bullet.image, self.camera.apply(bullet))
        else:
            # Fallback for no camera
            for floor in self.all_floors:
                self.screen.blit(floor.image, floor.rect)
            for sprite in self.all_sprites:
                if not getattr(sprite, 'is_floor', False) and sprite not in self.all_bullets:
                    self.screen.blit(sprite.image, sprite.rect)
            for bullet in self.all_bullets:
                self.screen.blit(bullet.image, bullet.rect)

        if self.narrative and self.narrative.active:
            self.narrative.draw()

        pg.display.flip()

    def draw_game_background(self):
        # Cache background surface for massive performance improvement
        if self.background_surface is None:
            self.background_surface = pg.Surface((WIDTH, HEIGHT))
            self.background_surface.fill((20, 20, 30))
            # Draw grid lines
            for x in range(0, WIDTH, TILESIZE):
                pg.draw.line(self.background_surface, (40, 40, 50), (x, 0), (x, HEIGHT), 1)
            for y in range(0, HEIGHT, TILESIZE):
                pg.draw.line(self.background_surface, (40, 40, 50), (0, y), (WIDTH, y), 1)

        self.screen.blit(self.background_surface, (0, 0))

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
        # Cache fonts for better performance
        font_key = (size, color)
        if font_key not in self.font_cache:
            font_name = pg.font.match_font('arial')
            self.font_cache[font_key] = pg.font.Font(font_name, size)

        font = self.font_cache[font_key]
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

    def draw_health_bar(self):
        if not hasattr(self, 'player'):
            return

        health = self.player.health
        max_health = 100  # Assuming max health is 100
        health_ratio = health / max_health

        # Health bar dimensions
        bar_width = 200
        bar_height = 20
        bar_x = 50
        bar_y = TILESIZE - 5

        # Background (gray)
        pg.draw.rect(self.screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))

        # Health fill color based on health percentage
        if health_ratio > 0.7:
            fill_color = GREEN
        elif health_ratio > 0.3:
            fill_color = YELLOW
        else:
            fill_color = RED

        # Fill the bar
        fill_width = int(bar_width * health_ratio)
        pg.draw.rect(self.screen, fill_color, (bar_x, bar_y, fill_width, bar_height))

        # Border
        pg.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

        # Health text
        health_text = f"{health}/{max_health}"
        self.draw_text(health_text, 16, WHITE, bar_x + bar_width // 2, bar_y - 25)

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