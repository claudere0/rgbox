from enum import Enum, auto
from .settings import *
from .timer import Timer

class PlayerStateID(Enum):
    IDLE = auto()
    RUN = auto()
    FALL = auto()
    JUMP = auto()
    WALL_SLIDE = auto()

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
        if keys[pygame.K_RIGHT]: input_vector.x += 1
        if keys[pygame.K_LEFT]: input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if just_pressed[pygame.K_SPACE] and self.player.on_surface['floor']:
            self.player.jump = True

    def update(self, dt):
        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height
            self.player.rect.bottom -= 1
            return PlayerStateID.JUMP

        if not self.player.on_surface['floor']:
            return PlayerStateID.FALL

        if self.player.direction.x != 0:
            return PlayerStateID.RUN

class RunState(PlayerState):
    def handle_input(self, keys, just_pressed):
        input_vector = Vector2(0,0)
        if keys[pygame.K_RIGHT]: input_vector.x += 1
        if keys[pygame.K_LEFT]: input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if just_pressed[pygame.K_SPACE] and self.player.on_surface['floor']:
            self.player.jump = True

    def update(self, dt):
        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height
            self.player.rect.bottom -= 1
            return PlayerStateID.JUMP

        if not self.player.on_surface['floor']:
            return PlayerStateID.FALL

        if self.player.direction.x == 0:
            return PlayerStateID.IDLE

class FallState(PlayerState):
    def handle_input(self, keys, just_pressed):
        if not self.player.timers['wall_jump_block'].active:
            input_vector = Vector2(0,0)
            if keys[pygame.K_RIGHT]: input_vector.x += 1
            if keys[pygame.K_LEFT]: input_vector.x -= 1
            self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if just_pressed[pygame.K_SPACE] and self.player.can_double_jump:
            self.player.can_double_jump = False
            self.player.jump = True

    def update(self, dt):
        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height

            return PlayerStateID.JUMP

        if (self.player.on_surface['left'] and self.player.direction.x < 0) or \
           (self.player.on_surface['right'] and self.player.direction.x > 0):
            return PlayerStateID.WALL_SLIDE

        self.player.direction.y += self.player.gravity * dt

        if self.player.on_surface['floor']:
            self.player.direction.y = 0
            if self.player.direction.x != 0:
                return PlayerStateID.RUN
            return PlayerStateID.IDLE

class JumpState(PlayerState):
    def handle_input(self, keys, just_pressed):
        if not self.player.timers['wall_jump_block'].active:
            input_vector = Vector2(0,0)
            if keys[pygame.K_RIGHT]: input_vector.x += 1
            if keys[pygame.K_LEFT]: input_vector.x -= 1
            self.player.direction.x = input_vector.normalize().x if input_vector else 0

        if just_pressed[pygame.K_SPACE] and self.player.can_double_jump:
            self.player.can_double_jump = False
            self.player.jump = True

    def update(self, dt):
        if self.player.jump:
            self.player.jump = False
            self.player.direction.y = -self.player.jump_height

            return PlayerStateID.JUMP

        if (self.player.on_surface['left'] and self.player.direction.x < 0) or \
           (self.player.on_surface['right'] and self.player.direction.x > 0):
            return PlayerStateID.WALL_SLIDE

        self.player.direction.y += self.player.gravity* dt

        if self.player.direction.y >= 0:
            return PlayerStateID.FALL

