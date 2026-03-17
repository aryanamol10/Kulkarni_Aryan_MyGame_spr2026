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
    def __init__(self, game, col, row, boss_type):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.vel = vec(0, 0)
        self.hit_rect = ENEMY_HIT_RECT
        self.hit_rect.center = self.pos


        # Boss Difficulty Scaling
        stats = {'A': 50, 'B': 100, 'C': 150, 'D': 300}
        self.health = stats.get(boss_type, 50)
        self.speed = 150

    def take_damage(self, damage):
        """Boss takes damage from player bullets"""
        self.health -= damage
        print(f"Boss health: {self.health}")

    def update(self):
        if hasattr(self.game, 'player'):
            self.seek(self.game.player.pos.x, self.game.player.pos.y)
        
        collide_with_walls(self, self.game.player, 'x')
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

class Door(Sprite):
    def init(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "door_animation.png"))
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = self.spritesheet.get_image(0, 0, TILESIZE, TILESIZE)
        self.load_images()
        self.rect.center = self.pos
        self.door_states = []
        self.open_door = False

    def load_images(self):
        self.door_states = [self.spritesheet.get_image(0, 0, TILESIZE, TILESIZE), 
                                self.spritesheet.get_image(TILESIZE, 0, TILESIZE, TILESIZE)]
        for frame in self.standing_frames:
            frame.set_colorkey(BLACK)

    def check_door_state(self):
        now = pg.time.get_ticks()
        if self.open_door:
                self.last_update = now
                self.door_states = (self.current_frame + 1) % len(self.standing_frames)
                bottom = self.rect.bottom
                self.image = self.standing_frames[self.current_frame]
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom

    def update(self):

        if hasattr(self.game, 'player'):
            self.open_door = collide_hit_rect(self, self.game.player)
        self.check_door_state()





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
    def __init__(self, game, pos, direction):
        self.groups = game.all_sprites, game.all_bullets
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface((10, 10))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=pos)
        self.vel = direction * 500

    def update(self):
        self.rect.center += self.vel * self.game.dt
        # Kill if it leaves map
        if not self.game.map.width > self.rect.x > 0: self.kill()

class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill((60, 60, 80)) # Dark blue-grey "brick" color
        self.rect = self.image.get_rect(topleft=(x*TILESIZE, y*TILESIZE))

class Door(Sprite):
    def __init__(self, game, x, y, door_type):
        self.groups = game.all_sprites, game.all_doors
        Sprite.__init__(self, self.groups)
        self.door_type = door_type
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(BLUE)
        pg.draw.rect(self.image, WHITE, (4, 4, 24, 24), 2) # Adding a "border"
        self.rect = self.image.get_rect(topleft=(x*TILESIZE, y*TILESIZE))