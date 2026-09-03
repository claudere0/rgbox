import pygame
import random, math
import json, os
from os.path import join
from enum import Enum, auto
from pygame.math import Vector2
from pygame.time import get_ticks
from pytmx.util_pygame import load_pygame

# settings

UNIT = 8
TILE_SIZE =  8 * UNIT
WINDOW_WIDTH = 15 * TILE_SIZE
WINDOW_HEIGHT = 12 * TILE_SIZE
FPS = 60

BLACK = (0,0,0)
BLUE = (0,0,255)
GREEN = (0,255,0)
CYAN = (0,255,255)
RED = (255,0,0)
MAGENTA = (255,0,255)
YELLOW = (255,255,0)
WHITE = (255,255,255)

LEVEL_ORDER = [
    "tutorial_zero",
    "tutorial_one",
    "level_zero",
    "level_one",
    "level_two",
    "level_three"
]

LEVEL_NAMES = {
    'tutorial_zero': '01: AWAKENING',
    'tutorial_one': '02: THE MIX',
    'level_zero': '03: FREEFALL',
    'level_one': '04: NO TIME TO STOP',
    'level_two': '05: JUMP JUMP DASH',
    'level_three': '06: THE LABIRINTH'
}

# timer

class Timer:
	def __init__(self, duration, func = None, repeat = False):
		self.duration = duration
		self.func = func
		self.start_time = 0
		self.active = False
		self.repeat = repeat

	def activate(self):
		self.active = True
		self.start_time = get_ticks()

	def deactivate(self):
		self.active = False
		self.start_time = 0
		if self.repeat:
			self.activate()

	def update(self):
		current_time = get_ticks()
		if current_time - self.start_time >= self.duration:
			if self.func and self.start_time != 0:
				self.func()
			self.deactivate()

# groups (camera)

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

# save manager

class SaveManager:
    def __init__(self, filepath='data/save.json'):
        self.filepath = filepath
        self.data = self.get_default_data()
        self.load()

    def get_default_data(self):
        return {
            "unlocked_levels": ["tutorial_zero"],
            "best_times": {},
            "secrets_found": [],
            "settings": {
                "music_volume": 50.0,
                "sfx_volume": 50.0,
                "fullscreen": False,
                "minimalist": False
            }
        }

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    saved_data = json.load(f)
                    self.data.update(saved_data)
            except:
                print("Error reading save file. Default settings will be used.")
                self.save()
        else:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self.save()

    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f, indent=4)

    def unlock_level(self, level_name):
        if level_name not in self.data["unlocked_levels"]:
            self.data["unlocked_levels"].append(level_name)
            self.save()

    def is_level_unlocked(self, level_name):
        return level_name in self.data["unlocked_levels"]

    def save_best_time(self, level_name, time_ms):
        current_best = self.data["best_times"].get(level_name, float('inf'))
        if time_ms < current_best:
            self.data["best_times"][level_name] = time_ms
            self.save()
            return True
        return False

    def unlock_secret(self, secret_name):
        if secret_name not in self.data["secrets_found"]:
            self.data["secrets_found"].append(secret_name)
            self.save()

    def has_secret(self, secret_name):
        return secret_name in self.data["secrets_found"]

# audio manager

class AudioManager:
    def __init__(self, game):
        self.game = game
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        
        self.sfx = {}
        self.music_path = join('audio', 'music')
        
        self.sfx_volume = 0.5
        self.music_volume = 0.3
        pygame.mixer.music.set_volume(self.music_volume)
        
        self.load_sfx()

    def load_sfx(self):
        sfx_files = {
            'jump': 'jump.mp3',
            'dash': 'dash.mp3',
            'death': 'death_arcade.wav', # can change to death_bubble.mp3
            'color': 'color_change.mp3',
            'secret': 'secret.wav',
            'portal': 'portal.wav'
            , 'button': 'button_press_unpress.mp3'        }
        
        for name, filename in sfx_files.items():
            path = join('audio', 'sfx', filename)
            if os.path.exists(path):
                self.sfx[name] = pygame.mixer.Sound(path)
            else:
                self.sfx[name] = None
                print(f"Warning: Audio missing -> {path}")

    def play_sfx(self, name):
        if name in self.sfx and self.sfx[name]:
            vol = self.game.save_manager.data["settings"].get("sfx_volume", 100) / 100.0
            self.sfx[name].set_volume(vol)
            self.sfx[name].play()

    def play_music(self, filename, loops=-1, fade_ms=2000):
        path = join(self.music_path, filename)
        if os.path.exists(path):
            pygame.mixer.music.load(path)

            vol = self.game.save_manager.data["settings"].get("music_volume", 100) / 100.0
            pygame.mixer.music.set_volume(vol)

            pygame.mixer.music.play(-1, fade_ms=fade_ms)
        else:
            print(f"Warning: Music missing -> {path}")

    def update_music_volume(self):
        vol = self.game.save_manager.data["settings"].get("music_volume", 100) / 100.0
        pygame.mixer.music.set_volume(vol)

    def stop_music(self, fade_ms=1000):
        pygame.mixer.music.fadeout(fade_ms)

