from .settings import *
from .timer import Timer

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf = pygame.Surface((TILE_SIZE, TILE_SIZE)), *groups):
        super().__init__(*groups)
        self.image = surf
        # self.image.fill(WHITE)
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()

class MovingSprite(Sprite):
    def __init__(self, size,  start_pos, end_pos, move_dir, speed, *groups):
        surf = pygame.Surface(size)
        surf.fill(WHITE)
        super().__init__(start_pos, surf, *groups)
        self.rect.center = start_pos
        if move_dir == 'x':
            self.rect.midleft = start_pos
        else:
            self.rect.midtop = start_pos
        self.start_pos = start_pos
        self.end_pos = end_pos

        self.moving = True
        self.speed = speed
        self.direction = Vector2(1,0) if move_dir == 'x' else Vector2(0,1)
        self.move_dir = move_dir

    def check_border(self):
        if self.move_dir == 'x':
            if self.rect.right >= self.end_pos[0] and self.direction.x == 1:
                self.direction.x = -1
                self.rect.right = self.end_pos[0]
            if self.rect.left <= self.start_pos[0] and self.direction.x == -1:
                self.direction.x = 1
                self.rect.left = self.start_pos[0]
        else: 
            if self.rect.bottom >= self.end_pos[1] and self.direction.y == 1:
                self.direction.y = -1
                self.rect.bottom = self.end_pos[1]
            if self.rect.top <= self.start_pos[1] and self.direction.y == -1:
                self.direction.y = 1
                self.rect.top = self.start_pos[1]

    def update(self, dt):
        self.old_rect = self.rect.copy()
        self.rect.topleft += self.direction * self.speed * dt
        self.check_border()

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

class Spike(Sprite):
    def __init__(self, pos, surf, *groups):
        super().__init__(pos, surf, *groups)
        self.rect.bottom = pos[1] + TILE_SIZE
        self.old_rect = self.rect.copy()

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

class TimerButton(Sprite):
    def __init__(self, pos, size, target_id, timer_ms, *groups):
        surf = pygame.Surface(size)
        surf.fill((255, 0, 0))
        super().__init__(pos, surf, *groups)

        self.base_rect = self.rect.copy()
        self.target_id = target_id
        self.target_laser = None

        from .timer import Timer
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