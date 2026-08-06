from enum import Enum, auto
from .settings import *
from .timer import Timer

class PlayerStateID(Enum):
    IDLE = auto()
    RUN = auto()
    FALL = auto()
    JUMP = auto()
    # WALL_JUMP = auto()

class PlayerState:
    def __init__(self, player):
        self.player = player

    def enter(self):
        pass

    def handle_input(self, keys):
        pass

    def update(self, dt):
        return None

class IdleState(PlayerState):
    def handle_input(self, keys):
        input_vector = Vector2(0,0)
        if keys[pygame.K_RIGHT]: input_vector.x += 1
        if keys[pygame.K_LEFT]: input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if keys[pygame.K_SPACE] and self.player.on_surface['floor']:
            self.player.jump = True

    def update(self, dt):
        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height
            self.player.rect.bottom -= 8
            return PlayerStateID.JUMP

        if not self.player.on_surface['floor']:
            return PlayerStateID.FALL

        if self.player.direction.x != 0:
            return PlayerStateID.RUN

class RunState(PlayerState):
    def handle_input(self, keys):
        input_vector = Vector2(0,0)
        if keys[pygame.K_RIGHT]: input_vector.x += 1
        if keys[pygame.K_LEFT]: input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if keys[pygame.K_SPACE] and self.player.on_surface['floor']:
            self.player.jump = True

    def update(self, dt):
        self.player.rect.x += self.player.direction.x * self.player.speed * dt
        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height
            self.player.rect.bottom -= 8
            return PlayerStateID.JUMP

        if not self.player.on_surface['floor']:
            return PlayerStateID.FALL

        if self.player.direction.x == 0:
            return PlayerStateID.IDLE

class FallState(PlayerState):
    def handle_input(self, keys):
        input_vector = Vector2(0,0)
        if keys[pygame.K_RIGHT]: input_vector.x += 1
        if keys[pygame.K_LEFT]: input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0

    def update(self, dt):
        self.player.rect.x += self.player.direction.x * self.player.speed * dt
        
        self.player.direction.y += self.player.gravity / 2 * dt
        self.player.rect.y += self.player.direction.y * dt
        self.player.direction.y += self.player.gravity / 2 * dt

        if self.player.on_surface['floor']:
            self.player.direction.y = 0
            if self.player.direction.x != 0:
                return PlayerStateID.RUN
            return PlayerStateID.IDLE

class JumpState(PlayerState):
    def handle_input(self, keys):
        input_vector = Vector2(0,0)
        if keys[pygame.K_RIGHT]: input_vector.x += 1
        if keys[pygame.K_LEFT]: input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0

    def update(self, dt):
        self.player.rect.x += self.player.direction.x * self.player.speed * dt

        self.player.direction.y += self.player.gravity / 2 * dt
        self.player.rect.y += self.player.direction.y * dt
        self.player.direction.y += self.player.gravity / 2 * dt

        if self.player.direction.y >= 0:
            return PlayerStateID.FALL

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, surf, collision_group_check, semicollidable_group_check, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface(surf)
        self.image.fill(RED)
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()

        self.direction = Vector2(0,0)
        self.speed = 300
        self.gravity = 2400
        self.jump = False
        self.jump_height = 1125

        self.collision_sprites = collision_group_check
        self.semi_collision_sprites = semicollidable_group_check
        self.on_surface = {'floor': False, 'left': False, 'right': False}
        self.platform = None

        # self.display_surface = pygame.display.get_surface()
        self.timers = {
            'wall_jump': Timer(500),
            'wall_jump_block': Timer(250),
            'fall_platform': Timer(250),
        }

        self.states = {
            PlayerStateID.IDLE: IdleState(self),
            PlayerStateID.RUN: RunState(self),
            PlayerStateID.FALL: FallState(self),
            PlayerStateID.JUMP: JumpState(self),
        }

        self.current_state = self.states[PlayerStateID.IDLE]

    def change_state(self, new_state_id):
        if self.current_state != self.states[new_state_id]:
            self.current_state = self.states[new_state_id]
            self.current_state.enter()

    def update(self, dt):
        self.old_rect = self.rect.copy()

        keys = pygame.key.get_pressed()
        self.current_state.handle_input(keys)

        self.platform_move(dt)

        new_state_id = self.current_state.update(dt)
        if new_state_id:
            self.change_state(new_state_id)


        self.update_timers()
        self.collision('horizontal')
        self.collision('vertical')
        self.check_contact()

        print(self.current_state)

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def platform_move(self, dt):
        if self.platform:
            self.rect.topleft += self.platform.direction * self.platform.speed * dt

    def check_contact(self):
        floor_rect = pygame.Rect(self.rect.bottomleft, (self.rect.width,8))
        right_rect = pygame.Rect(self.rect.topright + Vector2(0, self.rect.height / 4), (8, self.rect.height / 2))
        left_rect = pygame.Rect(self.rect.topleft + Vector2(-8, self.rect.height / 4), (8, self.rect.height / 2))
        collide_rects = [sprite.rect for sprite in self.collision_sprites]
        semi_collide_rects = [sprite.rect for sprite in self.semi_collision_sprites]

        # pygame.draw.rect(self.display_surface, YELLOW, floor_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, right_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, left_rect)

        self.on_surface['floor'] = True if floor_rect.collidelist(collide_rects) >= 0 or floor_rect.collidelist(semi_collide_rects) >= 0 and self.direction.y >= 0 else False
        self.on_surface['right'] = True if right_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['left'] = True if left_rect.collidelist(collide_rects) >= 0 else False
        # print(self.on_surface)

        self.platform = None
        sprites = self.collision_sprites.sprites() + self.semi_collision_sprites.sprites()
        for sprite in [sprite for sprite in sprites if hasattr(sprite, 'moving')]:
            if sprite.rect.colliderect(floor_rect):
                self.platform = sprite

    def collision(self, axis):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if axis == 'horizontal':
                    if self.rect.left <= sprite.rect.right and int(self.old_rect.left) >= int(sprite.old_rect.right):
                        self.rect.left = sprite.rect.right
                    if self.rect.right >= sprite.rect.left and int(self.old_rect.right) <= int(sprite.old_rect.left):
                        self.rect.right = sprite.rect.left
                else:
                    if self.rect.top <= sprite.rect.bottom and int(self.old_rect.top) >= int(sprite.old_rect.bottom):
                        self.rect.top = sprite.rect.bottom
                        if hasattr(sprite, 'moving'):
                            self.rect.top += 8
                    if self.rect.bottom >= sprite.rect.top and int(self.old_rect.bottom) <= int(sprite.old_rect.top):
                        self.rect.bottom = sprite.rect.top
                    self.direction.y = 0

    def semi_collision(self):
        if not self.timers['fall_platform'].active:
            for sprite in self.semi_collision_sprites:
                if sprite.rect.colliderect(self.rect):
                    if self.rect.bottom >= sprite.rect.top and int(self.old_rect.bottom) <= int(sprite.old_rect.top):
                        self.rect.bottom = sprite.rect.top
                        if self.direction.y > 0:
                            self.direction.y = 0
