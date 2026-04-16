import pygame as pgfrom 
from pygame.sprite import Sprite
from sprites import *
from sprites import collide_hit_rect


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


            
class ShootingState(State):
    def enter(self):
        self.owner.current_frame = 0
        self.owner.last_update = pg.time.get_ticks()
        self.owner.shoot_anim_start = self.owner.last_update
        self.owner.image = self.owner.shooting_frames[self.owner.current_frame]
        self.owner.image.set_colorkey(BLACK)
        if self.owner.direction_facing == 'left':
            self.owner.image = pg.transform.flip(self.owner.image, True, False)
        self.owner.rect = self.owner.image.get_rect(center=self.owner.rect.center)

    def update(self):
        now = pg.time.get_ticks()
        if now - self.owner.last_update > 100:
            self.owner.last_update = now
            self.owner.current_frame = (self.owner.current_frame + 1) % len(self.owner.shooting_frames)
            frame = self.owner.shooting_frames[self.owner.current_frame]
            if self.owner.direction_facing == 'left':
                frame = pg.transform.flip(frame, True, False)
            bottom = self.owner.rect.bottom
            self.owner.image = frame
            self.owner.rect = self.owner.image.get_rect()
            self.owner.rect.bottom = bottom

        # short shoot state duration, then return to walk state
        """
        if now - self.owner.shoot_anim_start > 250:
            if self.owner.direction_facing == "left":
                self.owner.update_state(WalkingLeftState)
            else:
                self.owner.update_state(WalkingRightState)

        """