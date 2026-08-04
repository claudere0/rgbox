from .settings import *
from .sprites import Sprite, MovingSprite
from .player import Player
from .groups import AllSprites

class Level:
    def __init__(self, tmx_map):
        self.display_surface = pygame.display.get_surface()

        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.semicollidable_sprites = pygame.sprite.Group()

        self.setup(tmx_map)

    def setup(self, tmx_map):
        for x, y, surf in tmx_map.get_layer_by_name('map').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, self.collision_sprites)

        for obj in tmx_map.get_layer_by_name('objects'):
            if obj.name == 'box':
                self.player = Player((obj.x, obj.y), (obj.width, obj.height), self.collision_sprites, self.semicollidable_sprites, self.all_sprites)

        for mov_obj in tmx_map.get_layer_by_name('moving_objects'):
            if mov_obj.name == 'moving_platform_0':
                move_dir = 'x'
                start_pos = (mov_obj.x, mov_obj.y + mov_obj.height / 2)
                end_pos = (mov_obj.x + mov_obj.width, mov_obj.y + mov_obj.height / 2)
            else: 
                move_dir = 'y'
                start_pos = (mov_obj.x + mov_obj.width / 2, mov_obj.y)
                end_pos = (mov_obj.x + mov_obj.width / 2, mov_obj.y + mov_obj.height)
            speed = 100
            MovingSprite(start_pos, end_pos, move_dir, speed, self.all_sprites, self.semicollidable_sprites)

    def update(self, dt):
        self.all_sprites.update(dt)

    def run(self, dt):
        self.display_surface.fill(BLACK)
        self.update(dt)
        self.all_sprites.draw(self.player.rect.center)