# sprites

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf = pygame.Surface((TILE_SIZE, TILE_SIZE)), *groups):
        super().__init__(*groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()
        self.z = 1

class Collectible(Sprite):
    def __init__(self, pos, surf, *groups):
        super().__init__(pos, surf, *groups)
        self.base_y = self.rect.y
        self.float_speed = 0.005
        self.float_amplitude = 16

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        self.rect.y = self.base_y + math.sin(current_time * self.float_speed) * self.float_amplitude

class CameoSprite(Collectible):
    def __init__(self, pos, secret_id, surf, bonus_ms, *groups):
        self.secret_id = secret_id
        self.bonus_ms = bonus_ms
        super().__init__(pos, surf, *groups)

class TimeBonusSprite(Collectible):
    def __init__(self, pos, black_surf, white_surf, bonus_ms, *groups):
        self.black_surf = black_surf
        self.white_surf = white_surf
        self.bonus_ms = bonus_ms
        super().__init__(pos, self.black_surf, *groups)

class ColorStation(Sprite):
    def __init__(self, pos, size, properties, *groups):
        surf = pygame.Surface(size)
        super().__init__(pos, surf, *groups)

        self.station_colors = {
            'R': properties.get('has_red', False),
            'G': properties.get('has_green', False),
            'B': properties.get('has_blue', False)
        }

    def draw_station(self, player_has_colors):
        empty_color = WHITE if player_has_colors else BLACK
        self.image.fill(empty_color)
        slot_width = self.rect.width / 3 

        if self.station_colors['R']:
            pygame.draw.rect(self.image, (255, 0, 0), (0, 0, slot_width, self.rect.height))
        if self.station_colors['G']:
            pygame.draw.rect(self.image, (0, 255, 0), (slot_width, 0, slot_width, self.rect.height))
        if self.station_colors['B']:
            pygame.draw.rect(self.image, (0, 0, 255), (slot_width * 2, 0, slot_width, self.rect.height))


class ColorDoor(Sprite):
    COLOR_MAP = {
        'K': {'R': False, 'G': False, 'B': False}, # Black
        'R': {'R': True,  'G': False, 'B': False}, # Red
        'G': {'R': False, 'G': True,  'B': False}, # Green
        'B': {'R': False, 'G': False, 'B': True},  # Blue
        'Y': {'R': True,  'G': True,  'B': False}, # Yellow (Red + Green)
        'C': {'R': False, 'G': True,  'B': True},  # Cyan (Green + Blue)
        'M': {'R': True,  'G': False, 'B': True},  # Magenta (Red + Blue)
        'W': {'R': True,  'G': True,  'B': True},  # White (All colors)
    }

    def __init__(self, pos, surf, color_code, *groups):
        super().__init__(pos, surf, *groups)
        self.req_pigments = self.COLOR_MAP.get(color_code, self.COLOR_MAP['K'])

    def is_passable(self, player_pigments):
        return player_pigments == self.req_pigments


class Portal(Sprite):
    def __init__(self, pos, size, *groups):
        surf = pygame.Surface(size, pygame.SRCALPHA) 
        super().__init__(pos, surf, *groups)

        self.orientation = 'H' if size[0] > size[1] else 'V'


class JumpPad(Sprite):
    def __init__(self, pos, size, power, *groups):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        
        super().__init__(pos, surf, *groups)
        self.power = power

        self.rect.bottom = pos[1] + size[1]


class FallingPlatform(Sprite):
    def __init__(self, pos, size, player, collision_sprites, *groups):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        super().__init__(pos, surf, *groups)

        self.player = player
        self.collision_group = collision_sprites

        self.collision_group.add(self)

        self.base_pos = pos
        self.shake_amount = 4

        self.state = 'IDLE'

        self.timers = {
            'crumble': Timer(500),
            'respawn': Timer(2000)
        }

    def reset(self):
        self.state = 'IDLE'
        self.timers['crumble'].deactivate()
        self.timers['respawn'].deactivate()
        self.collision_group.add(self)
        self.rect.topleft = self.base_pos

    def update(self, dt):
        self.old_rect = self.rect.copy()
        
        for timer in self.timers.values():
            timer.update()

        if self.state == 'IDLE':
            if self.rect.colliderect(self.player.rect.inflate(16, 16)):
                self.state = 'SHAKING'
                self.timers['crumble'].activate()

        elif self.state == 'SHAKING':
            if not self.timers['crumble'].active:
                self.state = 'BROKEN'
                self.timers['respawn'].activate()
                self.collision_group.remove(self) 

        elif self.state == 'BROKEN':
            if not self.timers['respawn'].active:
                self.state = 'IDLE'
                self.collision_group.add(self)

    def update_visuals(self, has_colors):
        if self.state == 'BROKEN':
            self.image.set_alpha(0)
            return

        self.image.set_alpha(255)

        base_color = pygame.Color(255, 255, 255) if has_colors else pygame.Color(0, 0, 0)
        
        if self.state == 'SHAKING':
            elapsed = pygame.time.get_ticks() - self.timers['crumble'].start_time
            progress = min(elapsed / self.timers['crumble'].duration, 1.0)

            target_color = pygame.Color(255, 255, 0)
            current_color = base_color.lerp(target_color, progress)
            self.image.fill(current_color)

            offset = math.sin(pygame.time.get_ticks() * 0.05) * self.shake_amount
            self.rect.x = self.base_pos[0] + offset
        else:
            self.image.fill(base_color)
            self.rect.x = self.base_pos[0]

class TimerButton(Sprite):
    def __init__(self, pos, size, target_id, timer_ms, *groups):
        surf = pygame.Surface(size)
        surf.fill((255, 0, 0))
        super().__init__(pos, surf, *groups)

        self.base_rect = self.rect.copy()
        self.target_id = target_id
        self.target_laser = None

        self.timer = Timer(timer_ms)
        self.pressed = False

    def press(self):
        if not self.pressed:
            self.pressed = True
            self.timer.activate()

            self.image = pygame.Surface((self.base_rect.width, 16))
            self.image.fill((0, 255, 0)) 
            self.rect = self.image.get_frect()
            self.rect.bottomleft = self.base_rect.bottomleft

            if self.target_laser:
                self.target_laser.active = False

    def update(self, dt):
        self.timer.update()

        if self.timer.active:
            elapsed = pygame.time.get_ticks() - self.timer.start_time
            progress = min(elapsed / self.timer.duration, 1.0)

            current_color = pygame.Color(0, 255, 0).lerp(pygame.Color(255, 0, 0), progress)
            self.image.fill(current_color)
        else:
            if self.pressed:
                self.pressed = False
                self.image = pygame.Surface(self.base_rect.size)
                self.image.fill((255, 0, 0))
                self.rect = self.base_rect.copy()

                if self.target_laser:
                    self.target_laser.active = True

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

# player

class PlayerStateID(Enum):
    IDLE = auto()
    RUN = auto()
    FALL = auto()
    JUMP = auto()
    WALL_SLIDE = auto()
    DASH = auto()
    DEATH = auto() 

class PlayerState:
    def __init__(self, player):
        self.player = player

    def enter(self):
        pass

    def handle_input(self, keys, just_pressed):
        pass

    def update(self, dt):
        return None

class IdleState(PlayerState):
    def handle_input(self, keys, just_pressed):
        input_vector = Vector2(0,0)
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]): input_vector.x += 1
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]): input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if just_pressed[pygame.K_SPACE] and self.player.on_surface['floor']:
            self.player.jump = True

        if just_pressed[pygame.K_LSHIFT] and self.player.can_dash and not self.player.timers['dash_cooldown'].active:
            self.player.can_dash = False
            self.player.is_dashing = True

    def update(self, dt):
        if self.player.is_dashing:
            self.player.is_dashing = False
            return PlayerStateID.DASH

        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height

            self.player.scale_x = 0.75
            self.player.scale_y = 1.25

            self.player.rect.bottom -= 1
            return PlayerStateID.JUMP

        if not self.player.on_surface['floor']:
            self.player.timers['coyote'].activate()
            return PlayerStateID.FALL

        if self.player.direction.x != 0:
            return PlayerStateID.RUN

