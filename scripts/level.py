from .settings import *
from .sprites import *
from .player import Player, PlayerStateID
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

                self.start_pos = (obj.x, obj.y)
                self.start_pigments = self.player.pigments.copy()

            elif obj.name == 'color_station':
                ColorStation((obj.x, obj.y), (obj.width, obj.height), obj.properties, self.trigger_sprites, self.all_sprites, self.collision_sprites)

        self.start_station_colors = {
            station: station.station_colors.copy() 
            for station in self.trigger_sprites if isinstance(station, ColorStation)
        }

        if 'hazzards' in [layer.name for layer in tmx_map.layers]:
            for x, y, surf in tmx_map.get_layer_by_name('hazzards').tiles():
                Spike((x * TILE_SIZE, y * TILE_SIZE), surf, self.all_sprites, self.hazard_sprites)

        self.update_stantions_to_fit_world()

    def reset_level(self):
        self.player.rect.topleft = self.start_pos
        self.player.direction = Vector2(0, 0)
        self.player.needs_respawn = False

        self.player.pigments = self.start_pigments.copy()
        self.player.update_color_and_size()

        for station, colors in self.start_station_colors.items():
            station.station_colors = colors.copy()

        self.update_stantions_to_fit_world()
        self.player.change_state(PlayerStateID.IDLE)

    def update(self, dt):
        self.all_sprites.update(dt)
        self.update_colors(dt)

        if self.player.needs_respawn:
            self.reset_level()

    def check_hazards(self):
        if self.player.current_state != self.player.states[PlayerStateID.DEATH]:
            if pygame.sprite.spritecollideany(self.player, self.hazard_sprites):
                self.player.change_state(PlayerStateID.DEATH)


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
