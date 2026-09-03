from .settings import *

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = Vector2(0,0)

    def draw(self, target_pos):
        self.offset.x = -(target_pos[0] - WINDOW_WIDTH / 2)
        self.offset.y = -(target_pos[1] - WINDOW_HEIGHT / 2)
        for sprite in sorted(self.sprites(), key=lambda sprite: getattr(sprite, 'z', 1)):
            if hasattr(sprite, 'display_rect'):
                offset_pos = sprite.display_rect.topleft + self.offset
            else:
                offset_pos = sprite.rect.topleft + self.offset
            self.display_surface.blit(sprite.image, offset_pos)