class RunState(PlayerState):
    def handle_input(self, keys, just_pressed):
        input_vector = Vector2(0,0)
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]): input_vector.x += 1
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]): input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if just_pressed[pygame.K_SPACE] and self.player.on_surface['floor']:
            self.player.jump = True

        if just_pressed[pygame.K_LSHIFT] and self.player.can_dash and not self.player.timers['dash_cooldown'].active:
            self.player.can_dash = False
            self.player.is_dashing = True

    def update(self, dt):
        if random.random() < 0.125:
            self.player.spawn_dust('run')

        if self.player.is_dashing:
            self.player.is_dashing = False
            return PlayerStateID.DASH

        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height

            self.player.scale_x = 0.75
            self.player.scale_y = 1.25

            self.player.rect.bottom -= 1
            return PlayerStateID.JUMP

        if not self.player.on_surface['floor']:
            self.player.timers['coyote'].activate()
            return PlayerStateID.FALL

        if self.player.direction.x == 0:
            return PlayerStateID.IDLE

class FallState(PlayerState):
    def handle_input(self, keys, just_pressed):
        if not self.player.timers['wall_jump_block'].active:
            input_vector = Vector2(0,0)
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]): input_vector.x += 1
            if (keys[pygame.K_LEFT] or keys[pygame.K_a]): input_vector.x -= 1
            self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if just_pressed[pygame.K_SPACE]:
            if self.player.timers['coyote'].active:
                self.player.timers['coyote'].deactivate()
                self.player.jump = True

            elif self.player.can_double_jump:
                self.player.can_double_jump = False
                self.player.jump = True

        if just_pressed[pygame.K_LSHIFT] and self.player.can_dash and not self.player.timers['dash_cooldown'].active:
            self.player.can_dash = False
            self.player.is_dashing = True

    def update(self, dt):
        if self.player.is_dashing:
            self.player.is_dashing = False
            return PlayerStateID.DASH

        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height

            self.player.scale_x = 0.75
            self.player.scale_y = 1.25

            return PlayerStateID.JUMP

        if (self.player.on_surface['left'] and self.player.direction.x < 0) and self.player.pigments['B'] or \
           (self.player.on_surface['right'] and self.player.direction.x > 0) and self.player.pigments['B']:
            return PlayerStateID.WALL_SLIDE

        self.player.direction.y += self.player.gravity * dt * self.player.fall_gravity_modifier
        self.player.direction.y = min(self.player.direction.y, self.player.max_fall_speed)

        if self.player.on_surface['floor']:
            impact_vel = self.player.direction.y 
            self.player.spawn_dust('land', impact_vel)
            self.player.direction.y = 0
            if self.player.direction.x != 0:
                return PlayerStateID.RUN
            return PlayerStateID.IDLE

class JumpState(PlayerState):
    def enter(self):
        self.player.audio.play_sfx('jump') 

    def handle_input(self, keys, just_pressed):
        if not self.player.timers['wall_jump_block'].active:
            input_vector = Vector2(0,0)
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]): input_vector.x += 1
            if (keys[pygame.K_LEFT] or keys[pygame.K_a]): input_vector.x -= 1
            self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if just_pressed[pygame.K_SPACE] and self.player.can_double_jump:
            self.player.can_double_jump = False
            self.player.jump = True

        if just_pressed[pygame.K_LSHIFT] and self.player.can_dash and not self.player.timers['dash_cooldown'].active:
            self.player.can_dash = False
            self.player.is_dashing = True

    def update(self, dt):
        if self.player.is_dashing:
            self.player.is_dashing = False
            return PlayerStateID.DASH

        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height

            self.player.scale_x = 0.75
            self.player.scale_y = 1.25

            return PlayerStateID.JUMP

        if (self.player.on_surface['left'] and self.player.direction.x < 0) and self.player.pigments['B'] or \
           (self.player.on_surface['right'] and self.player.direction.x > 0) and self.player.pigments['B']:
            return PlayerStateID.WALL_SLIDE

        self.player.direction.y += self.player.gravity* dt

        if self.player.direction.y >= 0:
            return PlayerStateID.FALL

class WallSlideState(PlayerState):
    def handle_input(self, keys, just_pressed):
        input_vector = Vector2(0,0)
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]): input_vector.x += 1
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]): input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0
        if just_pressed[pygame.K_SPACE]:
            self.player.jump = True

    def update(self, dt):
        if self.player.jump:
            self.player.jump = False

            self.player.direction.y = -self.player.jump_height

            self.player.direction.x = 1 if self.player.on_surface['left'] else -1

            self.player.timers['wall_jump_block'].activate()

            self.player.scale_x = 0.75
            self.player.scale_y = 1.25

            return PlayerStateID.JUMP

        self.player.direction.y += self.player.gravity * dt * self.player.slide_gravity_modifier
        self.player.direction.y = min(self.player.direction.y, self.player.max_fall_speed / 8)

        if self.player.on_surface['floor']:
            impact_vel = self.player.direction.y 
            self.player.spawn_dust('land', impact_vel)

            self.player.scale_x = 1.25
            self.player.scale_y = 0.75

            return PlayerStateID.IDLE

        if self.player.on_surface['left'] and self.player.direction.x >= 0:
            return PlayerStateID.FALL

        if self.player.on_surface['right'] and self.player.direction.x <= 0:
            return PlayerStateID.FALL

        if not self.player.on_surface['left'] and not self.player.on_surface['right']:
            return PlayerStateID.FALL

