from .settings import *

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

