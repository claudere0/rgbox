from .settings import *
from .sprites import Sprite, ColorStation
from .player import Player
from .groups import AllSprites

class Level:
    def __init__(self, tmx_map):
        self.display_surface = pygame.display.get_surface()

        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.semicollidable_sprites = pygame.sprite.Group()
        self.hazard_sprites = pygame.sprite.Group() # dead if collide
        self.trigger_sprites = pygame.sprite.Group() # check for overlapping

        self.setup(tmx_map)

    def setup(self, tmx_map):
        for x, y, surf in tmx_map.get_layer_by_name('terrain').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, self.collision_sprites)

        for obj in tmx_map.get_layer_by_name('objects'):
            if obj.name == 'box':
                self.player = Player((obj.x, obj.y), (obj.width, obj.height), self.collision_sprites, self.semicollidable_sprites, self.all_sprites)
                self.bg_color = WHITE if not any(self.player.pigments.values()) else BLACK
            elif obj.name == 'color_station':
                ColorStation((obj.x, obj.y), (obj.width, obj.height), obj.properties, self.trigger_sprites, self.all_sprites, self.collision_sprites)


    def update(self, dt):
        self.all_sprites.update(dt)

    def draw(self, screen):
        screen.fill(self.bg_color)
        self.all_sprites.draw(self.player.rect.center)