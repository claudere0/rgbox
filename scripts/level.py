from .settings import *
from .sprites import *
from .player import Player, PlayerStateID
from .groups import AllSprites
from os.path import join

class Level:
    def __init__(self, tmx_map, playing_state):
        self.playing_state = playing_state
        self.display_surface = pygame.display.get_surface()

        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.terrain_sprites = pygame.sprite.Group()
        self.hazard_sprites = pygame.sprite.Group()
        self.trigger_sprites = pygame.sprite.Group()
        self.falling_sprites = pygame.sprite.Group()
        self.collectible_sprites = pygame.sprite.Group()

        self.is_completed = False

        self.setup(tmx_map)

    def setup(self, tmx_map):
        self.map_height = tmx_map.height * TILE_SIZE 

        tileset_img = pygame.image.load(join('graphics', 'tilesets', 'demo_tiles.png')).convert_alpha()

        self.black_tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.black_tile_image.blit(tileset_img, (0, 0), (0, 0, TILE_SIZE, TILE_SIZE))

        self.white_tile_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.white_tile_image.blit(tileset_img, (0, 0), (7 * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE))

        self.black_spike_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.black_spike_image.blit(tileset_img, (0, 0), (4 * TILE_SIZE, 5 * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        self.white_spike_image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.white_spike_image.blit(tileset_img, (0, 0), (5 * TILE_SIZE, 5 * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        self.portal_vert_white = pygame.Surface((TILE_SIZE, TILE_SIZE * 2), pygame.SRCALPHA)
        self.portal_vert_white.blit(tileset_img, (0, 0), (4 * TILE_SIZE, 6 * TILE_SIZE, TILE_SIZE, TILE_SIZE * 2))

        self.portal_vert_black = pygame.Surface((TILE_SIZE, TILE_SIZE * 2), pygame.SRCALPHA)
        self.portal_vert_black.blit(tileset_img, (0, 0), (5 * TILE_SIZE, 6 * TILE_SIZE, TILE_SIZE, TILE_SIZE * 2))

        self.portal_horiz_white = pygame.Surface((TILE_SIZE * 2, TILE_SIZE), pygame.SRCALPHA)
        self.portal_horiz_white.blit(tileset_img, (0, 0), (6 * TILE_SIZE, 6 * TILE_SIZE, TILE_SIZE * 2, TILE_SIZE))

        self.portal_horiz_black = pygame.Surface((TILE_SIZE * 2, TILE_SIZE), pygame.SRCALPHA)
        self.portal_horiz_black.blit(tileset_img, (0, 0), (6 * TILE_SIZE, 7 * TILE_SIZE, TILE_SIZE * 2, TILE_SIZE))

        self.jumppad_black = pygame.Surface((TILE_SIZE * 2, TILE_SIZE), pygame.SRCALPHA)
        self.jumppad_black.blit(tileset_img, (0, 0), (0, 7 * TILE_SIZE, TILE_SIZE * 2, TILE_SIZE))

        self.jumppad_white = pygame.Surface((TILE_SIZE * 2, TILE_SIZE), pygame.SRCALPHA)
        self.jumppad_white.blit(tileset_img, (0, 0), (2 * TILE_SIZE, 7 * TILE_SIZE, TILE_SIZE * 2, TILE_SIZE))

        self.time_bonus_surfaces = []
        for i in range(4):
            black_surf = pygame.Surface((128, 128), pygame.SRCALPHA)
            black_surf.blit(tileset_img, (0, 0), (i * 128, 512, 128, 128))

            white_surf = pygame.Surface((128, 128), pygame.SRCALPHA)
            white_surf.blit(tileset_img, (0, 0), (i * 128, 640, 128, 128))

            self.time_bonus_surfaces.append({'black': black_surf, 'white': white_surf})
            
        self.cameo_surfaces = []
        for i in range(4):
            cameo_surf = pygame.Surface((128, 128), pygame.SRCALPHA)
            cameo_surf.blit(tileset_img, (0, 0), (i * 128, 768, 128, 128))
            self.cameo_surfaces.append(cameo_surf)

        for x, y, surf in tmx_map.get_layer_by_name('terrain').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, self.collision_sprites, self.terrain_sprites)

        is_minimalist = self.playing_state.game.save_manager.data["settings"].get("minimalist", False)

        if 'terrain_colored' in [layer.name for layer in tmx_map.layers]:
            for x, y, surf in tmx_map.get_layer_by_name('terrain_colored').tiles():
                if is_minimalist:
                    Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, self.collision_sprites, self.terrain_sprites)

                else:
                    Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, self.all_sprites, self.collision_sprites)

        lasers_dict = {} 

        for obj in tmx_map.get_layer_by_name('objects'):
            if obj.name == 'box':
                self.player = Player((obj.x, obj.y), (obj.width, obj.height), self.collision_sprites, self.playing_state.game.audio, self.all_sprites)
                self.bg_color = WHITE if not any(self.player.pigments.values()) else BLACK

                self.start_pos = (obj.x, obj.y)
                self.start_pigments = self.player.pigments.copy()

            elif obj.name == 'color_station':
                ColorStation((obj.x, obj.y), (obj.width, obj.height), obj.properties, self.trigger_sprites, self.all_sprites, self.collision_sprites)

            elif obj.name == 'color_door':
                color_code = obj.properties.get('color', 'K') # K by default if I forget to add
                ColorDoor((obj.x, obj.y), obj.image, color_code, self.all_sprites, self.collision_sprites)

            elif obj.name == 'portal':
                Portal((obj.x, obj.y), (obj.width, obj.height), self.trigger_sprites, self.all_sprites)

            elif obj.name == 'jumppad':
                power = obj.properties.get('power', 2024) # 1432 -> 400 px (6.25 tiles) and 2024 -> 800px (12.5 tiles)
                JumpPad((obj.x, obj.y), (obj.width, obj.height), power, self.trigger_sprites, self.all_sprites)

            elif obj.name == 'falling_platform':
                FallingPlatform((obj.x, obj.y), (obj.width, obj.height), self.player, self.collision_sprites, self.falling_sprites, self.all_sprites)

            elif obj.name == 'laser':
                move_axis = obj.properties.get('move_axis', 'y')
                move_dist = obj.properties.get('move_dist', 0)
                speed = obj.properties.get('speed', 0)
                laser = Laser((obj.x, obj.y), (obj.width, obj.height), move_axis, move_dist, speed, self.all_sprites, self.hazard_sprites)
                lasers_dict[obj.id] = laser

            elif obj.name == 'button':
                target_id = obj.properties.get('target_id', None)
                timer_ms = obj.properties.get('timer', 4000) # По умолчанию 4 секунды
                button = TimerButton((obj.x, obj.y), (obj.width, obj.height), target_id, timer_ms, self.all_sprites, self.trigger_sprites)

            elif obj.name == 'text':
                text_content = obj.properties.get('text', 'EMPTY')
                font_size = obj.properties.get('font_size', 24)
                
                TextSprite((obj.x, obj.y), text_content, int(font_size), self.all_sprites)

            elif obj.name == 'secret':
                secret_id = int(obj.properties.get('secret_id', 0))

                bonus_ms = (secret_id + 1) * 5000 

                if self.playing_state.game.save_manager.has_secret(secret_id):
                    surfs = self.time_bonus_surfaces[secret_id]
                    TimeBonusSprite((obj.x, obj.y), surfs['black'], surfs['white'], bonus_ms, self.collectible_sprites, self.all_sprites)
                else:
                    surf = self.cameo_surfaces[secret_id]
                    CameoSprite((obj.x, obj.y), secret_id, surf, bonus_ms, self.collectible_sprites, self.all_sprites)

        for sprite in self.trigger_sprites:
            if isinstance(sprite, TimerButton):
                if sprite.target_id in lasers_dict:
                    sprite.target_laser = lasers_dict[sprite.target_id]

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

        for platform in self.falling_sprites:
            platform.reset()

        for sprite in self.trigger_sprites:
            if isinstance(sprite, TimerButton) and sprite.pressed:
                sprite.timer.deactivate()
                sprite.pressed = False
                sprite.image = pygame.Surface(sprite.base_rect.size)
                sprite.image.fill((255, 0, 0))
                sprite.rect = sprite.base_rect.copy()
        for sprite in self.hazard_sprites:
            if isinstance(sprite, Laser):
                sprite.active = True
                sprite.rect.topleft = sprite.start_pos
                sprite.direction = 1

        self.update_stantions_to_fit_world()
        self.player.change_state(PlayerStateID.IDLE)

    def update(self, dt):
        self.all_sprites.update(dt)
        self.update_colors(dt)
        self.check_hazards()

        if self.player.needs_respawn:
            self.reset_level()

        for trigger in self.trigger_sprites:
            if isinstance(trigger, Portal):
                if self.player.rect.colliderect(trigger.rect.inflate(-16, -16)):
                    if not self.is_completed:
                        self.playing_state.game.audio.play_sfx('portal')
                        self.is_completed = True


            elif isinstance(trigger, JumpPad):
                if self.player.rect.colliderect(trigger.rect):
                    if self.player.direction.y >= 0:
                        self.player.direction.y = -trigger.power
                        self.player.change_state(PlayerStateID.JUMP)

                        self.player.can_dash = self.player.pigments['R']
                        self.player.can_double_jump = self.player.pigments['G']

            elif isinstance(trigger, TimerButton):
                if self.player.rect.colliderect(trigger.rect.inflate(8, 8)):
                    if not trigger.pressed:
                        self.playing_state.game.audio.play_sfx('secret')
                    trigger.press()

        for item in self.collectible_sprites:
            if self.player.rect.colliderect(item.rect):
                self.playing_state.game.audio.play_sfx('secret')
                if isinstance(item, CameoSprite):
                    self.playing_state.game.save_manager.unlock_secret(item.secret_id)

                self.playing_state.start_time += item.bonus_ms

                current_time = pygame.time.get_ticks()
                if current_time - self.playing_state.start_time < 0:
                    self.playing_state.start_time = current_time # make it 00:00:00 prevent time to be negative or 59:59:99

                item.kill()

    def check_hazards(self):
        if self.player.current_state != self.player.states[PlayerStateID.DEATH]:
            for hazard in self.hazard_sprites:
                if isinstance(hazard, Laser) and not hazard.active:
                    continue

                if self.player.rect.colliderect(hazard.rect):
                    self.player.change_state(PlayerStateID.DEATH)
                    break

            if self.player.rect.top > self.map_height:
                self.player.change_state(PlayerStateID.DEATH)

    def update_colors(self, dt):
        just_pressed = pygame.key.get_just_pressed()
        if just_pressed[pygame.K_e]:
            for station in self.trigger_sprites:
                if isinstance(station, ColorStation):
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
                            self.player.audio.play_sfx('color') 
                            self.player.pigments[color_key] = True
                            station.station_colors[color_key] = False

                            self.player.direction.y = -716 # half jump 1012 / square root of 2
                            self.player.scale_x = 0.75
                            self.player.scale_y = 1.25
                            self.player.rect.bottom -= 1

                            self.player.change_state(PlayerStateID.JUMP)

                            self.player.update_color_and_size()
                            self.update_stantions_to_fit_world()

                        elif self.player.pigments[color_key] and not station.station_colors[color_key]:
                            self.player.audio.play_sfx('color') 
                            self.player.pigments[color_key] = False
                            station.station_colors[color_key] = True

                            self.player.direction.y = -716 # half jump 1012 / square root of 2
                            self.player.scale_x = 0.75
                            self.player.scale_y = 1.25
                            self.player.rect.bottom -= 1

                            self.player.change_state(PlayerStateID.JUMP)

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
            spike_texture = self.white_spike_image
        else:
            bg_color = WHITE
            target_texture = self.black_tile_image
            spike_texture = self.black_spike_image

        screen.fill(bg_color)

        for tile in self.terrain_sprites:
            tile.image = target_texture

        for spike in self.hazard_sprites:
            if isinstance(spike, Spike):
                spike.image = spike_texture

        for platform in self.falling_sprites:
            platform.update_visuals(has_colors)

        for sprite in self.trigger_sprites:
            if isinstance(sprite, Portal):
                if sprite.orientation == 'V':
                    sprite.image = self.portal_vert_white if has_colors else self.portal_vert_black
                else:
                    sprite.image = self.portal_horiz_white if has_colors else self.portal_horiz_black

            elif isinstance(sprite, JumpPad):
                sprite.image = self.jumppad_white if has_colors else self.jumppad_black

        for sprite in self.collectible_sprites:
            if isinstance(sprite, TimeBonusSprite):
                sprite.image = sprite.white_surf if has_colors else sprite.black_surf

        for sprite in self.all_sprites:
            if isinstance(sprite, TextSprite):
                sprite.image = sprite.white_surf if has_colors else sprite.black_surf

        self.all_sprites.draw(self.player.rect.center)
