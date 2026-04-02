import pygame as pg
from settings import *

#Our baseline map, using length bounds through set tilemapping
class Map:
    def __init__(self, filename):
        #creating data for building map using list
        self.data = []


        with open(filename, 'rt') as f:
            for line in f:
                self.data.append(line.strip())

        self.tilewidth = len(self.data[0])
        self.tileheight = len(self.data)
        self.width = self.tilewidth * TILESIZE


#Camera POV which is adjusetd based on player pose
class Camera:
    
    def __init__(self, width, height):
        self.camera = pg.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        # Move an entity's rect by the camera offset
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        # Center the camera on target
        x = -target.rect.centerx + int(WIDTH / 2)
        y = -target.rect.centery + int(HEIGHT / 2)

        # Limit scrolling to map boundaries
        x = min(0, x)  # left
        x = max(-(self.width - WIDTH), x)  # right
        y = min(0, y)  # top
        y = max(-(self.height - HEIGHT), y)  # bottom

        self.camera = pg.Rect(x, y, self.width, self.height)


#This spritesheet class allows us to run through sprite animations with ease
#Easy class to instantiate and run through each action
class Spritesheet:
    def __init__(self, filename):
        self.spritesheet = pg.image.load(filename).convert()
    def get_image(self, x, y, width, height):
        image = pg.Surface((width, height))
        image.blit(self.spritesheet, (0,0), (x,y, width, height))
        new_image = pg.transform.scale(image ,(width, height))
        image = new_image
        return image

# this class creates a countdown timer for a cooldown
class Cooldown:
    def __init__(self, time):
        self.start_time = 0
        # allows us to set property for time until cooldown
        self.time = time
        # self.current_time = self.time
    def start(self):
        self.start_time = pg.time.get_ticks()

    def ready(self):
        # sets current time to 
        current_time = pg.time.get_ticks()
        # if the difference between current and start time are greater than self.time
        # return True
        if current_time - self.start_time >= self.time:
            return True
        return False


class NarrativeBox:
    """Simple gamified text box for narrative/dialogue.

    Usage:
      nb = NarrativeBox(game)
      nb.show(["First line...", "Second page..."])
      In the main loop call nb.draw() each frame. Use nb.active to check if it's open.
    """
    PADDING = 12

    def __init__(self, game, width=WIDTH, height=140, font_name=None):
        self.game = game
        self.width = width
        self.height = height
        self.font_name = font_name or pg.font.match_font('arial')
        self.box_rect = pg.Rect(0, HEIGHT - self.height, self.width, self.height)
        self.pages = []
        self.page_index = 0
        self.active = False
        self.text_color = (230, 230, 230)
        self.bg_color = (10, 10, 20, 200)
        self.hint_color = (180, 180, 180)
        self.font_size = 20

    def show(self, pages):
        if isinstance(pages, str):
            pages = [pages]
        self.pages = pages
        self.page_index = 0
        self.active = True

    def next(self):
        self.page_index += 1
        if self.page_index >= len(self.pages):
            self.close()

    def skip(self):
        self.close()

    def close(self):
        self.active = False
        self.pages = []
        self.page_index = 0

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pg.MOUSEBUTTONDOWN or (event.type == pg.KEYDOWN and event.key in (pg.K_RETURN, pg.K_SPACE)):
            self.next()

    def _wrap_text(self, text, font, max_width):
        words = text.split(' ')
        lines = []
        cur = ''
        for w in words:
            test = (cur + ' ' + w).strip()
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def draw(self):
        if not self.active:
            return
        surf = pg.Surface((self.width, self.height), pg.SRCALPHA)
        surf.fill(self.bg_color)

        font = pg.font.Font(self.font_name, self.font_size)
        page = self.pages[self.page_index]
        max_w = self.width - self.PADDING * 2
        lines = self._wrap_text(page, font, max_w)

        y = self.PADDING
        for line in lines:
            txt = font.render(line, True, self.text_color)
            surf.blit(txt, (self.PADDING, y))
            y += txt.get_height() + 4

        hint_font = pg.font.Font(self.font_name, 16)
        hint = "Click / Enter to continue"
        hint_s = hint_font.render(hint, True, self.hint_color)
        surf.blit(hint_s, (self.PADDING, self.height - hint_s.get_height() - 8))

        # draw to game screen
        self.game.screen.blit(surf, self.box_rect)


    