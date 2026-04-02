import pygame as pg
from pygame.sprite import Sprite
from settings import *
from utils import *
from os import path
import math

vec = pg.math.Vector2

def collide_hit_rect(one, two):
    # Floors should not block movement — skip collision if either side is a floor
    if getattr(one, 'is_floor', False) or getattr(two, 'is_floor', False):
        return False
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


#State machine logic: allows us to call ParentState and switch
#between other objects and classes like MovingState, OpenState, etc.
class State():
    def __init__(self, owner):
        self.owner = owner
    def enter(self):
        pass
    def update(self, *args, **kargs):
        if self.state:
            now = pg.time.get_ticks()
            self.state.update(now)
    def exit(self):
        pass

class WalkingRightState(State):
    def update(self):
        now = pg.time.get_ticks()
        
        if now - self.owner.last_update > 50:
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

class WalkingLeftState(State):
    def update(self):
        now = pg.time.get_ticks()
        
        if now - self.owner.last_update > 50:
            self.owner.last_update = now
            
            
            if self.owner.vel.length() > 0.1:
                self.owner.current_frame = (self.owner.current_frame + 1) % len(self.owner.standing_frames)
            else:
                self.owner.current_frame = 0 

            # Update the actual image
            bottom = self.owner.rect.bottom
            self.owner.image = pg.transform.flip(self.owner.standing_frames[self.owner.current_frame], True, False)
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
            self.state.update()

class DoorClosedState(State):
    def enter(self):
        self.owner.image =  self.owner.door_states[0]
    def update(self):
        if collide_hit_rect(self.owner.game.player, self.owner):
            self.owner.update_state(DoorOpenState)


class DoorOpenState(State):
    def enter(self):
        self.owner.image = self.owner.door_states[1]
        # Immediately switch certain level based on corresponding door
        try:
            match self.owner.door_type:
                case "A":
                    self.owner.game.current_level = 'Boss_1'
                case "B":
                    self.owner.game.current_level = "Boss_2"
                case "C":
                    self.owner.game.current_level = "Boss_3"
                case "D":
                    self.owner.game.current_level = "Boss_4"
            self.owner.game.new()
        except Exception:
            pass
    def update(self):
        if not collide_hit_rect(self.owner.game.player, self.owner):
            self.owner.update_state(DoorClosedState)

