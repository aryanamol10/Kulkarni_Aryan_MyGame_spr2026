import pygame as pg
from pygame.sprite import Sprite
from settings import TILESIZE


# ─── Frame data ───────────────────────────────────────────────────────────────
# Each entry holds everything a state needs: which spritesheet slice,
# how many frames, and the delay between them.
# Add new attacks/animations here — no new class required.



FRAME_DATA = {
    "idle":        {"frames": None, "delay": 0},
    "walk_right":  {"frames": None, "delay": 50},
    "walk_left":   {"frames": None, "delay": 50},
    "shoot":       {"frames": None, "delay": 50},
    "coin_spin":   {"frames": None, "delay": 350},
    "door_open":   {"frames": None, "delay": 0},
    "door_closed": {"frames": None, "delay": 0},
    "door_opening": {"frames": None, "delay": 100},
    "door_closing": {"frames": None, "delay": 100},
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
            if getattr(self.owner, 'direction_facing', None) == "right":
                self.owner.update_state("walk_right")
            elif getattr(self.owner, 'direction_facing', None) == "left":
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
    def enter(self):
        self.owner.current_frame = 0
        self.owner.last_update = pg.time.get_ticks()
        if hasattr(self.owner, 'standing_frames') and self.owner.standing_frames:
            self.owner.image = self.owner.standing_frames[0]
            self.owner.rect = self.owner.image.get_rect()

    def update(self):
        if hasattr(self.owner, 'standing_frames') and self.owner.standing_frames:
            bottom = self.owner.rect.bottom
            self.owner.image = self.owner.standing_frames[0]
            self.owner.rect = self.owner.image.get_rect()
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
        self.owner.current_frame = 0
        self.owner.last_update = pg.time.get_ticks()
        self.owner.image = self.owner.door_closed_frames[0]
        self.owner.rect = self.owner.image.get_rect()
        self.owner.transitioned = False

    def update(self):
        if hasattr(self.owner.game, 'player') and collide_hit_rect(self.owner.game.player, self.owner):
            self.owner.update_state("door_opening")


class DoorOpeningState(State):
    key = "door_opening"
    def __init__(self, owner):
        super().__init__(owner)
        self.all_frames = owner.door_opening_frames + owner.door_open_frames
        self.delay = 100
    
    def enter(self):
        self.owner.current_frame = 0
        self.owner.last_update = pg.time.get_ticks()
        self.owner.animation_complete = False
        self.owner.transitioned = False

    def update(self):
        now = pg.time.get_ticks()
        if now - self.owner.last_update > self.delay:
            self.owner.last_update = now
            self.owner.current_frame += 1
            
            if self.owner.current_frame < len(self.all_frames):
                self.owner.image = self.all_frames[self.owner.current_frame]
                self.owner.rect = self.owner.image.get_rect()
            else:
                self.owner.animation_complete = True
                self.owner.current_frame = len(self.all_frames) - 1
                self.owner.image = self.all_frames[-1]
                self.owner.rect = self.owner.image.get_rect()
                
                if not self.owner.transitioned:
                    self.owner.transitioned = True
                    self._transition_to_boss()
        
        if hasattr(self.owner.game, 'player') and not collide_hit_rect(self.owner.game.player, self.owner):
            if self.owner.animation_complete:
                self.owner.update_state("door_closing")
    
    def _transition_to_boss(self):
        if self.owner.door_type in ['A', 'B', 'C', 'D']:
            boss_map = {'A': 'Boss_1', 'B': 'Boss_2', 'C': 'Boss_3', 'D': 'Boss_4'}
            self.owner.game.current_level = boss_map[self.owner.door_type]
            self.owner.game.new()


class DoorClosingState(State):
    key = "door_closing"
    def __init__(self, owner):
        super().__init__(owner)
        self.all_frames = owner.door_closing_frames
        self.delay = 100
    
    def enter(self):
        self.owner.current_frame = 0
        self.owner.last_update = pg.time.get_ticks()
        self.owner.animation_complete = False

    def update(self):
        now = pg.time.get_ticks()
        if now - self.owner.last_update > self.delay:
            self.owner.last_update = now
            self.owner.current_frame += 1
            
            if self.owner.current_frame < len(self.all_frames):
                self.owner.image = self.all_frames[self.owner.current_frame]
                self.owner.rect = self.owner.image.get_rect()
            else:
                self.owner.update_state("door_closed")


class DoorOpenState(State):
    key = "door_open"
    def enter(self):
        self.owner.current_frame = 0
        self.owner.last_update = pg.time.get_ticks()
        if self.frames:
            self.owner.image = self.frames[0]
            self.owner.rect = self.owner.image.get_rect()

    def update(self):
        self._advance_frame(self.frames or getattr(self.owner, 'door_open_frames', [self.owner.image]))
        if not hasattr(self.owner.game, 'player') or not collide_hit_rect(self.owner.game.player, self.owner):
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
    "door_opening": DoorOpeningState,
    "door_closing": DoorClosingState,
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