class DashState(PlayerState):
    def enter(self):
        self.player.audio.play_sfx('dash')
        self.player.timers['dash'].activate()
        self.dash_dir = self.player.facing 

    def handle_input(self, keys, just_pressed):
        pass

    def update(self, dt):
        self.player.spawn_trail()
        self.player.direction.y = 0

        self.player.direction.x = self.dash_dir * 3

        if not self.player.timers['dash'].active:
            self.player.timers['dash_cooldown'].activate()
            self.player.direction.x = self.dash_dir
            return PlayerStateID.FALL

        if (self.player.on_surface['right'] and self.dash_dir > 0) or \
           (self.player.on_surface['left'] and self.dash_dir < 0):
            self.player.timers['dash_cooldown'].activate()
            self.player.direction.x = 0
            return PlayerStateID.FALL

class DeathState(PlayerState):
    def enter(self):
        self.player.audio.play_sfx('death') 
        self.player.spawn_dust('death') 

        self.player.timers['death'].activate()
        self.player.direction.x = 0
        self.player.direction.y = 0

        self.start_color = pygame.Color(
            255 if self.player.pigments['R'] else 0,
            255 if self.player.pigments['G'] else 0,
            255 if self.player.pigments['B'] else 0
        )

        has_colors = any(self.player.pigments.values())
        self.target_color = pygame.Color(0, 0, 0) if has_colors else pygame.Color(255, 255, 255)

    def handle_input(self, keys, just_pressed):
        if just_pressed[pygame.K_SPACE]:
            self.player.timers['death'].deactivate()
            self.player.needs_respawn = True

    def update(self, dt):
        self.player.direction = Vector2(0, 0)

        if self.player.timers['death'].active:
            elapsed = pygame.time.get_ticks() - self.player.timers['death'].start_time
            progress = min(elapsed / self.player.timers['death'].duration, 1.0)

            current_color = self.start_color.lerp(self.target_color, progress)
            self.player.image.fill(current_color)
        else:
            self.player.needs_respawn = True

