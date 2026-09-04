import pygame, math
from .base import Sprite
from ..timer import Timer
from ..settings import *

class ColorStation(Sprite):
    _tileset = None

    def __init__(self, pos, size, properties, *groups):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        super().__init__(pos, surf, *groups)

        self.station_colors = {
            'R': properties.get('has_red', False),
            'G': properties.get('has_green', False),
            'B': properties.get('has_blue', False)
        }

        if ColorStation._tileset is None:
            from os.path import join
            ColorStation._tileset = pygame.image.load(join('graphics', 'tilesets', 'demo_tiles.png')).convert_alpha()

        self.textures = {
            'empty_R':  ColorStation._tileset.subsurface(pygame.Rect(64,  320, 64, 32)),
            'empty_G':  ColorStation._tileset.subsurface(pygame.Rect(128, 320, 64, 32)),
            'empty_B':  ColorStation._tileset.subsurface(pygame.Rect(192, 320, 64, 32)),
            
            'filled_R': ColorStation._tileset.subsurface(pygame.Rect(64,  352, 64, 32)),
            'filled_G': ColorStation._tileset.subsurface(pygame.Rect(128, 352, 64, 32)),
            'filled_B': ColorStation._tileset.subsurface(pygame.Rect(192, 352, 64, 32))
        }

    def draw_station(self, player_has_colors):
        self.image.fill((0, 0, 0, 0))

        img_r = self.textures['filled_R'] if self.station_colors['R'] else self.textures['empty_R']
        self.image.blit(img_r, (0, 0))

        img_g = self.textures['filled_G'] if self.station_colors['G'] else self.textures['empty_G']
        self.image.blit(img_g, (64, 0))

        img_b = self.textures['filled_B'] if self.station_colors['B'] else self.textures['empty_B']
        self.image.blit(img_b, (128, 0))

class ColorDoor(Sprite):
    COLOR_MAP = {
        'K': {'R': False, 'G': False, 'B': False}, # Black
        'R': {'R': True,  'G': False, 'B': False}, # Red
        'G': {'R': False, 'G': True,  'B': False}, # Green
        'B': {'R': False, 'G': False, 'B': True},  # Blue
        'Y': {'R': True,  'G': True,  'B': False}, # Yellow (Red + Green)
        'C': {'R': False, 'G': True,  'B': True},  # Cyan (Green + Blue)
        'M': {'R': True,  'G': False, 'B': True},  # Magenta (Red + Blue)
        'W': {'R': True,  'G': True,  'B': True},  # White (All colors)
    }

    def __init__(self, pos, surf, color_code, *groups):
        super().__init__(pos, surf, *groups)
        self.req_pigments = self.COLOR_MAP.get(color_code, self.COLOR_MAP['K'])

    def is_passable(self, player_pigments):
        return player_pigments == self.req_pigments


class Portal(Sprite):
    def __init__(self, pos, size, *groups):
        surf = pygame.Surface(size, pygame.SRCALPHA) 
        super().__init__(pos, surf, *groups)

        self.orientation = 'H' if size[0] > size[1] else 'V'


class JumpPad(Sprite):
    def __init__(self, pos, size, power, *groups):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        
        super().__init__(pos, surf, *groups)
        self.power = power

        self.rect.bottom = pos[1] + size[1]

class FallingPlatform(Sprite):
    def __init__(self, pos, size, player, collision_sprites, *groups):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        super().__init__(pos, surf, *groups)

        self.player = player
        self.collision_group = collision_sprites
        self.collision_group.add(self)

        self.base_pos = pos
        self.shake_amount = 4
        self.state = 'IDLE'

        base_crumble_time = 500

        if size[0] >= 256:
            crumble_time = int(base_crumble_time * 2)

        elif size[0] >= 192:
            crumble_time = int(base_crumble_time * 1.5)

        else:
            crumble_time = base_crumble_time

        self.timers = {
            'crumble': Timer(crumble_time),
            'respawn': Timer(2000)
        }

    def reset(self):
        self.state = 'IDLE'
        self.timers['crumble'].deactivate()
        self.timers['respawn'].deactivate()
        self.collision_group.add(self)
        self.rect.topleft = self.base_pos

    def update(self, dt):
        self.old_rect = self.rect.copy()
        for timer in self.timers.values():
            timer.update()

        if self.state == 'IDLE':
            if self.rect.inflate(0, 16).colliderect(self.player.rect):
                if self.player.rect.bottom <= self.rect.top + 8:
                    self.state = 'SHAKING'
                    self.timers['crumble'].activate()

        elif self.state == 'SHAKING':
            if not self.timers['crumble'].active:
                self.state = 'BROKEN'
                self.timers['respawn'].activate()
                self.collision_group.remove(self) 

        elif self.state == 'BROKEN':
            if not self.timers['respawn'].active:
                self.state = 'IDLE'
                self.collision_group.add(self)

    def update_visuals(self, has_colors):
        if self.state == 'BROKEN':
            self.image.set_alpha(0)
            return

        self.image.set_alpha(255)
        base_color = pygame.Color(255, 255, 255) if has_colors else pygame.Color(0, 0, 0)
        
        if self.state == 'SHAKING':
            elapsed = pygame.time.get_ticks() - self.timers['crumble'].start_time
            progress = min(elapsed / self.timers['crumble'].duration, 1.0)

            target_color = pygame.Color(255, 255, 0)
            current_color = base_color.lerp(target_color, progress)
            self.image.fill(current_color)

            offset = math.sin(pygame.time.get_ticks() * 0.05) * self.shake_amount
            self.rect.x = self.base_pos[0] + offset

        else:
            self.image.fill(base_color)
            self.rect.x = self.base_pos[0]

class TimerButton(Sprite):
    def __init__(self, pos, size, target_id, timer_ms, *groups):
        surf = pygame.Surface(size)
        surf.fill((255, 0, 0))
        super().__init__(pos, surf, *groups)

        self.base_rect = self.rect.copy()
        self.target_id = target_id
        self.target_laser = None

        from ..timer import Timer
        self.timer = Timer(timer_ms)
        self.pressed = False

    def press(self):
        if not self.pressed:
            self.pressed = True
            self.timer.activate()

            self.image = pygame.Surface((self.base_rect.width, 16))
            self.image.fill((0, 255, 0)) 
            self.rect = self.image.get_frect()
            self.rect.bottomleft = self.base_rect.bottomleft

            if self.target_laser:
                self.target_laser.active = False

    def update(self, dt):
        self.timer.update()

        if self.timer.active:
            elapsed = pygame.time.get_ticks() - self.timer.start_time
            progress = min(elapsed / self.timer.duration, 1.0)

            current_color = pygame.Color(0, 255, 0).lerp(pygame.Color(255, 0, 0), progress)
            self.image.fill(current_color)
        else:
            if self.pressed:
                self.pressed = False
                self.image = pygame.Surface(self.base_rect.size)
                self.image.fill((255, 0, 0))
                self.rect = self.base_rect.copy()

                if self.target_laser:
                    self.target_laser.active = True
