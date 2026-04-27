import pygame as pg 
from pygame.sprite import Sprite
from sprites import *

#State machine logic: allows us to call ParentState and switch
#between other objects and classes like MovingState, OpenState, etc.

def shoot_bullet(self):
    now = pg.time.get_ticks()
    if now - self.owner.last_update > 50:
        self.owner.last_update = now
        self.owner.current_frame = (self.owner.current_frame + 1) % len(self.owner.shooting_frames)
        frame = self.owner.shooting_frames[self.owner.current_frame]
        if self.owner.direction_facing == 'left':
            frame = pg.transform.flip(frame, True, False)
        bottom = self.owner.rect.bottom
        self.owner.image = frame
        self.owner.rect = self.owner.image.get_rect()
        self.owner.rect.bottom = bottom
"""
MVE_LIST = {
    "Shoot": {
        "logic":shoot_bullet(),
        "total frames":7
    },
}
"""

class Character:
    def __init__(self, game):
        self.game = game
        self.last_update = 0
        self.current_frame = 0
    def use_state(self, index_num):
        if index_num < len(MVE_LIST):
            mve_start = MVE_LIST[index_num]
            print("Currently at "+mve_start+" state")

    


def collide_hit_rect(one, two):
    # Floors should not block movement — skip collision if either side is a floor
    if getattr(one, 'is_floor', False) or getattr(two, 'is_floor', False):
        return False
    return one.hit_rect.colliderect(two.rect)

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
            
            
            self.owner.current_frame = (self.owner.current_frame + 1) % len(self.owner.standing_frames)

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
            
            print("Walking left")
            
            
            self.owner.current_frame = (self.owner.current_frame + 1) % len(self.owner.standing_frames)

            # Update the actual image
            bottom = self.owner.rect.bottom
            self.owner.image = pg.transform.flip(self.owner.standing_frames[self.owner.current_frame], True, False)
            self.owner.rect = self.owner.image.get_rect()
            self.owner.rect.bottom = bottom

        
class IdleState(State):
    def update(self):   
        # Update the actual image
        bottom = self.owner.rect.bottom
        self.owner.image = self.owner.spritesheet.get_image(139.5, 132, TILESIZE, TILESIZE)
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


            
class ShootingState(State):

    def update(self):
        now = pg.time.get_ticks()
        if now - self.owner.last_update > 50:
            self.owner.last_update = now
            self.owner.current_frame = (self.owner.current_frame + 1) % len(self.owner.shooting_frames)
            frame = self.owner.shooting_frames[self.owner.current_frame]
            if self.owner.direction_facing == 'left':
                frame = pg.transform.flip(frame, True, False)
            bottom = self.owner.rect.bottom
            self.owner.image = frame
            self.owner.rect = self.owner.image.get_rect()
            self.owner.rect.bottom = bottom