class WallSlideState(PlayerState):
    def handle_input(self, keys, just_pressed):
        input_vector = Vector2(0,0)
        if keys[pygame.K_RIGHT]: input_vector.x += 1
        if keys[pygame.K_LEFT]: input_vector.x -= 1
        self.player.direction.x = input_vector.normalize().x if input_vector else 0
        if just_pressed[pygame.K_SPACE]:
            self.player.jump = True

    def update(self, dt):
        if self.player.jump:
            self.player.jump = False

            self.player.direction.y = -self.player.jump_height

            self.player.direction.x = 1 if self.player.on_surface['left'] else -1

            self.player.timers['wall_jump_block'].activate()

            return PlayerStateID.JUMP

        self.player.direction.y = 150

        if self.player.on_surface['floor']:
            return PlayerStateID.IDLE

        if self.player.on_surface['left'] and self.player.direction.x >= 0:
            return PlayerStateID.FALL

        if self.player.on_surface['right'] and self.player.direction.x <= 0:
            return PlayerStateID.FALL

        if not self.player.on_surface['left'] and not self.player.on_surface['right']:
            return PlayerStateID.FALL


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, surf, collision_group_check, semicollidable_group_check, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface(surf)
        self.image.fill(WHITE)
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()

        self.direction = Vector2(0,0)
        self.speed = 300
        self.gravity = 2400
        self.jump = False
        self.jump_height = 1125
        self.can_double_jump = False

        self.collision_sprites = collision_group_check
        self.semi_collision_sprites = semicollidable_group_check
        self.on_surface = {'floor': False, 'left': False, 'right': False}
        self.platform = None

        # self.display_surface = pygame.display.get_surface()
        self.timers = {
            'wall_jump': Timer(500),
            'wall_jump_block': Timer(250),
        }

        self.states = {
            PlayerStateID.IDLE: IdleState(self),
            PlayerStateID.RUN: RunState(self),
            PlayerStateID.FALL: FallState(self),
            PlayerStateID.JUMP: JumpState(self),
            PlayerStateID.WALL_SLIDE: WallSlideState(self),
        }

        self.current_state = self.states[PlayerStateID.IDLE]

    def change_state(self, new_state_id):
        if self.current_state != self.states[new_state_id]:
            self.current_state = self.states[new_state_id]
            self.current_state.enter()

    def update(self, dt):
        self.old_rect = self.rect.copy()

        keys = pygame.key.get_pressed()
        just_pressed = pygame.key.get_just_pressed()

        self.current_state.handle_input(keys, just_pressed)

        new_state_id = self.current_state.update(dt)
        if new_state_id:
            self.change_state(new_state_id)

        self.rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.rect.y += self.direction.y * dt
        self.collision('vertical')

        self.update_timers()
        self.check_contact()

        print(self.current_state)

    def update_timers(self):
        for timer in self.timers.values():
            timer.update()

    def check_contact(self):
        floor_rect = pygame.Rect(self.rect.bottomleft, (self.rect.width,8))
        right_rect = pygame.Rect(self.rect.topright + Vector2(0, self.rect.height / 8), (8, self.rect.height / 2))
        left_rect = pygame.Rect(self.rect.topleft + Vector2(-1, self.rect.height / 8), (8, self.rect.height / 2))
        collide_rects = [sprite.rect for sprite in self.collision_sprites]
        semi_collide_rects = [sprite.rect for sprite in self.semi_collision_sprites]

        # pygame.draw.rect(self.display_surface, YELLOW, floor_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, right_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, left_rect)

        self.on_surface['floor'] = True if floor_rect.collidelist(collide_rects) >= 0 or floor_rect.collidelist(semi_collide_rects) >= 0 and self.direction.y >= 0 else False
        self.on_surface['right'] = True if right_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['left'] = True if left_rect.collidelist(collide_rects) >= 0 else False
        # print(self.on_surface)

        if self.on_surface['floor'] or self.on_surface['left'] or self.on_surface['right']:
            self.can_double_jump = True

    def collision(self, axis):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
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

    # def semi_collision(self):
    #     if not self.timers['fall_platform'].active:
    #         for sprite in self.semi_collision_sprites:
    #             if sprite.rect.colliderect(self.rect):
    #                 if self.rect.bottom >= sprite.rect.top and int(self.old_rect.bottom) <= int(sprite.old_rect.top):
    #                     self.rect.bottom = sprite.rect.top
    #                     if self.direction.y > 0:
    #                         self.direction.y = 0
