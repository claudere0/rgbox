from .settings import *
from .sprites import Sprite, ColorStation
from .player import Player
from .groups import AllSprites
from os.path import join

class Level:
    def __init__(self, tmx_map):
        self.display_surface = pygame.display.get_surface()

        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.terrain_sprites = pygame.sprite.Group()
        self.semicollidable_sprites = pygame.sprite.Group()
        self.hazard_sprites = pygame.sprite.Group() # dead if collide
        self.trigger_sprites = pygame.sprite.Group() # check for overlapping

        self.setup(tmx_map)

    def setup(self, tmx_map):
        tileset_img = pygame.image.load(join('graphics', 'tilesets', 'demo_tiles.png')).convert_alpha()

        self.black_tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.black_tile_image.blit(tileset_img, (0, 0), (0, 0, TILE_SIZE, TILE_SIZE))

        self.white_tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.white_tile_image.blit(tileset_img, (0, 0), (7 * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE))

        for x, y, surf in tmx_map.get_layer_by_name('terrain').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, self.collision_sprites, self.terrain_sprites)

        for obj in tmx_map.get_layer_by_name('objects'):
            if obj.name == 'box':
                self.player = Player((obj.x, obj.y), (obj.width, obj.height), self.collision_sprites, self.semicollidable_sprites, self.all_sprites)
                self.bg_color = WHITE if not any(self.player.pigments.values()) else BLACK
            elif obj.name == 'color_station':
                ColorStation((obj.x, obj.y), (obj.width, obj.height), obj.properties, self.trigger_sprites, self.all_sprites, self.collision_sprites)

        self.update_stantions_to_fit_world()

    def update(self, dt):
        self.all_sprites.update(dt)
        self.update_colors(dt)

    def update_colors(self, dt):
        just_pressed = pygame.key.get_just_pressed()
        if just_pressed[pygame.K_e]:
            for station in self.trigger_sprites:
                if self.player.rect.move(0, 16).colliderect(station.rect):

                    dx = self.player.rect.centerx - station.rect.left
                    slot_width = station.rect.width / 3
                    
                    if dx < slot_width:
                        color_key = 'R'
                    elif dx < slot_width * 2:
                        color_key = 'G'
                    else:
                        color_key = 'B'

                    if not self.player.pigments[color_key] and station.station_colors[color_key]:
                        self.player.pigments[color_key] = True
                        station.station_colors[color_key] = False

                        self.player.jump = True
                        self.player.update_color_and_size()
                        self.update_stantions_to_fit_world()

                    elif self.player.pigments[color_key] and not station.station_colors[color_key]:
                        self.player.pigments[color_key] = False
                        station.station_colors[color_key] = True

                        self.player.jump = True
                        self.player.update_color_and_size()
                        self.update_stantions_to_fit_world()

    def update_stantions_to_fit_world(self):
        has_colors = any(self.player.pigments.values())
        for st in self.trigger_sprites:
            if isinstance(st, ColorStation):
                st.draw_station(has_colors)

    def draw(self, screen):
        has_colors = any(self.player.pigments.values())
        if has_colors:
            bg_color = BLACK
            target_texture = self.white_tile_image
        else:
            bg_color = WHITE
            target_texture = self.black_tile_image

        screen.fill(bg_color)

        for tile in self.terrain_sprites:
            tile.image = target_texture

        self.all_sprites.draw(self.player.rect.center)