class Player(pygame.sprite.Sprite):
    def _init_graphics(self, surf, pos):
        self.base_image = pygame.Surface(surf)
        self.base_image.fill(WHITE)
        self.image = self.base_image.copy()

        self.rect = self.image.get_frect(topleft=pos)
        self.old_rect = self.rect.copy()
        self.display_rect = self.rect.copy()
        self.z = 10
        self.scale_x = 1.0
        self.scale_y = 1.0

    def _init_physics(self):
        self.direction = Vector2(0, 0)
        self.speed = 300
        self.gravity = 2560 # earth 640px/s^2 but in games it should be bigger from 2-5 times
        self.jump = False
        self.jump_height = 1012

        self.fall_gravity_modifier = 2
        self.slide_gravity_modifier = 0.125
        self.max_fall_speed = 1600 # To avoid bugs passing through platforms

        self.on_surface = {'floor': False, 'left': False, 'right': False}
        self.platform = None

    def _init_mechanics(self):
        self.can_double_jump = False
        self.can_dash = True
        self.facing = 1
        self.is_dashing = False
        self.pigments = {'R': False, 'G': False, 'B': False}
        self.needs_respawn = False

        self.timers = {
            'wall_jump': Timer(500),
            'wall_jump_block': Timer(250),
            'dash': Timer(250),
            'dash_cooldown': Timer(250),
            'coyote': Timer(125),
            'death': Timer(500),
        }

    def _init_states(self):
        self.states = {
            PlayerStateID.IDLE: IdleState(self),
            PlayerStateID.RUN: RunState(self),
            PlayerStateID.FALL: FallState(self),
            PlayerStateID.JUMP: JumpState(self),
            PlayerStateID.WALL_SLIDE: WallSlideState(self),
            PlayerStateID.DASH: DashState(self),
            PlayerStateID.DEATH: DeathState(self),
        }
        self.current_state = self.states[PlayerStateID.IDLE]
        self.update_color_and_size()

    def __init__(self, pos, surf, collision_group_check, audio, *groups):
        super().__init__(*groups)
        self.audio = audio
        self.collision_sprites = collision_group_check
        
        self._init_graphics(surf, pos)
        self._init_physics()
        self._init_mechanics()
        self._init_states()

    def change_state(self, new_state_id):
        if self.current_state != self.states[new_state_id]:
            self.current_state = self.states[new_state_id]
            self.current_state.enter()

    def update(self, dt):
        self.old_rect = self.rect.copy()

        keys = pygame.key.get_pressed()
        just_pressed = pygame.key.get_just_pressed()

        self.current_state.handle_input(keys, just_pressed)
        if self.direction.x != 0:
            self.facing = 1 if self.direction.x > 0 else -1

        new_state_id = self.current_state.update(dt)
        if new_state_id:
            self.change_state(new_state_id)

        self.rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.rect.y += self.direction.y * dt
        self.collision('vertical')

        self.update_timers()
        self.check_contact()

        lerp_speed = 15 * dt
        self.scale_x += (1.0 - self.scale_x) * lerp_speed
        self.scale_y += (1.0 - self.scale_y) * lerp_speed

        self.scale_x = max(0.75, min(1.25, self.scale_x))
        self.scale_y = max(0.75, min(1.25, self.scale_y))

        new_width = max(1, int(self.base_image.get_width() * self.scale_x))
        new_height = max(1, int(self.base_image.get_height() * self.scale_y))
        self.image = pygame.transform.scale(self.base_image, (new_width, new_height))

        self.display_rect = self.image.get_frect(center=self.rect.center)


    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def check_contact(self):
        floor_rect = pygame.Rect(self.rect.bottomleft, (self.rect.width,8))
        right_rect = pygame.Rect(self.rect.topright + Vector2(0, self.rect.height / 8), (8, self.rect.height / 2))
        left_rect = pygame.Rect(self.rect.topleft + Vector2(-1, self.rect.height / 8), (8, self.rect.height / 2))
        valid_collision_rects = []
        for sprite in self.collision_sprites:
            if isinstance(sprite, ColorDoor) and sprite.is_passable(self.pigments):
                continue
            valid_collision_rects.append(sprite.rect)
        collide_rects = valid_collision_rects

        # pygame.draw.rect(self.display_surface, YELLOW, floor_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, right_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, left_rect)

        self.on_surface['floor'] = True if floor_rect.collidelist(collide_rects) >= 0 and self.direction.y >= 0 else False
        self.on_surface['right'] = True if right_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['left'] = True if left_rect.collidelist(collide_rects) >= 0 else False
        # print(self.on_surface)

        if self.on_surface['floor']:
            self.can_double_jump = self.pigments['G']
            self.can_dash = self.pigments['R']
        elif self.on_surface['left'] or self.on_surface['right']:
            self.can_dash = self.pigments['R'] #and only dash also can reload by walls

    def update_color_and_size(self):
        count = sum(self.pigments.values())

        color = (
            255 if self.pigments['R'] else 0,
            255 if self.pigments['G'] else 0,
            255 if self.pigments['B'] else 0
        )

        new_size = (5 + 2 * count) * UNIT # UNIT = 8

        old_center = self.rect.center
        self.base_image = pygame.Surface((new_size, new_size))
        self.base_image.fill(color)
        self.image = self.base_image.copy()

        self.rect = self.image.get_frect(center=old_center)
        self.display_rect = self.rect.copy()

        self.can_dash = self.pigments['R']
        self.can_double_jump = self.pigments['G']

    def get_all_sprites_group(self):
        for g in self.groups():
            if type(g).__name__ == 'AllSprites':
                return g
        return self.groups()[0]

    def spawn_dust(self, spawn_type='land', impact_vel=0):
        all_sprites = self.get_all_sprites_group()
        has_colors = any(self.pigments.values())
        color = WHITE if has_colors else BLACK

        if spawn_type == 'run':
            spawn_x = self.rect.left if self.direction.x > 0 else self.rect.right
            spawn_pos = (spawn_x, self.rect.bottom)
            
            vel_x = random.uniform(-64, 64)
            vel_y = random.uniform(-64, -192)
            lifetime = random.randint(125, 500)
            DustParticle(spawn_pos, color, (vel_x, vel_y), lifetime, all_sprites)
            
        elif spawn_type == 'land':
            vel = max(0, impact_vel) # defence from negative numbers
            amount = int(vel ** 0.5) # square root
            
            for i in range(amount):
                if i % 2 == 0:
                    spawn_x = self.rect.left
                    vel_x = random.uniform(-192, -64)
                else:
                    spawn_x = self.rect.right
                    vel_x = random.uniform(64, 192)
                    
                spawn_pos = (spawn_x, self.rect.bottom)
                vel_y = random.uniform(-64, -256)
                lifetime = random.randint(125, 500)
                DustParticle(spawn_pos, color, (vel_x, vel_y), lifetime, all_sprites)
                
        elif spawn_type == 'death':
            area = self.rect.width * self.rect.height
            amount = int((area / 64))
            
            for _ in range(amount):
                spawn_pos = self.rect.center
                vel_x = random.uniform(-448, 448)
                vel_y = random.uniform(-448, 448)
                lifetime = random.randint(125, 500)
                DustParticle(spawn_pos, color, (vel_x, vel_y), lifetime, all_sprites)

    def spawn_trail(self):
        all_sprites = self.get_all_sprites_group()
        TrailParticle(self.rect.topleft, self.image, 250, all_sprites)

    def collision(self, axis):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if isinstance(sprite, ColorDoor):
                    if sprite.is_passable(self.pigments):
                        continue
                if axis == 'horizontal':
                    if self.rect.left <= sprite.rect.right and self.old_rect.left >= sprite.old_rect.right - 1:
                        self.rect.left = sprite.rect.right
                    if self.rect.right >= sprite.rect.left and self.old_rect.right <= sprite.old_rect.left + 1:
                        self.rect.right = sprite.rect.left
                else:
                    if self.rect.top <= sprite.rect.bottom and self.old_rect.top >= sprite.old_rect.bottom - 1:
                        self.rect.top = sprite.rect.bottom
                    if self.rect.bottom >= sprite.rect.top and self.old_rect.bottom <= sprite.old_rect.top + 1:
                        self.rect.bottom = sprite.rect.top
                    self.direction.y = 0

# level

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

    def _handle_triggers(self):
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
                        self.playing_state.game.audio.play_sfx('button')
                    trigger.press()

    def _handle_collectibles(self):
        for item in self.collectible_sprites:
            if self.player.rect.colliderect(item.rect):
                self.playing_state.game.audio.play_sfx('secret')
                if isinstance(item, CameoSprite):
                    self.playing_state.game.save_manager.unlock_secret(item.secret_id)

                self.playing_state.start_time += item.bonus_ms
                current_time = pygame.time.get_ticks()

                if current_time - self.playing_state.start_time < 0:
                    self.playing_state.start_time = current_time 
                item.kill()

    def update(self, dt):
        self.all_sprites.update(dt)
        self.update_colors(dt)
        self.check_hazards()

        if self.player.needs_respawn:
            self.reset_level()

        self._handle_triggers()
        self._handle_collectibles()

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

    def _toggle_color(self, station, color_key, enable_player):
        self.player.audio.play_sfx('color') 
        self.player.pigments[color_key] = enable_player
        station.station_colors[color_key] = not enable_player

        self.player.direction.y = -716 # half jump 1012 / square root of 2
        self.player.scale_x = 0.75
        self.player.scale_y = 1.25
        self.player.rect.bottom -= 1

        self.player.change_state(PlayerStateID.JUMP)

        self.player.update_color_and_size()
        self.update_stantions_to_fit_world()

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
                            self._toggle_color(station, color_key, True)

                        elif self.player.pigments[color_key] and not station.station_colors[color_key]:
                            self._toggle_color(station, color_key, False)

    def update_stantions_to_fit_world(self):
        has_colors = any(self.player.pigments.values())
        for st in self.trigger_sprites:
            if isinstance(st, ColorStation):
                st.draw_station(has_colors)

    def _draw_textures(self, has_colors):
        target_texture = self.white_tile_image if has_colors else self.black_tile_image
        spike_texture = self.white_spike_image if has_colors else self.black_spike_image

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

    def draw(self, screen):
        has_colors = any(self.player.pigments.values())
        bg_color = BLACK if has_colors else WHITE
        screen.fill(bg_color)

        self._draw_textures(has_colors)
        self.all_sprites.draw(self.player.rect.center)

