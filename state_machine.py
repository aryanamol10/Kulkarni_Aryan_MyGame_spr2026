import pygame as pg
from pygame.sprite import Sprite
from sprites import *
from settings import *
from utils import *
from os import path
from main import *


# ─── Frame data ───────────────────────────────────────────────────────────────
# Each entry holds everything a state needs: which spritesheet slice,
# how many frames, and the delay between them.
# Add new attacks/animations here — no new class required.

class Animations():
    def __init__(self, game):
        self.game = game
    def idle_player_animations(self):

        self.idle_spritesheet = Spritesheet(path.join(self.game.img_dir, "door_animation.png"))
        
        self.idle_frames = self.idle_spritesheet.get_image(0, 0, WIDTH, HEIGHT)

        return self.idle_frames


FRAME_DATA = {
    "idle":        {"frames": Animations.idle_player_animations(Game), "delay": 0},
    "walk_right":  {"frames": None, "delay": 50},
    "walk_left":   {"frames": None, "delay": 50},
    "shoot":       {"frames": None, "delay": 50},
    "coin_spin":   {"frames": None, "delay": 350},
    "door_open":   {"frames": None, "delay": 0},
    "door_closed": {"frames": None, "delay": 0},
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def collide_hit_rect(one, two):
    if getattr(one, 'is_floor', False) or getattr(two, 'is_floor', False):
        return False
    return one.hit_rect.colliderect(two.rect)


# ─── Base State ───────────────────────────────────────────────────────────────

class State:
    key = "idle"   # subclasses override this to match their FRAME_DATA key

    def __init__(self, owner):
        self.owner  = owner
        cfg         = FRAME_DATA.get(self.key, {})
        self.frames = cfg.get("frames")
        self.delay  = cfg.get("delay", 50)

    def enter(self):  pass
    def update(self): pass
    def exit(self):
        try:
            if self.owner.direcion == "right":
                self.owner.update_state("walk_right")
            elif self.owner.direction == "left":
                self.owner.update_state("walk_left")
        except Exception:
            pass

    # Shared helper — advances the frame strip, optionally flipping horizontally
    def _advance_frame(self, frames, flip_h=False):
        now = pg.time.get_ticks()
        if now - self.owner.last_update > self.delay:
            self.owner.last_update   = now
            self.owner.current_frame = (self.owner.current_frame + 1) % len(frames)
            bottom = self.owner.rect.bottom
            frame  = frames[self.owner.current_frame]
            if flip_h:
                frame = pg.transform.flip(frame, True, False)
            self.owner.image = frame
            self.owner.rect  = self.owner.image.get_rect()
            self.owner.rect.bottom = bottom


# ─── Concrete states ──────────────────────────────────────────────────────────

class WalkingRightState(State):
    key = "walk_right"
    def update(self):
        self._advance_frame(self.frames or self.owner.standing_frames)


class WalkingLeftState(State):
    key = "walk_left"
    def update(self):
        self._advance_frame(self.frames or self.owner.standing_frames, flip_h=True)


class IdleState(State):
    key = "idle"
    def update(self):
        bottom           = self.owner.rect.bottom
        self.owner.image = self.owner.spritesheet.get_image(139.5, 132, TILESIZE, TILESIZE)
        self.owner.rect  = self.owner.image.get_rect()
        self.owner.rect.bottom = bottom


class ShootingState(State):
    key = "shoot"
    def update(self):
        flip = (self.owner.direction_facing == 'left')
        self._advance_frame(self.frames or self.owner.shooting_frames, flip_h=flip)


class CoinSpinState(State):
    key = "coin_spin"
    def update(self):
        self._advance_frame(self.frames or self.owner.standing_frames)


class DoorClosedState(State):
    key = "door_closed"
    def enter(self):
        self.owner.image = self.owner.door_states[0]
    def update(self):
        if collide_hit_rect(self.owner.game.player, self.owner):
            self.owner.update_state("door_open")


class DoorOpenState(State):
    key = "door_open"
    def enter(self):
        self.owner.image = self.owner.door_states[1]
        try:
            match self.owner.door_type:
                case "A": self.owner.game.current_level = "Boss_1"
                case "B": self.owner.game.current_level = "Boss_2"
                case "C": self.owner.game.current_level = "Boss_3"
                case "D": self.owner.game.current_level = "Boss_4"
            self.owner.game.new()
        except Exception:
            pass
    def update(self):
        if not collide_hit_rect(self.owner.game.player, self.owner):
            self.owner.update_state("door_closed")


# ─── Registry ─────────────────────────────────────────────────────────────────
# Maps string keys to state classes.
# To add a state: write the class above, add one line here.

STATE_REGISTRY = {
    "idle":        IdleState,
    "walk_right":  WalkingRightState,
    "walk_left":   WalkingLeftState,
    "shoot":       ShootingState,
    "coin_spin":   CoinSpinState,
    "door_open":   DoorOpenState,
    "door_closed": DoorClosedState,
}


# ─── ParentState ──────────────────────────────────────────────────────────────

class ParentState(Sprite):
    """
    Base sprite with a built-in state machine.
    Transition to any state with:  self.update_state("shoot")
    No class imports needed in sprites.py.
    """
    def __init__(self, groups):
        super().__init__(groups)
        self.state         = None
        self.last_update   = 0
        self.current_frame = 0

    def update_state(self, key: str):
        cls = STATE_REGISTRY.get(key)
        if cls is None:
            raise KeyError(f"Unknown state '{key}'. Add it to STATE_REGISTRY.")
        if self.state:
            self.state.exit()
        self.state = cls(self)
        self.state.enter()

    def update(self):
        if self.state:
            self.state.update()


# ─── How to instantiate in your sprite class ──────────────────────────────────
#
# Pattern is always the same three steps:
#   1. super().__init__(groups)     — init Sprite + state machine
#   2. Build frames, load images    — your existing spritesheet code
#   3. Populate FRAME_DATA          — point each key at your frame lists
#   4. update_state("idle")         — machine starts running
#
# After that, call update_state("walk_right") from input / collision / AI.

class Player(ParentState):
    def __init__(self, game, x, y, groups):
        super().__init__(groups)                   # step 1
        self.game             = game
        self.direction_facing = "right"

        # step 2 — build frame lists from your spritesheet as normal
        self.spritesheet     = Spritesheet(path.join(self.game.img_dir, "Player_Sprite.png"))
        self.standing_frames = [
            self.spritesheet.get_image(0,  0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(48, 0, TILESIZE, TILESIZE),
            # … rest of walk strip
        ]
        self.shooting_frames = [
            self.spritesheet.get_image(0,  48, TILESIZE, TILESIZE),
            self.spritesheet.get_image(48, 48, TILESIZE, TILESIZE),
            # … rest of shoot strip
        ]

        # step 3 — hand the frames to FRAME_DATA so states can read them
        FRAME_DATA["walk_right"]["frames"] = self.standing_frames
        FRAME_DATA["walk_left"]["frames"]  = self.standing_frames  # flipped in state
        FRAME_DATA["shoot"]["frames"]      = self.shooting_frames

        # step 4 — start the machine
        self.image    = self.standing_frames[0]
        self.rect     = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.hit_rect = self.rect.copy()
        self.update_state("idle")

    def handle_input(self):
        keys = pg.key.get_pressed()
        if keys[pg.K_RIGHT]:
            self.direction_facing = "right"
            self.update_state("walk_right")    # string key — no class needed
        elif keys[pg.K_LEFT]:
            self.direction_facing = "left"
            self.update_state("walk_left")
        elif keys[pg.K_SPACE]:
            self.update_state("shoot")
        else:
            self.update_state("idle")

    def update(self):
        self.handle_input()
        super().update()                       # delegates to self.state.update()


class Coin(ParentState):
    def __init__(self, game, x, y, groups):
        super().__init__(groups)
        self.game = game

        self.spritesheet     = Spritesheet(path.join(self.game.img_dir, "coin_sprite_sheet.png"))
        self.standing_frames = [
            self.spritesheet.get_image(0,  0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(16, 0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(32, 0, TILESIZE, TILESIZE),
            self.spritesheet.get_image(48, 0, TILESIZE, TILESIZE),
        ]
        FRAME_DATA["coin_spin"]["frames"] = self.standing_frames

        self.image = self.standing_frames[0]
        self.rect  = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.update_state("coin_spin")         # coins spin from the start


class Door(ParentState):
    def __init__(self, game, x, y, door_type, groups):
        super().__init__(groups)
        self.game      = game
        self.door_type = door_type

        sheet            = Spritesheet(path.join(self.game.img_dir, "door_animation.png"))
        self.door_states = [
            sheet.get_image(0,  0, TILESIZE, TILESIZE * 2),   # [0] = closed
            sheet.get_image(16, 0, TILESIZE, TILESIZE * 2),   # [1] = open
        ]
        self.image    = self.door_states[0]
        self.rect     = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.hit_rect = self.rect.copy()
        self.update_state("door_closed")       # doors always start closed