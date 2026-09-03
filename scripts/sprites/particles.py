import pygame
from .base import Sprite
from ..settings import *

class TextSprite(Sprite):
    def __init__(self, pos, text_string, font_size, *groups):
        font = pygame.font.SysFont('courier', font_size, bold=True)
        lines = text_string.split('\n')

        def render_text_block(color):
            rendered_lines = [font.render(line, True, color) for line in lines]

            if not rendered_lines:
                return pygame.Surface((1, 1), pygame.SRCALPHA)

            width = max(surf.get_width() for surf in rendered_lines)
            height = sum(surf.get_height() for surf in rendered_lines)

            final_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            current_y = 0
            for line_surf in rendered_lines:
                final_surf.blit(line_surf, (0, current_y))
                current_y += line_surf.get_height()
            return final_surf

        self.white_surf = render_text_block((255, 255, 255))
        self.black_surf = render_text_block((0, 0, 0))

        super().__init__(pos, self.white_surf, *groups)

class DustParticle(Sprite):
    def __init__(self, pos, color, velocity, lifetime, *groups):
        super().__init__(pos, pygame.Surface((8, 8)), *groups)
        self.size = 8
        self.image.fill(color)
        self.rect = self.image.get_frect(center=pos)
        
        self.pos = Vector2(pos)
        self.velocity = Vector2(velocity)
        self.gravity = 1431 # particle gravity
        
        self.start_time = pygame.time.get_ticks()
        self.lifetime = lifetime
        self.color = color

    def update(self, dt):
        self.velocity.y += self.gravity * dt
        self.pos += self.velocity * dt
        self.rect.center = self.pos
        
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed > self.lifetime:
            self.kill()
        else:
            progress = elapsed / self.lifetime
            current_size = max(1, int(self.size * (1 - progress)))
            self.image = pygame.Surface((current_size, current_size))
            self.image.fill(self.color)
            self.rect = self.image.get_frect(center=self.pos)

class TrailParticle(Sprite):
    def __init__(self, pos, surf, lifetime, *groups):
        super().__init__(pos, surf.copy(), *groups)
        self.original_image = surf.copy()
        self.rect = self.image.get_frect(topleft=pos)
        
        self.start_time = pygame.time.get_ticks()
        self.lifetime = lifetime
        
    def update(self, dt):
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed > self.lifetime:
            self.kill()
        else:
            progress = elapsed / self.lifetime
            alpha = int(255 * (1 - progress))
            
            self.image = self.original_image.copy()
            self.image.set_alpha(alpha)