# states


class StateID(Enum):
    MENU = auto()
    LEVEL_SELECT = auto()
    PLAYING = auto()
    PAUSE = auto()
    LEVEL_COMPLETE = auto()
    SETTINGS = auto()
    SECRETS = auto()

class State:
    def __init__(self, game):
        self.game = game

    def events(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

# MENU -> LEVEL_SELECT or SECRETS or SETTINGS

class MenuState(State):
    def enter(self):
        self.game.audio.play_music('menu.mp3', fade_ms=2000)

    def __init__(self, game):
        super().__init__(game)
        self.game.audio.play_music('menu.mp3', fade_ms=2000)
        self.options = ["PLAY", "SECRETS", "SETTINGS", "QUIT"]
        self.selected_index = 0
        self.font_large = pygame.font.SysFont('courier', 64)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.options)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key == pygame.K_RETURN:
                selected = self.options[self.selected_index]
                if selected == "PLAY":
                    self.game.change_state(StateID.LEVEL_SELECT)

                elif selected == "SECRETS":
                    self.game.change_state(StateID.SECRETS)

                elif selected == "SETTINGS":
                    self.game.change_state(StateID.SETTINGS)

                elif selected == "QUIT":
                    self.game.running = False

    def draw(self, screen):
        screen.fill(BLACK)

        for i, option in enumerate(self.options):
            if i == self.selected_index:
                color = YELLOW
                text = f"> {option} <"
            else:
                color = WHITE
                text = option
                
            img = self.font_large.render(text, True, color)
            rect = img.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 64 + i * 64))
            screen.blit(img, rect)

# LEVEL_SELECT -> PLAYING or MENU

class LevelSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.selected_index = 0
        self.font_main = pygame.font.SysFont('courier', 48, bold=True)
        self.font_small = pygame.font.SysFont('courier', 24)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(StateID.MENU)

            elif event.key in (pygame.K_UP, pygame.K_w):
                if self.selected_index > 0:
                    self.selected_index -= 1

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                if self.selected_index < len(LEVEL_ORDER) - 1:
                    self.selected_index += 1

            elif event.key == pygame.K_RETURN:
                level_name = LEVEL_ORDER[self.selected_index]
                if self.game.save_manager.is_level_unlocked(level_name):
                    self.game.states[StateID.PLAYING].load_level(level_name)

    def _draw_level_item(self, screen, level_name, index, center_y, spacing, is_unlocked):
        offset = index - self.selected_index
        is_selected = (index == self.selected_index)

        if is_selected:
            if is_unlocked:
                color = YELLOW
                display_name = LEVEL_NAMES.get(level_name, level_name.upper())
            else:
                color = (255, 255, 255)
                display_name = "??? (LOCKED)"

            title_img = self.font_main.render(display_name, True, color)
            title_rect = title_img.get_frect(center=(WINDOW_WIDTH / 2, center_y))
            screen.blit(title_img, title_rect)

            if is_unlocked:
                best_time = self.game.save_manager.data["best_times"].get(level_name, None)
                if best_time is not None:
                    seconds = (best_time // 1000) % 60
                    minutes = (best_time // 60000) % 60
                    millis = (best_time % 1000) // 10
                    time_text = f"BEST TIME: {minutes:02d}:{seconds:02d}:{millis:02d}"
                else:
                    time_text = "NOT COMPLETED YET"
                    
                time_img = self.font_small.render(time_text, True, WHITE)
                time_rect = time_img.get_frect(center=(WINDOW_WIDTH / 2, center_y + 48))
                screen.blit(time_img, time_rect)
            
        else:
            if is_unlocked:
                color = (150, 150, 150)
                display_name = LEVEL_NAMES.get(level_name, level_name.upper())
            else:
                color = (50, 50, 50)
                display_name = "???"
                
            title_img = self.font_small.render(display_name, True, color)
            title_rect = title_img.get_frect(center=(WINDOW_WIDTH / 2, center_y + (offset * spacing)))
            screen.blit(title_img, title_rect)

    def draw(self, screen):
        screen.fill(BLUE)

        center_y = WINDOW_HEIGHT / 2
        spacing = 96

        for i, level_name in enumerate(LEVEL_ORDER):
            is_unlocked = self.game.save_manager.is_level_unlocked(level_name)
            self._draw_level_item(screen, level_name, i, center_y, spacing, is_unlocked)

# PLAYING -> PAUSE (ESCAPE) or LEVEL_COMPLETE

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)
        self.current_stage = None
        self.current_level_name = ""
        self.start_time = 0 
        self.last_run_time = 0
        self.pause_start_time = 0

    def load_level(self, level_name):
        self.current_level_name = level_name
        tmx_map = load_pygame(join('data', 'levels', f'{level_name}.tmx'))

        self.current_stage = Level(tmx_map, self)

        self.start_time = pygame.time.get_ticks()
        self.game.audio.play_music('magiksolo-investigation-puzzle.mp3', fade_ms=1000)
        self.game.change_state(StateID.PLAYING)

    def resume_timer(self):
        pause_duration = pygame.time.get_ticks() - self.pause_start_time
        self.start_time += pause_duration

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.pause_start_time = pygame.time.get_ticks()
                self.game.change_state(StateID.PAUSE)

    def update(self, dt):
        if self.current_stage:
            self.current_stage.update(dt)
            
            if hasattr(self.current_stage, 'is_completed') and self.current_stage.is_completed:
                final_time_ms = pygame.time.get_ticks() - self.start_time
                self.last_run_time = final_time_ms

                is_new_record = self.game.save_manager.save_best_time(self.current_level_name, final_time_ms)

                if self.current_level_name in LEVEL_ORDER:
                    current_idx = LEVEL_ORDER.index(self.current_level_name)
                    if current_idx + 1 < len(LEVEL_ORDER):
                        next_level_name = LEVEL_ORDER[current_idx + 1]
                        self.game.save_manager.unlock_level(next_level_name)

                self.game.change_state(StateID.LEVEL_COMPLETE)

    def draw(self, screen):
        if self.current_stage:
            self.current_stage.draw(screen)

            if self.game.current_state == self:
                current_time_ms = pygame.time.get_ticks() - self.start_time
            else:
                current_time_ms = self.pause_start_time - self.start_time

            seconds = (current_time_ms // 1000) % 60
            minutes = (current_time_ms // 60000) % 60
            millis = (current_time_ms % 1000) // 10
            
            font = pygame.font.SysFont('courier', 32)

            time_text = font.render(f"TIME: {minutes:02d}:{seconds:02d}:{millis:02d}", True, (0, 255, 0))
            screen.blit(time_text, (screen.width - (time_text.width + 64), 64)) #y = screen.height - (time_text.height + 64))

# PAUSE -> PLAYING/SETTINGS/MENU

class PauseState(State):
    def __init__(self, game):
        super().__init__(game)
        self.options = ["RESUME", "RESTART LEVEL", "MENU"]
        self.selected_index = 0
        self.font_huge = pygame.font.SysFont('courier', 64, bold=True)
        self.font_large = pygame.font.SysFont('courier', 48, bold=True)

        self.overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 127))

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.states[StateID.PLAYING].resume_timer()
                self.game.change_state(StateID.PLAYING)

            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.options)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key == pygame.K_RETURN:
                selected = self.options[self.selected_index]
                playing_state = self.game.states[StateID.PLAYING]
                
                if selected == "RESUME":
                    playing_state.resume_timer()
                    self.game.change_state(StateID.PLAYING)

                elif selected == "RESTART LEVEL":
                    playing_state.load_level(playing_state.current_level_name)

                elif selected == "MENU":
                    self.game.change_state(StateID.MENU)

    def draw(self, screen):
        self.game.states[StateID.PLAYING].draw(screen)
        screen.blit(self.overlay, (0, 0))

        title = self.font_huge.render("PAUSED", True, WHITE)
        title_rect = title.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 64))
        screen.blit(title, title_rect)

        for i, option in enumerate(self.options):
            if i == self.selected_index:
                color = YELLOW
                text = f"> {option} <" 
            else:
                color = WHITE
                text = option
                
            img = self.font_large.render(text, True, color)
            rect = img.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + i * 64))
            screen.blit(img, rect)

