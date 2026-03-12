import pygame as pg
from pygame.sprite import Sprite
from settings import *
from utils import *
from os import path

vec = pg.math.Vector2

def collide_hit_rect(one, two):
    return one.hit_rect.colliderect(two.rect)

def collide_with_walls(sprite, group, dir):
    if dir == 'x':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            print("collide with wall from x dir")
            if hits[0].rect.centerx > sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.left - (sprite.hit_rect.width/2)
            if hits[0].rect.centerx < sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.right + (sprite.hit_rect.width/2)
            sprite.vel.x = 0
            sprite.hit_rect.centerx = sprite.pos.x
    if dir == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            print("collide with wall from y dir")
            if hits[0].rect.centery >= sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.height/2
            if hits[0].rect.centery <= sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_rect.height/2
            sprite.vel.y = 0
            sprite.hit_rect.centery = sprite.pos.y

player_Dictionaries = {}
            
class Player(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "Player_Sprite.png"))
        self.load_images()
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = self.spritesheet.get_image(139.5, 132, TILESIZE, TILESIZE)
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()
        self.positive_mov_x = False
        self.positive_mov_y = False
        self.vel = vec(0, 0)
        self.pos = vec(x, y) * TILESIZE
        self.acceleration = vec(0, 0)
        self.trace_bullet = []
        self.shoot_cooldown = 20
        self.hit_rect = PLAYER_HIT_RECT
        self.direction_facing = ""
        self.jumping = False
        self.walking = False
        self.last_update = 0
        self.current_frame = 0
        self.health = 100
        
    def shoot(self):
        self.trace_bullet.append(Bullet(self.game, self.rect.x, self.rect.y))
        self.game.all_bullets.add(self.trace_bullet[-1])

    def attack(self):
        """Player attack method"""
        if self.shoot_cooldown <= 0:
            self.shoot()
            self.shoot_cooldown = 20

    def take_damage(self, damage):
        """Player takes damage from boss"""
        self.health -= damage
        if self.health < 0:
            self.health = 0
        print(f"Player health: {self.health}")

    def bounce_back(self):
        """Player bounces back from collision"""
        self.vel *= -0.5

    def update(self):
        pressed_keys = pg.key.get_pressed()
        self.shoot_cooldown += 1

        if pressed_keys[pg.K_LEFT] or pressed_keys[pg.K_a]:
            self.acceleration.x = -PLAYER_ACCEL
            self.direction_facing = "left"

        if pressed_keys[pg.K_RIGHT] or pressed_keys[pg.K_d]:
            self.acceleration.x = PLAYER_ACCEL
            self.direction_facing = "right"

        if pressed_keys[pg.K_UP] or pressed_keys[pg.K_w]:
            self.acceleration.y = -PLAYER_ACCEL
            self.direction_facing = "up"

        if pressed_keys[pg.K_DOWN] or pressed_keys[pg.K_s]:
            self.acceleration.y = PLAYER_ACCEL
            self.direction_facing = "down"

        self.state_check()
        self.animate()

        self.acceleration += self.vel * PLAYER_FRICTION
        self.vel += self.acceleration
        self.pos += self.vel + 0.5 * self.acceleration
        self.rect.center = self.pos
        self.acceleration.x = 0
        self.acceleration.y = 0

        collide_with_walls(self, self.game.all_walls, 'x')
        self.hit_rect.centery = self.pos.y
        collide_with_walls(self, self.game.all_walls, 'y')
        self.hit_rect.centerx = self.pos.x

    def load_images(self):
        WIDTH = TILESIZE
        HEIGHT = TILESIZE
        self.standing_frames = [self.spritesheet.get_image(0, 0, WIDTH, HEIGHT), 
                               self.spritesheet.get_image(WIDTH, 0, WIDTH, HEIGHT),
                               self.spritesheet.get_image(WIDTH*2, 0, WIDTH, HEIGHT),
                               self.spritesheet.get_image(WIDTH*3, 0, WIDTH, HEIGHT),
                               self.spritesheet.get_image(WIDTH*4, 0, WIDTH, HEIGHT),
                               self.spritesheet.get_image(WIDTH*5, 0, WIDTH, HEIGHT),
                               self.spritesheet.get_image(WIDTH*6, 0, WIDTH, HEIGHT),
                               self.spritesheet.get_image(WIDTH*7, 0, WIDTH, HEIGHT),
                               self.spritesheet.get_image(WIDTH*8, 0, WIDTH, HEIGHT),
                               self.spritesheet.get_image(WIDTH*9, 0, WIDTH, HEIGHT)]
        for frame in self.standing_frames:
            frame.set_colorkey(BLACK)

    def animate(self):
        now = pg.time.get_ticks()
        if not self.jumping and self.walking:
            if now - self.last_update > 35:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.standing_frames)
                bottom = self.rect.bottom
                self.image = self.standing_frames[self.current_frame]
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom
        elif not self.walking:
            if now - self.last_update > 35:
                self.last_update = now
                self.current_frame = 1
                bottom = self.rect.bottom
                self.image = self.standing_frames[self.current_frame]
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom

    def state_check(self):
        if self.vel != vec(0.1, 0.1):
            self.walking = True
        else: 
            self.walking = False

    
