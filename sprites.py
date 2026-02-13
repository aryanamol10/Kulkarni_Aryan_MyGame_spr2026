import pygame as pg
from pygame.sprite import Sprite
from settings import *

vec = pg.math.Vector2


#Written the collision seperately so that we dont need to make multiple for each class
#Uses pygame in built library
def collide_hit_rect(one, two):
    #Return boolean value to check collision between the two
    return one.hit_rect.colliderect(two.rect)


#Checks whether the x and y is aligned and in range with the wall
#Then it changes velocity to 0 and sets the center of x and y
#to the bounds of the wall
def collide_with_walls(sprite, group, dir):
    if dir == 'x':
        #We see that boolean is being used here for collide_with_walls
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            print("collide with wall from x dir")
            if hits[0].rect.centerx > sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.left - sprite.hit_rect.width/2
            if hits[0].rect.centerx > sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.right - sprite.hit_rect.width/2
            sprite_vel = 0
            sprite.hit_rect.centerx = sprite.pos.x
    if dir == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            print("collide with wall from x dir")
            if hits[0].rect.centery > sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.height/2
            if hits[0].rect.centery > sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.bottom - sprite.hit_rect.height/2
            sprite_vel.y = 0
            sprite.hit_rect.centert = sprite.pos.t
            

class Player(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.positive_mov_x = False
        self.positive_mov_y = False
        self.vel = vec(0,0)
        self.pos = vec(x,y) * TILESIZE
        self.acceleration = vec(0,0)
        self.trace_bullet = []
        self.shoot_cooldown = 20
        self.hit_rect = PLAYER_HIT_RECT

    def update(self):

        pressed_keys = pg.key.get_pressed()
         # Reset acceleration each frame

        if pressed_keys[pg.K_LEFT] or pressed_keys[pg.K_a]:
            self.acceleration.x = -PLAYER_ACCEL

        if pressed_keys[pg.K_RIGHT] or pressed_keys[pg.K_d]:
            self.acceleration.x = PLAYER_ACCEL

        if pressed_keys[pg.K_UP] or pressed_keys[pg.K_w]:
            self.acceleration.y = -PLAYER_ACCEL

        if pressed_keys[pg.K_DOWN] or pressed_keys[pg.K_s]:
            self.acceleration.y = PLAYER_ACCEL

        if pressed_keys[pg.K_SPACE]:
            if self.shoot_cooldown >= 20:
                self.shoot()
            self.shoot_cooldown = 0

        self.acceleration += self.vel * PLAYER_FRICTION

        self.vel += self.acceleration

        self.pos += self.vel +0.5  *self.acceleration

        self.rect.center = self.pos

        self.acceleration.x = 0
        self.acceleration.y = 0

        #self.rect.x += 1

        #self.acceleration.x += self.vel *-0.1

    def shoot(self):
        self.trace_bullet.append()
        

    
class Enemy(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        self.pos = vec(x,y)
        self.speed = 2

    def update(self):
        self.rect.x += 1

    def seek(self, player_centerx, player_centery):
        target_pos = pg.math.Vector2(player_centerx, player_centery)

        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            self.pos += direction * self.speed
            self.rect.center = self.pos
        
        #Want to seek the player
        
class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        # x,y are tile coordinates; convert to pixel coordinates
        self.pos = vec(x, y) * TILESIZE
        self.rect.center = self.pos

class Coin(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        # x,y are tile coordinates; convert to pixel coordinates
        self.pos = vec(x, y) * TILESIZE
        self.rect.center = self.pos



class Bullet(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.vel = vec(0,0)
        # x,y are tile coordinates; convert to pixel coordinates
        self.pos = vec(x, y) * TILESIZE
        self.rect.center = self.pos

    def draw(self, screen):
        pg.draw.rect(screen, GREEN, self.rect)

    def check_direction(self, key_movement):

        if key_movement == "left":
            self.vel.x = -10
        elif key_movement == "right":
            self.vel.x = 10
        elif key_movement == "up":
            self.vel.y = -10
        elif key_movement == "down":
            self.vel.y = 10