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


class State():
    def __init__(self, owner):
        self.owner = owner
    def enter(self):
        pass
    def update(self, now):
        pass
    def exit(self):
        pass

class WalkingState(State):
    def update(self, now):
        
        if now - self.owner.last_update > 100:
            self.owner.last_update = now
            
            
            if self.owner.vel.length() > 0.1:
                self.owner.current_frame = (self.owner.current_frame + 1) % len(self.owner.standing_frames)
            else:
                self.owner.current_frame = 0 

            # Update the actual image
            bottom = self.owner.rect.bottom
            self.owner.image = self.owner.standing_frames[self.owner.current_frame]
            self.owner.rect = self.owner.image.get_rect()
            self.owner.rect.bottom = bottom


class ParentState(Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.state = None 

    def update_state(self, state_class):
        if self.state:
            self.state.exit()
        self.state = state_class(self)
        self.state.enter()

    def update(self):
        if self.state:
            now = pg.time.get_ticks()
            self.state.update(now)

class DoorClosedState(State):
    def update(self, now):
        if collide_hit_rect(self.owner.game.player, self.owner):
            self.owner.change_state(DoorOpenState)

class DoorOpenState(State):
    def enter(self):
        self.owner.image = self.owner.door_states[1] # Open frame
    def update(self, now):
        if not collide_hit_rect(self.owner.game.player, self.owner):
            self.owner.change_state(DoorClosedState)

class CoinSpinState(State):
    def update(self, now):
        if now - self.owner.last_update > 350:
            self.owner.last_update = now
            self.owner.current_frame = (self.owner.current_frame + 1) % len(self.owner.standing_frames)
            self.owner.image = self.owner.standing_frames[self.owner.current_frame]
        



            
class Player(ParentState):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        super().__init__(self.groups)
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
        self.walking = False
        self.last_update = 0
        self.current_frame = 0
        self.health = 100
        self.shooting_state = False


        self.update_state(WalkingState)


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

        if pressed_keys[pg.K_SPACE]:
            self.shoot_state = True

        #self.state_check()
        super().update()

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





"""
def check_walking_state(self, now, rect):
    if self.vel != vec(0.0, 0.0):
        if now - self.last_update > 35:
                self.last_update = now
                current_frame = (self.current_frame + 1) % len(self.standing_frames)
                bottom = rect.bottom
                image = self.standing_frames[self.current_frame]
                rect = self.image.get_rect()
                recbottom = bottom
    elif self.vel == vec(0.0, 0.0):
        if now - self.last_update > 35:
                self.last_update = now
                self.current_frame = 1
                bottom = rect.bottom
                image = self.standing_frames[self.current_frame]
                rect = self.image.get_rect()
                recbottom = bottom

    return image, rect, recbottom
"""

def check_shooting_state(shoot_state, trace_bullet, game, rectx, recty):
    if shoot_state:
        trace_bullet.append(Bullet(game, rectx, recty))
        game.all_bullets.add(trace_bullet[-1])



    
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
        

class Door(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_doors
        Sprite.__init__(self, self.groups)
        self.game = game
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "door_animation.png"))
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = self.spritesheet.get_image(0, 0, TILESIZE, TILESIZE)
        self.load_images()
        self.rect = self.image.get_rect()
        self.open_door = False
        self.current_door_state = 0

    def load_images(self):
        self.door_states = [self.spritesheet.get_image(0, 0, TILESIZE, TILESIZE), 
                                self.spritesheet.get_image(TILESIZE, 0, TILESIZE, TILESIZE)]
        for frame in self.door_states:
            frame.set_colorkey(BLACK)

    def check_door_state(self):
        now = pg.time.get_ticks()
        if self.open_door:
                self.last_update = now
                self.current_door_state = (self.current_door_state + 1) % len(self.door_states)
                bottom = self.rect.bottom
                self.image = self.door_states[int(self.current_door_state)]
                self.rect = self.image.get_rect()
                self.rect.bottom = bottom

    def update(self):

        if hasattr(self.game, 'player'):
            self.open_door = collide_hit_rect(self.game.player, self)
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
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos
        # Kill if it leaves screen (simplified)
        if not (0 < self.rect.x < WIDTH and 0 < self.rect.y < HEIGHT):
            self.kill()

class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill((60, 60, 80)) # Dark blue-grey "brick" color
        self.rect = self.image.get_rect(topleft=(x*TILESIZE, y*TILESIZE))