class Enemy(Sprite):
    def __init__(self, game, x, y, speed=2, health=50):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.vel = vec(0, 0)
        self.pos = vec(x, y)
        self.speed = speed
        self.health = health
        self.max_health = health
        self.hit_rect = ENEMY_HIT_RECT
        self.hit_rect.center = self.pos

    def take_damage(self, damage):
        """Boss takes damage from player bullets"""
        self.health -= damage
        print(f"Boss health: {self.health}")

    def update(self):
        # Seek player if available
        if hasattr(self.game, 'player'):
            self.seek(self.game.player.pos.x, self.game.player.pos.y)
        
        collide_with_walls(self, self.game.all_walls, 'x')
        self.hit_rect.centery = self.pos.y
        collide_with_walls(self, self.game.all_walls, 'y')
        self.hit_rect.centerx = self.pos.x

    def seek(self, player_centerx, player_centery):
        """Seek and move towards player"""
        target_pos = pg.math.Vector2(player_centerx, player_centery)
        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed
            self.rect.center = self.pos
            self.hit_rect.center = self.pos
        
class Floor(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_floors
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        # simple tile; you can replace this with an actual image
        self.image.fill((50, 50, 70))
        pg.draw.rect(self.image, (60, 60, 80), self.image.get_rect(), 1)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y) * TILESIZE
        self.rect.center = self.pos
        
    def update(self):
        pass

class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.game = game
        # try loading texture; fall back to plain fill if not present
        try:
            self.image = pg.image.load(path.join(self.game.img_dir,
                                                 'wall_tile.png')).convert_alpha()
            self.image = pg.transform.scale(self.image, (TILESIZE, TILESIZE))
        except Exception:
            self.image = pg.Surface((TILESIZE, TILESIZE))
            self.image.fill((100, 70, 40))
            pg.draw.rect(self.image, (80, 50, 20), self.image.get_rect(), 2)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y) * TILESIZE
        self.rect.center = self.pos
    def update(self):
        pass

class Door(pg.sprite.Sprite):
    def __init__(self, game, x, y, door_type):
        pg.sprite.Sprite.__init__(self)
        self.game = game
        self.x = x
        self.y = y
        self.door_type = door_type  # A, B, C, or D
        self.direction = self.get_direction_label()
        self.is_open = False
        self.animation_progress = 0
        self.animation_speed = 0.1
        
        # Door dimensions
        self.door_width = 80
        self.door_height = 100
        
        self.image = pg.Surface((self.door_width, self.door_height))
        self.rect = self.image.get_rect()
        self.rect.center = (x * TILESIZE + TILESIZE // 2, y * TILESIZE + TILESIZE // 2)
        
        self.draw_door()
    
    def get_direction_label(self):
        """Convert door type (A, B, C, D) to displayable direction"""
        direction_map = {
            'A': 'Boss A',
            'B': 'Boss B',
            'C': 'Boss C',
            'D': 'Boss D'
        }
        return direction_map.get(self.door_type, 'Unknown')
    
    def draw_door(self):
        """Draw the door with current animation state"""
        self.image.fill((30, 30, 30))  # Dark background
        
        # Door frame
        pg.draw.rect(self.image, (100, 70, 40), self.image.get_rect(), 3)
        
        # Door opening animation
        if self.is_open:
            door_open = int(self.door_width * self.animation_progress)
            # Draw opening crack
            pg.draw.rect(self.image, (150, 150, 150), (door_open, 10, 5, self.door_height - 20))
        else:
            # Door knob
            knob_x = int(self.door_width * 0.75)
            knob_y = self.door_height // 2
            pg.draw.circle(self.image, (200, 150, 50), (knob_x, knob_y), 8)
            
            # Door label with direction
            self.draw_door_label()
    
    def draw_door_label(self):
        """Draw direction label on door"""
        font = pg.font.Font(None, 28)
        label_text = font.render(self.direction, True, (255, 200, 0))
        label_rect = label_text.get_rect(center=(self.door_width // 2, self.door_height // 2))
        self.image.blit(label_text, label_rect)
    
    def animate(self):
        """Trigger door opening animation"""
        self.is_open = True
        self.animation_progress = 0
    
    def update(self):
        """Update door animation"""
        if self.is_open and self.animation_progress < 1.0:
            self.animation_progress += self.animation_speed
        
        self.draw_door()

class Coin(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "coin_sprite_sheet.png"))
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = self.spritesheet.get_image(0, 0, TILESIZE, TILESIZE)
        self.load_images()
        self.rect = self.image.get_rect()
        self.vel = vec(0, 0)
        self.pos = vec(x, y) * TILESIZE
        self.rect.center = self.pos
        self.last_update = 0
        self.current_frame = 0

    def load_images(self):
        self.standing_frames = [self.spritesheet.get_image(0, 0, TILESIZE, TILESIZE), 
                                self.spritesheet.get_image(TILESIZE, 0, TILESIZE, TILESIZE)]
        self.moving_frames = [self.spritesheet.get_image(TILESIZE*2, 0, TILESIZE, TILESIZE), 
                                self.spritesheet.get_image(TILESIZE*3, 0, TILESIZE, TILESIZE)]
        for frame in self.standing_frames:
            frame.set_colorkey(BLACK)

    def animate(self):
        now = pg.time.get_ticks()
        if now - self.last_update > 350:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.standing_frames)
                bottom = self.rect.bottom
                self.image = self.standing_frames[self.current_frame]
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom

    def update(self):
        self.animate()

class Bullet(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_bullets
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((8, 8))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.vel = vec(0, 0)
        self.pos = vec(x, y)
        self.rect.center = self.pos

    def draw(self, screen, pos):
        pg.draw.rect(screen, GREEN, (pos[0], pos[1], 8, 8))

    def check_dir(self, direction):
        if direction == "left":
            self.vel.x = -10
        elif direction == "right":
            self.vel.x = 10
        elif direction == "up":
            self.vel.y = -10
        elif direction == "down":
            self.vel.y = 10

    def update(self):
        self.pos += self.vel
        self.rect.center = self.pos
        
        # Remove bullet if off screen
        if self.rect.x < 0 or self.rect.x > WIDTH or self.rect.y < 0 or self.rect.y > HEIGHT:
            self.kill()