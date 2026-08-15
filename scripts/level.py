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
        if any(self.player.pigments.values()):
            self.bg_color = BLACK
        else:
            self.bg_color = WHITE

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
                        station.draw_station()

                    elif self.player.pigments[color_key] and not station.station_colors[color_key]:
                        self.player.pigments[color_key] = False
                        station.station_colors[color_key] = True
                        
                        self.player.jump = True
                        self.player.update_color_and_size()
                        station.draw_station()

    def draw(self, screen):
        screen.fill(self.bg_color)
        self.all_sprites.draw(self.player.rect.center)