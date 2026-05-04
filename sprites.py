import pygame as pg
from pygame.sprite import Sprite
from settings import *
from state_machine import FRAME_DATA, ParentState
from utils import *
from os import path
import math

vec = pg.math.Vector2

def collide_hit_rect(one, two):
    if getattr(one, 'is_floor', False) or getattr(two, 'is_floor', False):
        return False
    return one.hit_rect.colliderect(two.rect)

def collide_with_walls(sprite, group, dir):
    if dir == 'x':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            if hits[0].rect.centerx > sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.left - (sprite.hit_rect.width/2)
            if hits[0].rect.centerx < sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.right + (sprite.hit_rect.width/2)
            sprite.vel.x = 0
            sprite.hit_rect.centerx = sprite.pos.x
    if dir == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            if hits[0].rect.centery >= sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.height/2
            if hits[0].rect.centery <= sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_rect.height/2
            sprite.vel.y = 0
            sprite.hit_rect.centery = sprite.pos.y


class Player(ParentState):
    def __init__(self, game, x, y, groups=None):
        self.groups = groups if groups is not None else game.all_sprites
        super().__init__(self.groups)
        self.game = game
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "Player_Sprite.png"))
        self.spritesheet2 = Spritesheet(path.join(self.game.img_dir, "megaman_shoot_sheet.png"))
        self.load_images()

        self.vel = vec(0, 0)
        self.pos = vec(x, y) * TILESIZE
        self.acceleration = vec(0, 0)
        self.trace_bullet = []
        self.shoot_cooldown = 0
        self.hit_rect = PLAYER_HIT_RECT.copy()
        self.direction_facing = "right"
        self.last_update = 0
        self.current_frame = 0
        self.health = 100

        FRAME_DATA["walk_right"]["frames"] = self.standing_frames
        FRAME_DATA["walk_left"]["frames"]  = self.standing_frames
        FRAME_DATA["shoot"]["frames"]      = self.shooting_frames

        self.image = self.standing_frames[0]
        self.rect = self.image.get_rect()
        self.rect.topleft = (x * TILESIZE, y * TILESIZE)
        self.hit_rect = self.rect.copy()
        self.update_state("idle")

    def load_images(self):
        W = TILESIZE
        H = TILESIZE
        self.standing_frames = [
            self.spritesheet.get_image(W*0, 0, W, H),
            self.spritesheet.get_image(W*1, 0, W, H),
            self.spritesheet.get_image(W*2, 0, W, H),
            self.spritesheet.get_image(W*3, 0, W, H),
            self.spritesheet.get_image(W*4, 0, W, H),
            self.spritesheet.get_image(W*5, 0, W, H),
            self.spritesheet.get_image(W*6, 0, W, H),
            self.spritesheet.get_image(W*7, 0, W, H),
            self.spritesheet.get_image(W*8, 0, W, H),
            self.spritesheet.get_image(W*9, 0, W, H),
        ]
        self.shooting_frames = [
            self.spritesheet2.get_image(0, H*0, W, H),
            self.spritesheet2.get_image(0, H*1, W, H),
            self.spritesheet2.get_image(0, H*2, W, H),
            self.spritesheet2.get_image(0, H*3, W, H),
            self.spritesheet2.get_image(0, H*4, W, H),
            self.spritesheet2.get_image(0, H*5, W, H),
            self.spritesheet2.get_image(0, H*6, W, H),
            self.spritesheet2.get_image(0, H*7, W, H),
        ]
        for frame in self.standing_frames + self.shooting_frames:
            frame.set_colorkey(BLACK)

    def attack(self):
        if self.shoot_cooldown <= 0:
            self.shoot()
            self.shoot_cooldown = 15
            self.update_state("shoot")

    def shoot(self):
        dir_vec = vec(-1, 0) if self.direction_facing == 'left' else vec(1, 0)
        head_offset = vec(0, -TILESIZE * 0.25)
        spawn_pos = self.pos + dir_vec * (TILESIZE // 2) + head_offset
        try:
            spark = pg.Surface((6, 6), pg.SRCALPHA)
            pg.draw.circle(spark, (180, 220, 255), (3, 3), 3)
            if hasattr(self.game, 'camera'):
                self.game.screen.blit(spark, self.game.camera.apply(self).move(0, -TILESIZE//4))
        except Exception:
            pass
        Bullet(self.game, spawn_pos, dir_vec)

    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0:
            self.health = 0
        print(f"Player health: {self.health}")

    def bounce_back(self):
        self.vel *= -0.5

    def change_dir(self, direction):
        from state_machine import ShootingState
        if isinstance(self.state, ShootingState):
            return
        try:
            if direction == "right":
                self.update_state("walk_right")
            elif direction == "left":
                self.update_state("walk_left")
        except Exception:
            pass

    def handle_input(self):
        pressed_keys = pg.key.get_pressed()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        moving = False
        self.acceleration.x = 0
        self.acceleration.y = 0

        if pressed_keys[pg.K_LEFT] or pressed_keys[pg.K_a]:
            self.acceleration.x = -PLAYER_ACCEL
            self.direction_facing = "left"
            self.update_state("walk_left")
            moving = True
        elif pressed_keys[pg.K_RIGHT] or pressed_keys[pg.K_d]:
            self.acceleration.x = PLAYER_ACCEL
            self.direction_facing = "right"
            self.update_state("walk_right")
            moving = True

        if pressed_keys[pg.K_UP] or pressed_keys[pg.K_w]:
            self.acceleration.y = -PLAYER_ACCEL
            moving = True
        if pressed_keys[pg.K_DOWN] or pressed_keys[pg.K_s]:
            self.acceleration.y = PLAYER_ACCEL
            moving = True

        if not moving:
            self.update_state("idle")

    def update(self):
        self.handle_input()
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


def check_shooting_state(shoot_state, trace_bullet, game, pos, direction):
    if shoot_state:
        b = Bullet(game, pos, direction)
        trace_bullet.append(b)
        try:
            game.all_bullets.add(b)
        except Exception:
            pass


class Enemy(Sprite):
    def __init__(self, game, col, row, enemy_type):
        self.groups = game.all_sprites, game.all_bosses
        Sprite.__init__(self, self.groups)
        self.game = game
        self.type = enemy_type

        self.pos = vec(col * TILESIZE + TILESIZE / 2, row * TILESIZE + TILESIZE / 2)
        self.rect = pg.Rect(0, 0, TILESIZE, TILESIZE)
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.hit_rect = ENEMY_HIT_RECT.copy()
        self.hit_rect.center = self.pos

        template = {
            'A': {'health': 180, 'speed': 90,  'color': (200, 50,  50),  'ranged': False, 'zigzag': False, 'turret': False},
            'B': {'health': 120, 'speed': 60,  'color': (40,  120, 200), 'ranged': True,  'shoot_delay': 1200},
            'C': {'health': 140, 'speed': 80,  'color': (140, 60,  180), 'zigzag': True},
            'D': {'health': 260, 'speed': 40,  'color': (200, 160, 40),  'ranged': True,  'turret': True, 'shoot_delay': 900},
            'E': {'health': 32,  'speed': 140, 'color': (200, 90,  140), 'ranged': False},
        }
        stats = template.get(enemy_type, template['E'])
        self.health      = stats['health']
        self.max_health  = self.health
        self.speed       = stats.get('speed', 80)
        self.color       = stats.get('color', RED)
        self.ranged      = stats.get('ranged', False)
        self.zigzag      = stats.get('zigzag', False)
        self.turret      = stats.get('turret', False)
        self.shoot_delay = stats.get('shoot_delay', 1000)

        self.standing_frames = self._make_frames()
        self.current_frame = 0
        self.last_update   = 0
        self.image = self.standing_frames[0]
        self.rect  = self.image.get_rect()
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        self.vel = vec(0, 0)
        self.last_shot = 0

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()
        print(f"Enemy {self.type} hit! Health: {self.health}")

    def _make_frames(self):
        frames = []
        for i in range(4):
            surf = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA)
            surf.fill((0, 0, 0, 0))
            shade = tuple(max(0, min(255, c + i * 8 - 8)) for c in self.color)
            pg.draw.circle(surf, shade, (TILESIZE // 2, TILESIZE // 2), TILESIZE // 2 - 2)
            eye_x = 9 if i % 2 == 0 else 11
            pg.draw.circle(surf, (255, 255, 255), (TILESIZE // 2 - eye_x, TILESIZE // 2 - 6), 3)
            pg.draw.circle(surf, (255, 255, 255), (TILESIZE // 2 + eye_x, TILESIZE // 2 - 6), 3)
            frames.append(surf)
        return frames

    def update(self):
        now = pg.time.get_ticks()
        if now - self.last_update > 140:
            self.last_update   = now
            self.current_frame = (self.current_frame + 1) % len(self.standing_frames)
            self.image = self.standing_frames[self.current_frame]

        if not hasattr(self.game, 'player'):
            return

        dir_vec = self.game.player.pos - self.pos
        dist = dir_vec.length()
        direction = dir_vec.normalize() if dist > 0 else vec(0, 0)

        if self.turret:
            self.vel = vec(0, 0)
        else:
            if self.zigzag and dist > 8:
                perp   = vec(-direction.y, direction.x)
                offset = math.sin(pg.time.get_ticks() / 220.0) * 0.5
                move   = (direction + perp * offset)
                if move.length() > 0:
                    move = move.normalize()
                self.vel = move * self.speed
            else:
                self.vel = direction * self.speed
            self.pos += self.vel * self.game.dt

        self.rect.center     = (int(self.pos.x), int(self.pos.y))
        self.hit_rect.center = self.pos

        collide_with_walls(self, self.game.all_walls, 'x')
        collide_with_walls(self, self.game.all_walls, 'y')

        if (self.ranged or self.turret) and dist < 800:
            if now - self.last_shot > self.shoot_delay:
                self.last_shot = now
                self.shoot_at_player()

        self._draw_healthbar()

    def shoot_at_player(self):
        if not hasattr(self.game, 'player'):
            return
        direction = self.game.player.pos - self.pos
        if direction.length() == 0:
            direction = vec(1, 0)
        EnemyBullet(self.game, vec(self.pos), direction.normalize())

    def _draw_healthbar(self):
        try:
            bar_w    = TILESIZE - 6
            bar_h    = 6
            hp_ratio = max(0, min(1, self.health / max(1, self.max_health)))
            bar_surf = pg.Surface((bar_w, bar_h), pg.SRCALPHA)
            pg.draw.rect(bar_surf, (30,  30,  30),  (0, 0, bar_w, bar_h), border_radius=3)
            pg.draw.rect(bar_surf, (200, 60,  60),  (1, 1, int((bar_w - 2) * hp_ratio), bar_h - 2), border_radius=2)
            base = self.standing_frames[self.current_frame].copy()
            base.blit(bar_surf, (3, 2))
            self.image = base
        except Exception:
            pass


class EnemyBullet(Sprite):
    def __init__(self, game, pos, direction):
        self.groups = game.all_sprites, getattr(game, 'all_enemy_bullets', pg.sprite.Group())
        Sprite.__init__(self, self.groups)
        self.game  = game
        self.image = pg.Surface((6, 6), pg.SRCALPHA)
        pg.draw.circle(self.image, (255, 160, 120), (3, 3), 3)
        self.pos  = vec(pos)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.vel  = vec(direction).normalize() * 360

    def update(self):
        self.pos += self.vel * self.game.dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if not (0 <= self.rect.x <= WIDTH and 0 <= self.rect.y <= HEIGHT):
            self.kill()


class Floor(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_floors
        Sprite.__init__(self, self.groups)
        self.is_floor = True
        self.image    = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill((30, 30, 50))
        for i in range(0, TILESIZE, 8):
            pg.draw.line(self.image, (24, 24, 36), (i, 0), (i, TILESIZE), 1)
        self.rect = self.image.get_rect(topleft=(x * TILESIZE, y * TILESIZE))


class Trap(Sprite):
    def __init__(self, game, x, y, damage=10):
        self.groups = game.all_sprites, getattr(game, 'all_traps', pg.sprite.Group())
        Sprite.__init__(self, self.groups)
        self.game   = game
        self.image  = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill((100, 10, 10))
        pg.draw.rect(self.image, (220, 80, 80), (4, 4, TILESIZE - 8, TILESIZE - 8), 2)
        self.rect   = self.image.get_rect(topleft=(x * TILESIZE, y * TILESIZE))
        self.pos    = vec(x * TILESIZE + TILESIZE / 2, y * TILESIZE + TILESIZE / 2)
        self.damage = damage

    def update(self):
        if hasattr(self.game, 'player'):
            if self.rect.colliderect(self.game.player.hit_rect):
                self.game.player.take_damage(self.damage)
                self.kill()


class Door(ParentState):
    def __init__(self, game, x, y, door_type=None, groups=None):
        self.groups = groups if groups is not None else game.all_sprites
        super().__init__(self.groups)
        self.game      = game
        self.door_type = door_type
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "door_animation.png"))
        self.load_images()

        self.image = self.door_closed_frames[0]
        self.rect  = self.image.get_rect()
        self.pos   = vec(x * TILESIZE, y * TILESIZE)
        self.rect.center = (int(self.pos.x) + TILESIZE // 2, int(self.pos.y) + TILESIZE // 2)
        self.hit_rect  = self.rect.copy()
        self.open_door = False
        self.animation_complete = False
        self.transitioned = False

        self.update_state("door_closed")

    def load_images(self):
        # Load all 10 frames from the 640x64 spritesheet
        self.door_closed_frames = [
            self.spritesheet.get_image(0, 0, TILESIZE, TILESIZE),
        ]
        self.door_opening_frames = [
            self.spritesheet.get_image(64, 0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(128, 0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(192, 0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(256, 0, TILESIZE, TILESIZE),
        ]
        self.door_open_frames = [
            self.spritesheet.get_image(320, 0, TILESIZE, TILESIZE),
        ]
        self.door_closing_frames = [
            self.spritesheet.get_image(384, 0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(448, 0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(512, 0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(576, 0, TILESIZE, TILESIZE),
        ]
        all_frames = self.door_closed_frames + self.door_opening_frames + self.door_open_frames + self.door_closing_frames
        for frame in all_frames:
            frame.set_colorkey(BLACK)

    def update(self):
        self.rect.center = (int(self.pos.x) + TILESIZE // 2, int(self.pos.y) + TILESIZE // 2)
        self.hit_rect = self.rect.copy()
        if hasattr(self.game, 'player'):
            self.open_door = collide_hit_rect(self.game.player, self)
        super().update()


class Coin(ParentState):
    def __init__(self, game, x, y, groups=None):
        self.groups = groups if groups is not None else game.all_sprites
        super().__init__(self.groups)
        self.game = game
        self.spritesheet = Spritesheet(path.join(self.game.img_dir, "coin_sprite_sheet.png"))
        self.load_images()

        self.vel  = vec(0, 0)
        self.pos  = vec(x, y) * TILESIZE
        self.last_update   = 0
        self.current_frame = 0

        FRAME_DATA["coin_spin"]["frames"] = self.standing_frames

        self.image = self.standing_frames[0]
        self.rect  = self.image.get_rect()
        self.rect.center = self.pos
        self.update_state("coin_spin")

    def load_images(self):
        self.standing_frames = [
            self.spritesheet.get_image(0,          0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(TILESIZE,   0, TILESIZE, TILESIZE),
        ]
        self.moving_frames = [
            self.spritesheet.get_image(TILESIZE*2, 0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(TILESIZE*3, 0, TILESIZE, TILESIZE),
        ]
        for frame in self.standing_frames:
            frame.set_colorkey(BLACK)


class Bullet(Sprite):
    def __init__(self, game, pos, direction):
        self.groups = game.all_sprites, game.all_bullets
        Sprite.__init__(self, self.groups)
        self.game  = game
        self.image = None
        try:
            if hasattr(game, 'player') and getattr(game.player, 'image', None) is not None:
                base = pg.transform.smoothscale(game.player.image, (10, 10)).convert_alpha()
                tint = pg.Surface(base.get_size(), pg.SRCALPHA)
                tint.fill((80, 160, 255, 180))
                base.blit(tint, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
                self.image = base
        except Exception:
            self.image = None

        if self.image is None:
            self.image = pg.Surface((8, 8), pg.SRCALPHA)
            pg.draw.circle(self.image, (80, 160, 255), (4, 4), 4)

        self.rect = self.image.get_rect()
        self.pos  = vec(pos)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        direction = vec(direction)
        self.vel  = direction.normalize() * 600 if direction.length() != 0 else vec(1, 0) * 600

    def update(self):
        self.pos += self.vel * self.game.dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        if not (0 <= self.rect.x <= WIDTH and 0 <= self.rect.y <= HEIGHT):
            self.kill()


class Wall(Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.all_walls
        Sprite.__init__(self, self.groups)
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill((60, 60, 80))
        self.rect  = self.image.get_rect(topleft=(x * TILESIZE, y * TILESIZE))