import pygame, math
from .base import Sprite
from ..settings import *

class Collectible(Sprite):
    def __init__(self, pos, surf, *groups):
        super().__init__(pos, surf, *groups)
        self.base_y = self.rect.y
        self.float_speed = 0.005
        self.float_amplitude = 16

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        self.rect.y = self.base_y + math.sin(current_time * self.float_speed) * self.float_amplitude

class CameoSprite(Collectible):
    def __init__(self, pos, secret_id, surf, bonus_ms, *groups):
        self.secret_id = secret_id
        self.bonus_ms = bonus_ms
        super().__init__(pos, surf, *groups)

class TimeBonusSprite(Collectible):
    def __init__(self, pos, black_surf, white_surf, bonus_ms, *groups):
        self.black_surf = black_surf
        self.white_surf = white_surf
        self.bonus_ms = bonus_ms
        super().__init__(pos, self.black_surf, *groups)