# LEVEL_COMPLETE -> play next level PLAYING(retry or load next level) or quit to MENU

class LevelCompleteState(State):
    def enter(self):
        pygame.mixer.music.fadeout(1000)
        playing_state = self.game.states[StateID.PLAYING]
        current_level = playing_state.current_level_name
        
        self.selected_index = 0
        if current_level in LEVEL_ORDER and LEVEL_ORDER.index(current_level) + 1 < len(LEVEL_ORDER):
            self.options = ["NEXT LEVEL", "RETRY", "MENU"]
        else:
            self.options = ["RETRY", "MENU"]

    def __init__(self, game):
        super().__init__(game)
        self.options = ["NEXT LEVEL", "RETRY", "MENU"]
        self.selected_index = 0
        self.font_huge = pygame.font.SysFont('courier', 64, bold=True)
        self.font_large = pygame.font.SysFont('courier', 48, bold=True)
        self.font_small = pygame.font.SysFont('courier', 32)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.options)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key == pygame.K_RETURN:
                selected = self.options[self.selected_index]
                playing_state = self.game.states[StateID.PLAYING]
                
                if selected == "NEXT LEVEL":
                    current_level = playing_state.current_level_name
                    if current_level in LEVEL_ORDER:
                        idx = LEVEL_ORDER.index(current_level)
                        if idx + 1 < len(LEVEL_ORDER):
                            next_level = LEVEL_ORDER[idx + 1]
                            playing_state.load_level(next_level)

                        else:
                            self.game.change_state(StateID.MENU) 
                            
                elif selected == "RETRY":
                    playing_state.load_level(playing_state.current_level_name)
                    
                elif selected == "MENU":
                    self.game.change_state(StateID.MENU)

    def draw(self, screen):
        screen.fill(YELLOW)
        title = self.font_huge.render("LEVEL COMPLETE", True, BLACK)
        title_rect = title.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 128))
        screen.blit(title, title_rect)

        playing_state = self.game.states[StateID.PLAYING]
        run_time = playing_state.last_run_time
        seconds = (run_time // 1000) % 60
        minutes = (run_time // 60000) % 60
        millis = (run_time % 1000) // 10

        time_text = self.font_small.render(f"YOUR TIME: {minutes:02d}:{seconds:02d}:{millis:02d}", True, RED)
        time_rect = time_text.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 64))
        screen.blit(time_text, time_rect)

        # TOTAL BEST TIME
        total_time = sum(self.game.save_manager.data.get("best_times", {}).values())
        t_seconds = (total_time // 1000) % 60
        t_minutes = (total_time // 60000) % 60
        t_millis = (total_time % 1000) // 10
        
        total_text = self.font_small.render(f"TOTAL TIME: {t_minutes:02d}:{t_seconds:02d}:{t_millis:02d}", True, BLACK)
        total_rect = total_text.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 32))
        screen.blit(total_text, total_rect)

        for i, option in enumerate(self.options):
            if i == self.selected_index:
                color = BLACK
                text = f"> {option} <" 
            else:
                color = RED
                text = option
                
            img = self.font_large.render(text, True, color)
            rect = img.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 48 + i * 64))
            screen.blit(img, rect)

# SETTINGS -> go back to MENU/PAUSE

class SettingsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.options = ["FULLSCREEN", "MINIMALIST", "MUSIC VOL", "SFX VOL", "BACK"]
        self.selected_index = 0
        self.font_large = pygame.font.SysFont('courier', 48, bold=True)
        self.font_huge = pygame.font.SysFont('courier', 64, bold=True)

    def _handle_volume_change(self, selected, step):
        if selected == "MUSIC VOL":
            vol = self.game.save_manager.data["settings"].get("music_volume", 100)
            new_vol = max(0, min(100, vol + step))
            self.game.save_manager.data["settings"]["music_volume"] = new_vol
            self.game.save_manager.save()
            self.game.audio.update_music_volume()

        elif selected == "SFX VOL":
            vol = self.game.save_manager.data["settings"].get("sfx_volume", 100)
            new_vol = max(0, min(100, vol + step))
            self.game.save_manager.data["settings"]["sfx_volume"] = new_vol
            self.game.save_manager.save()
            self.game.audio.play_sfx('jump')

    def _handle_toggle(self, selected):
        if selected == "FULLSCREEN":
            current_val = self.game.save_manager.data["settings"]["fullscreen"]
            self.game.save_manager.data["settings"]["fullscreen"] = not current_val
            self.game.save_manager.save()
            pygame.display.toggle_fullscreen()

        elif selected == "MINIMALIST":
            current_val = self.game.save_manager.data["settings"].get("minimalist", False)
            self.game.save_manager.data["settings"]["minimalist"] = not current_val
            self.game.save_manager.save()

        elif selected == "BACK":
            self.game.change_state(StateID.MENU)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.options)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                selected = self.options[self.selected_index]
                step = -10 if event.key in (pygame.K_LEFT, pygame.K_a) else 10
                self._handle_volume_change(selected, step)

            elif event.key == pygame.K_RETURN:
                selected = self.options[self.selected_index]
                self._handle_toggle(selected)

    def _get_option_text(self, option):
        if option == "FULLSCREEN":
            is_on = self.game.save_manager.data["settings"]["fullscreen"]
            return f"FULLSCREEN [{'ON' if is_on else 'OFF'}]"

        elif option == "MINIMALIST":
            is_on = self.game.save_manager.data["settings"].get("minimalist", False)
            return f"MINIMALIST [{'ON' if is_on else 'OFF'}]"

        elif option == "MUSIC VOL":
            vol = self.game.save_manager.data["settings"].get("music_volume", 100)
            return f"MUSIC VOL < {vol}% >"

        elif option == "SFX VOL":
            vol = self.game.save_manager.data["settings"].get("sfx_volume", 100)
            return f"SFX VOL   < {vol}% >"

        return option

    def draw(self, screen):
        screen.fill(BLACK)

        title = self.font_huge.render("SETTINGS", True, WHITE)
        title_rect = title.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 160))
        screen.blit(title, title_rect)

        for i, option in enumerate(self.options):
            display_text = self._get_option_text(option)
            color = YELLOW if i == self.selected_index else WHITE
            text = f"> {display_text} <" if i == self.selected_index else display_text
            img = self.font_large.render(text, True, color)
            rect = img.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 24 + i * 64))
            screen.blit(img, rect)

# SECRETS -> MENU

class SecretsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.font_title = pygame.font.SysFont('courier', 64, bold=True)
        self.font_name = pygame.font.SysFont('courier', 32)

        self.cameo_names = ["NINJA", "ELUETTE", "RAPPY", "NANAS"]

        tileset_img = pygame.image.load(join('graphics', 'tilesets', 'demo_tiles.png')).convert_alpha()
        self.cameo_surfaces = []

        for i in range(4):
            surf = pygame.Surface((128, 128), pygame.SRCALPHA)
            surf.blit(tileset_img, (0, 0), (i * 128, 768, 128, 128))
            self.cameo_surfaces.append(surf)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.game.change_state(StateID.MENU)

    def draw(self, screen):
        screen.fill(BLACK)

        title = self.font_title.render("SECRETS GALLERY", True, YELLOW)
        title_rect = title.get_frect(center=(WINDOW_WIDTH / 2, 80))
        screen.blit(title, title_rect)

        instruction = self.font_name.render("PRESS ESC TO RETURN", True, WHITE)
        inst_rect = instruction.get_frect(center=(WINDOW_WIDTH / 2, 128))
        screen.blit(instruction, inst_rect)

        start_x = WINDOW_WIDTH / 2 - 300
        spacing_x = 200

        for i in range(4):
            x = start_x + (i * spacing_x)
            y = WINDOW_HEIGHT / 2

            is_unlocked = self.game.save_manager.has_secret(i)

            if is_unlocked:
                img_rect = self.cameo_surfaces[i].get_frect(center=(x, y))
                screen.blit(self.cameo_surfaces[i], img_rect)

                name_text = self.font_name.render(self.cameo_names[i], True, WHITE)

            else:
                placeholder = pygame.Surface((128, 128))
                placeholder.fill((255, 0, 255))
                img_rect = placeholder.get_frect(center=(x, y))
                screen.blit(placeholder, img_rect)

                q_text = self.font_title.render("?", True, WHITE)
                q_rect = q_text.get_frect(center=(x, y))
                screen.blit(q_text, q_rect)

                name_text = self.font_name.render("???", True, WHITE)

            name_rect = name_text.get_frect(center=(x, y + 96))
            screen.blit(name_text, name_rect)

# game

class Game:
    def __init__(self):
        pygame.init()

        self.save_manager = SaveManager()
        self.audio = AudioManager(self)

        is_fullscreen = self.save_manager.data["settings"]["fullscreen"]
        flags = pygame.FULLSCREEN | pygame.SCALED if is_fullscreen else pygame.SCALED

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        pygame.display.set_caption('rgbox')
        self.clock = pygame.time.Clock()
        self.running = True

        self.states = {
            StateID.MENU: MenuState(self),
            StateID.LEVEL_SELECT: LevelSelectState(self),
            StateID.PLAYING: PlayingState(self),
            StateID.PAUSE: PauseState(self),
            StateID.LEVEL_COMPLETE: LevelCompleteState(self),
            StateID.SETTINGS: SettingsState(self),
            StateID.SECRETS: SecretsState(self),
        }

        self.current_state = self.states[StateID.MENU]
        # self.current_state = self.states[StateID.PLAYING]

    def change_state(self, state_id: StateID):
        if hasattr(self.current_state, 'exit'):
            self.current_state.exit()
        self.current_state = self.states[state_id]
        if hasattr(self.current_state, 'enter'):
            self.current_state.enter()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_q:
                    self.running = False

            self.current_state.events(event)

    def update(self, dt):
        self.current_state.update(dt)

    def draw(self, screen):
        self.current_state.draw(screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update(dt)
            self.draw(self.screen)

if __name__ == '__main__':
    game = Game()
    game.run()
