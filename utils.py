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
        # Typewriter reveal state
        self._char_index = 0
        self._last_char_time = 0
        self._char_delay = 25  # ms per character

    def show(self, pages):
        if isinstance(pages, str):
            pages = [pages]
        self.pages = pages
        self.page_index = 0
        # reset typing state
        self._char_index = 0
        self._last_char_time = pg.time.get_ticks()
        self.active = True

    def next(self):
        # If page still typing, skip to full page first
        page = self.pages[self.page_index]
        if self._char_index < len(page):
            self._char_index = len(page)
            return

        self.page_index += 1
        if self.page_index >= len(self.pages):
            self.close()
            return
        # reset typing for next page
        self._char_index = 0
        self._last_char_time = pg.time.get_ticks()

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
        # Retro-style panel with shadow, border, icon, scanlines and blinking prompt
        now = pg.time.get_ticks()
        box_w, box_h = self.width, self.height
        page = self.pages[self.page_index]

        # Draw shadow behind the panel directly to screen
        shadow_surf = pg.Surface((box_w, box_h), pg.SRCALPHA)
        pg.draw.rect(shadow_surf, (0, 0, 0, 160), shadow_surf.get_rect(), border_radius=12)
        self.game.screen.blit(shadow_surf, (self.box_rect.left + 6, self.box_rect.top + 6))

        # Panel surface
        panel = pg.Surface((box_w, box_h), pg.SRCALPHA)

        # Gradient fill (top -> bottom)
        top = (28, 28, 48)
        bot = (8, 8, 20)
        for i in range(box_h):
            t = i / max(1, box_h)
            r = int(top[0] * (1 - t) + bot[0] * t)
            g = int(top[1] * (1 - t) + bot[1] * t)
            b = int(top[2] * (1 - t) + bot[2] * t)
            pg.draw.line(panel, (r, g, b, 220), (0, i), (box_w, i))

        # Subtle inner overlay for depth
        inner = pg.Surface((box_w - 8, box_h - 8), pg.SRCALPHA)
        inner.fill((0, 0, 0, 30))
        panel.blit(inner, (4, 4))

        # Scanline / CRT hint
        for y_line in range(0, box_h, 4):
            pg.draw.line(panel, (255, 255, 255, 6), (0, y_line), (box_w, y_line))

        # Decorative pixel icon on the left
        icon_size = 48
        icon_x = self.PADDING
        icon_y = self.PADDING
        icon_rect = pg.Rect(icon_x, icon_y, icon_size, icon_size)
        pg.draw.rect(panel, (30, 120, 200), icon_rect, border_radius=6)
        # small pixel pattern inside icon
        sub = icon_size // 4
        for px in range(4):
            for py in range(4):
                col = (180 - px * 20, 220 - py * 18, 140 + px * 8)
                r = pg.Rect(icon_x + px * sub + 2, icon_y + py * sub + 2, sub - 3, sub - 3)
                pg.draw.rect(panel, col, r)

        # Choose a pixel-y font when available
        font_candidates = ['pressstart2p', 'arcadeclassic', 'minecraftia', 'couriernew', 'arial']
        chosen = None
        for name in font_candidates:
            fpath = pg.font.match_font(name)
            if fpath:
                chosen = fpath
                break
        if chosen:
            font = pg.font.Font(chosen, self.font_size)
            hint_font = pg.font.Font(chosen, 16)
            dot_font = pg.font.Font(chosen, 14)
        else:
            font = pg.font.Font(self.font_name, self.font_size)
            hint_font = pg.font.Font(self.font_name, 16)
            dot_font = pg.font.Font(self.font_name, 14)

        # advance typewriter index based on time
        while self._char_index < len(page) and now - self._last_char_time >= self._char_delay:
            self._char_index += 1
            self._last_char_time += self._char_delay

        display_text = page[:self._char_index]

        # compute text area (account for icon)
        text_x = self.PADDING + icon_size + self.PADDING
        max_w = box_w - text_x - self.PADDING
        lines = self._wrap_text(display_text, font, max_w)

        # render lines with shadow + outline for readability
        y = self.PADDING
        for line in lines:
            # shadow
            shadow = font.render(line, True, (0, 0, 0))
            panel.blit(shadow, (text_x + 2, y + 2))
            # outline (simple 4-way)
            outline = font.render(line, True, (40, 40, 50))
            panel.blit(outline, (text_x - 1, y))
            panel.blit(outline, (text_x + 1, y))
            panel.blit(outline, (text_x, y - 1))
            panel.blit(outline, (text_x, y + 1))
            # main text
            txt = font.render(line, True, self.text_color)
            panel.blit(txt, (text_x, y))
            y += txt.get_height() + 6

        # Page indicators (centered)
        if len(self.pages) > 1:
            dots = ' '.join('●' if i == self.page_index else '○' for i in range(len(self.pages)))
            dots_s = dot_font.render(dots, True, self.hint_color)
            panel.blit(dots_s, ((box_w - dots_s.get_width()) // 2, box_h - dots_s.get_height() - 12))

        # Blinking action prompt when page fully revealed
        blink = (now // 500) % 2 == 0
        if self._char_index >= len(page) and blink:
            hint = "PRESS [SPACE]"
            hint_s = hint_font.render(hint, True, self.hint_color)
            hint_box_w = hint_s.get_width() + 12
            hint_box_h = hint_s.get_height() + 8
            hint_rect = pg.Rect(box_w - hint_box_w - self.PADDING, box_h - hint_box_h - self.PADDING, hint_box_w, hint_box_h)
            # hint background and border
            pg.draw.rect(panel, (20, 30, 40, 220), hint_rect, border_radius=8)
            pg.draw.rect(panel, (160, 200, 255, 200), hint_rect, 2, border_radius=8)
            panel.blit(hint_s, (hint_rect.left + 6, hint_rect.top + 4))
        elif self._char_index < len(page):
            # typing dots animation while typing
            dots_count = ((now // 250) % 4)
            dots = '.' * dots_count
            ts = hint_font.render(dots, True, self.hint_color)
            panel.blit(ts, (text_x, box_h - ts.get_height() - 12))

        # Outer border glow
        pg.draw.rect(panel, (80, 160, 220, 120), panel.get_rect(), 2, border_radius=10)

        # Blit panel onto the game screen at the designated box location
        self.game.screen.blit(panel, self.box_rect.topleft)


    