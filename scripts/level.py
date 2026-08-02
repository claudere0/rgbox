from .settings import *
from .sprites import Sprite

class Level:
    def __init__(self, tmx_map):
        self.display_surface = pygame.display.get_surface()

        self.all_sprites = pygame.sprite.Group()

        self.setup(tmx_map)

    def setup(self, tmx_map):
        for x, y, surf in tmx_map.get_layer_by_name('map').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites)

        for obj in tmx_map.get_layer_by_name('objects'):
            if obj.name == 'box':
                print(obj.x, obj.y)

    def run(self):
        self.display_surface.fill(BLACK) 
        self.all_sprites.draw(self.display_surface)