#Keep coining spinning
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
        # cooldown in frames; 0 means ready
        self.shoot_cooldown = 0
        self.hit_rect = PLAYER_HIT_RECT
        self.direction_facing = ""
        self.walking = False
        self.last_update = 0
        self.current_frame = 0
        self.health = 100
        self.shooting_state = False


        self.update_state(WalkingRightState)


    def attack(self):
        """Player attack method"""
        # single-shot with a short frame-based cooldown
        if self.shoot_cooldown <= 0:
            self.shoot()
            self.shoot_cooldown = 15

    def shoot(self):
        """Spawn a bullet in the player's facing direction."""
        # determine direction based on last horizontal facing; default right
        dir_vec = vec(1, 0)
        if self.direction_facing == 'left':
            dir_vec = vec(-1, 0)
        elif self.direction_facing == 'right':
            dir_vec = vec(1, 0)

        # spawn slightly in front of the player
        # displace spawn up to the player's head so animation looks synced
        head_offset = vec(0, -TILESIZE * 0.25)
        spawn_pos = self.pos + dir_vec * (TILESIZE // 2) + head_offset
        # small visual spark at head when shooting
        try:
            spark = pg.Surface((6, 6), pg.SRCALPHA)
            pg.draw.circle(spark, (180, 220, 255), (3, 3), 3)
            # blit immediate tiny spark to screen (camera aware)
            if hasattr(self.game, 'camera'):
                self.game.screen.blit(spark, self.game.camera.apply(self).move(0, -TILESIZE//4))
        except Exception:
            pass
        Bullet(self.game, spawn_pos, dir_vec)

    def take_damage(self, damage):
        """Player takes damage from boss"""
        self.health -= damage
        if self.health < 0:
            self.health = 0
        print(f"Player health: {self.health}")

    def bounce_back(self):
        """Player bounces back from collision"""
        self.vel *= -0.5

    #reverse direction basically (flip or transform the model)
    def change_dir(self, direction):
        try:
            if direction == "right":
                self.update_state(WalkingRightState)
            if direction == "left":
                self.update_state (WalkingLeftState)

        except Exception:
            pass

    def update(self):
        pressed_keys = pg.key.get_pressed()
        # cooldown counts down to zero
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if pressed_keys[pg.K_LEFT] or pressed_keys[pg.K_a]:
            self.acceleration.x = -PLAYER_ACCEL
            self.direction_facing = "left"

        if pressed_keys[pg.K_RIGHT] or pressed_keys[pg.K_d]:
            self.acceleration.x = PLAYER_ACCEL
            self.direction_facing = "right"

        if pressed_keys[pg.K_UP] or pressed_keys[pg.K_w]:
            self.acceleration.y = -PLAYER_ACCEL

        if pressed_keys[pg.K_DOWN] or pressed_keys[pg.K_s]:
            self.acceleration.y = PLAYER_ACCEL

        # Space is handled via KEYDOWN -> player.attack() in main.events


        self.change_dir(self.direction_facing)
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


#Still work in progress but almost able to work
def check_shooting_state(shoot_state, trace_bullet, game, pos, direction):
    """Helper to spawn a bullet if `shoot_state` is truthy.

    Kept for compatibility with older code; creates a Bullet and
    appends it to the provided trace list.
    """
    if shoot_state:
        b = Bullet(game, pos, direction)
        trace_bullet.append(b)
        try:
            game.all_bullets.add(b)
        except Exception:
            pass



    
class Enemy(Sprite):
    def __init__(self, game, col, row, enemy_type):
        # Add to both all_sprites and all_bosses groups (used for collision checks)
        self.groups = game.all_sprites, game.all_bosses
        Sprite.__init__(self, self.groups)
        self.game = game
        self.type = enemy_type

        # position (col,row are tile coords); center within tile
        self.pos = vec(col * TILESIZE + TILESIZE / 2, row * TILESIZE + TILESIZE / 2)
        self.rect = pg.Rect(0, 0, TILESIZE, TILESIZE)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # hit rect and physics
        self.hit_rect = ENEMY_HIT_RECT.copy()
        self.hit_rect.center = self.pos

        # Type-specific stats
        template = {
            'A': {'health': 180, 'speed': 90, 'color': (200, 50, 50), 'ranged': False, 'zigzag': False, 'turret': False},
            'B': {'health': 120, 'speed': 60, 'color': (40, 120, 200), 'ranged': True, 'shoot_delay': 1200},
            'C': {'health': 140, 'speed': 80, 'color': (140, 60, 180), 'zigzag': True},
            'D': {'health': 260, 'speed': 40, 'color': (200, 160, 40), 'ranged': True, 'turret': True, 'shoot_delay': 900},
            'E': {'health': 32,  'speed': 140, 'color': (200, 90, 140), 'ranged': False}
        }
        stats = template.get(enemy_type, template['E'])
        self.health = stats['health']
        self.max_health = self.health
        self.speed = stats.get('speed', 80)
        self.color = stats.get('color', RED)
        self.ranged = stats.get('ranged', False)
        self.zigzag = stats.get('zigzag', False)
        self.turret = stats.get('turret', False)
        self.shoot_delay = stats.get('shoot_delay', 1000)

        # animation frames (procedural)
        self.standing_frames = self._make_frames()
        self.current_frame = 0
        self.last_update = 0
        self.image = self.standing_frames[0]
        self.rect = self.image.get_rect()
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # physics velocity vector (used by collision helpers)
        self.vel = vec(0, 0)

        # attack timing
        self.last_shot = 0

    def take_damage(self, damage):
        """Boss takes damage from player bullets"""
        self.health -= damage
        # flash or knockback could be added here
        if self.health <= 0:
            self.kill()
        print(f"Enemy {self.type} hit! Health: {self.health}")

    def _make_frames(self):
        frames = []
        for i in range(4):
            surf = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA)
            surf.fill((0, 0, 0, 0))
            # body
            shade = tuple(max(0, min(255, c + i * 8 - 8)) for c in self.color)
            pg.draw.circle(surf, shade, (TILESIZE // 2, TILESIZE // 2), TILESIZE // 2 - 2)
            # eyes
            eye_x = 9 if i % 2 == 0 else 11
            pg.draw.circle(surf, (255, 255, 255), (TILESIZE // 2 - eye_x, TILESIZE // 2 - 6), 3)
            pg.draw.circle(surf, (255, 255, 255), (TILESIZE // 2 + eye_x, TILESIZE // 2 - 6), 3)
            frames.append(surf)
        return frames

    def update(self):
        now = pg.time.get_ticks()
        # animate
        if now - self.last_update > 140:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.standing_frames)
            self.image = self.standing_frames[self.current_frame]

        if not hasattr(self.game, 'player'):
            return

        # decide movement pattern
        player_vec = self.game.player.pos
        dir_vec = player_vec - self.pos
        dist = dir_vec.length()
        if dist > 0:
            direction = dir_vec.normalize()
        else:
            direction = vec(0, 0)

        if self.turret:
            # turret stays in place
            self.vel = vec(0, 0)
        else:
            if self.zigzag and dist > 8:
                perp = vec(-direction.y, direction.x)
                offset = math.sin(pg.time.get_ticks() / 220.0) * 0.5
                move = (direction + perp * offset)
                if move.length() > 0:
                    move = move.normalize()
                self.vel = move * self.speed
            else:
                # simple chase
                self.vel = direction * self.speed

            # integrate velocity
            self.pos += self.vel * self.game.dt

        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.hit_rect.center = self.pos

        # collisions
        collide_with_walls(self, self.game.all_walls, 'x')
        collide_with_walls(self, self.game.all_walls, 'y')

        # ranged attack logic
        if (self.ranged or self.turret) and dist < 800:
            if now - self.last_shot > self.shoot_delay:
                self.last_shot = now
                self.shoot_at_player()

        # draw healthbar overlay onto image for feedback
        self._draw_healthbar()

    def shoot_at_player(self):
        # spawn an enemy bullet toward the player
        if not hasattr(self.game, 'player'):
            return
        direction = (self.game.player.pos - self.pos)
        if direction.length() == 0:
            direction = vec(1, 0)
        EnemyBullet(self.game, vec(self.pos), direction.normalize())

    def _draw_healthbar(self):
        # render a small health bar above the enemy onto the image
        try:
            bar_w = TILESIZE - 6
            bar_h = 6
            hp_ratio = max(0, min(1, self.health / max(1, self.max_health)))
            bar_surf = pg.Surface((bar_w, bar_h), pg.SRCALPHA)
            # background
            pg.draw.rect(bar_surf, (30, 30, 30), (0, 0, bar_w, bar_h), border_radius=3)
            # fill
            pg.draw.rect(bar_surf, (200, 60, 60), (1, 1, int((bar_w - 2) * hp_ratio), bar_h - 2), border_radius=2)
            # blit onto a copy of base frame
            base = self.standing_frames[self.current_frame].copy()
            base.blit(bar_surf, (3, 2))
            self.image = base
        except Exception:
            pass


class EnemyBullet(Sprite):
    def __init__(self, game, pos, direction):
        self.groups = game.all_sprites, getattr(game, 'all_enemy_bullets', pg.sprite.Group())
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((6, 6), pg.SRCALPHA)
        pg.draw.circle(self.image, (255, 160, 120), (3, 3), 3)
        self.pos = vec(pos)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.vel = vec(direction).normalize() * 360

    def update(self):
        self.pos += self.vel * self.game.dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        # kill when offscreen
        if not (0 <= self.rect.x <= WIDTH and 0 <= self.rect.y <= HEIGHT):
            self.kill()


class Floor(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_floors
        Sprite.__init__(self, self.groups)
        self.game = game
        # mark as non-collidable surface for movement checks
        self.is_floor = True
        self.image = pg.Surface((TILESIZE, TILESIZE))
        # subtle floor pattern
        self.image.fill((30, 30, 50))
        for i in range(0, TILESIZE, 8):
            pg.draw.line(self.image, (24, 24, 36), (i, 0), (i, TILESIZE), 1)
        self.rect = self.image.get_rect(topleft=(x * TILESIZE, y * TILESIZE))


class Trap(Sprite):
    def __init__(self, game, x, y, damage=10):
        self.groups = game.all_sprites, getattr(game, 'all_traps', pg.sprite.Group())
        Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill((100, 10, 10))
        # visual hazard
        pg.draw.rect(self.image, (220, 80, 80), (4, 4, TILESIZE - 8, TILESIZE - 8), 2)
        self.rect = self.image.get_rect(topleft=(x * TILESIZE, y * TILESIZE))
        self.pos = vec(x * TILESIZE + TILESIZE / 2, y * TILESIZE + TILESIZE / 2)
        self.damage = damage

    def update(self):
        # damage player on overlap
        if hasattr(self.game, 'player'):
            if self.rect.colliderect(self.game.player.hit_rect):
                self.game.player.take_damage(self.damage)
                # optional: deactivate trap after triggered
                self.kill()
        

#Door calls simple Open/Close state that enables us to open and close / enter
class Door(ParentState):
    def __init__(self, game, x, y, door_type=None):
        self.groups = game.all_sprites
        super().__init__(self.groups)
        self.game = game
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "door_animation.png"))
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image = self.spritesheet.get_image(0, 0, TILESIZE/2, TILESIZE)
        self.load_images()
        self.rect = self.image.get_rect()
        self.open_door = False
        self.current_door_state = 0
        # position in pixels
        self.pos = vec(x * TILESIZE, y * TILESIZE)
        # record the door's type so the game can map it to a boss level
        self.door_type = door_type

        self.update_state(DoorClosedState)
        

    def load_images(self):
        self.door_states = [self.spritesheet.get_image(0, 0, TILESIZE/2, TILESIZE), 
                                self.spritesheet.get_image(TILESIZE/2, 0, TILESIZE/2, TILESIZE)]
        for frame in self.door_states:
            frame.set_colorkey(BLACK)


    def update(self):
        self.rect.center = self.pos
        if hasattr(self.game, 'player'):
            self.open_door = collide_hit_rect(self.game.player, self)
        super().update()



#Simple coin animation (needs to be implemented to map still)
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

#Bullet class which can be iterated as we append through space trigger
class Bullet(Sprite):
    def __init__(self, game, pos, direction):
        # add to main sprite groups
        self.groups = game.all_sprites, game.all_bullets
        Sprite.__init__(self, self.groups)
        self.game = game
        # Try to create a projectile image from the player's sprite for animation
        self.image = None
        try:
            if hasattr(game, 'player') and getattr(game.player, 'image', None) is not None:
                # scale down player's current frame to make a bullet frame
                base = pg.transform.smoothscale(game.player.image, (10, 10)).convert_alpha()
                # tint to blue for Megaman-style projectile
                tint = pg.Surface(base.get_size(), pg.SRCALPHA)
                tint.fill((80, 160, 255, 180))
                base.blit(tint, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
                self.image = base
        except Exception:
            self.image = None

        # Fallback: simple blue circle if we couldn't make a sprite-based bullet
        if self.image is None:
            self.image = pg.Surface((8, 8), pg.SRCALPHA)
            pg.draw.circle(self.image, (80, 160, 255), (4, 4), 4)
        self.rect = self.image.get_rect()
        # position as vector for smooth movement
        self.pos = vec(pos)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # ensure direction is a Vector2 and normalized
        direction = vec(direction)
        if direction.length() != 0:
            self.vel = direction.normalize() * 600
        else:
            self.vel = vec(1, 0) * 600

    def update(self):
        # move according to delta-time from the game loop
        self.pos += self.vel * self.game.dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        # Kill if it leaves the visible area
        if not (0 <= self.rect.x <= WIDTH and 0 <= self.rect.y <= HEIGHT):
            self.kill()

#Blocks for bounds of map (useful and can be adjusted for custom animation)
class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill((60, 60, 80)) # Dark blue-grey "brick" color
        self.rect = self.image.get_rect(topleft=(x*TILESIZE, y*TILESIZE))