import pygame
from .base import Sprite
from ..settings import *

class Spike(Sprite):
    def __init__(self, pos, surf, *groups):
        super().__init__(pos, surf, *groups)
        self.rect.bottom = pos[1] + TILE_SIZE
        self.old_rect = self.rect.copy()

class Laser(Sprite):
    def __init__(self, start_pos, size, move_axis, move_dist, speed, *groups):
        surf = pygame.Surface(size)
        surf.fill((255, 0, 0))
        super().__init__(start_pos, surf, *groups)

        self.start_pos = start_pos
        if move_axis == 'x':
            self.end_pos = (start_pos[0] + move_dist, start_pos[1])
        else:
            self.end_pos = (start_pos[0], start_pos[1] + move_dist)

        self.move_axis = move_axis
        self.speed = speed
        self.direction = 1
        self.active = True

    def update(self, dt):
        self.old_rect = self.rect.copy()
        self.image.set_alpha(255 if self.active else 63)

        if self.speed > 0:
            if self.move_axis == 'x':
                self.rect.x += self.speed * self.direction * dt
                if self.rect.x >= self.end_pos[0] and self.direction == 1:
                    self.direction = -1
                elif self.rect.x <= self.start_pos[0] and self.direction == -1:
                    self.direction = 1
            else:
                self.rect.y += self.speed * self.direction * dt
                if self.rect.y >= self.end_pos[1] and self.direction == 1:
                    self.direction = -1
                elif self.rect.y <= self.start_pos[1] and self.direction == -1:
                    self.direction = 1
