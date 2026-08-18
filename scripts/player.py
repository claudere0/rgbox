from enum import Enum, auto
from .settings import *
from .sprites import ColorDoor
from .timer import Timer

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
        if keys[pygame.K_RIGHT]: input_vector.x += 1
        if keys[pygame.K_LEFT]: input_vector.x -= 1
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
        if keys[pygame.K_RIGHT]: input_vector.x += 1
        if keys[pygame.K_LEFT]: input_vector.x -= 1
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
            if keys[pygame.K_RIGHT]: input_vector.x += 1
            if keys[pygame.K_LEFT]: input_vector.x -= 1
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

            return PlayerStateID.JUMP

        if (self.player.on_surface['left'] and self.player.direction.x < 0) and self.player.pigments['B'] or \
           (self.player.on_surface['right'] and self.player.direction.x > 0) and self.player.pigments['B']:
            return PlayerStateID.WALL_SLIDE

        self.player.direction.y += self.player.gravity * dt * self.player.fall_gravity_modifier
        self.player.direction.y = min(self.player.direction.y, self.player.max_fall_speed)

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

        self.player.direction.y += self.player.gravity * dt * self.player.slide_gravity_modifier
        self.player.direction.y = min(self.player.direction.y, self.player.max_fall_speed / 8)

        if self.player.on_surface['floor']:
            return PlayerStateID.IDLE

        if self.player.on_surface['left'] and self.player.direction.x >= 0:
            return PlayerStateID.FALL

        if self.player.on_surface['right'] and self.player.direction.x <= 0:
            return PlayerStateID.FALL

        if not self.player.on_surface['left'] and not self.player.on_surface['right']:
            return PlayerStateID.FALL

class DashState(PlayerState):
    def enter(self):
        self.player.timers['dash'].activate()
        self.dash_dir = self.player.facing 

    def handle_input(self, keys, just_pressed):
        pass

    def update(self, dt):
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
    def __init__(self, pos, surf, collision_group_check, semicollidable_group_check, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface(surf)
        self.image.fill(WHITE)
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()

        self.direction = Vector2(0,0)
        self.speed = 300
        self.gravity = 2560 # earth 640px/s^2 but in games it should be bigger from 2-5 times
        self.jump = False
        self.jump_height = 1012
        self.fall_gravity_modifier = 2
        self.slide_gravity_modifier = 0.125
        self.max_fall_speed = 1600 # I wanted it to be 2560 means 48 px per second but it can cause a bugs cause my little paltforms has thickness of 32 i need less than 32 * 60 means less than 1920 (3/4 of 2560) and I choose 1600 (5/8 of 2560)
        self.can_double_jump = False
        self.can_dash = True
        self.facing = 1
        self.is_dashing = False

        self.collision_sprites = collision_group_check
        self.semi_collision_sprites = semicollidable_group_check
        self.on_surface = {'floor': False, 'left': False, 'right': False}
        self.platform = None

        # self.display_surface = pygame.display.get_surface()
        self.timers = {
            'wall_jump': Timer(500),
            'wall_jump_block': Timer(250),
            'dash': Timer(250),
            'dash_cooldown': Timer(250),
            'coyote': Timer(125),
            'death': Timer(500),
        }

        self.pigments = {'R': False, 'G': False, 'B': False}
        self.needs_respawn = False

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

        print(self.current_state)

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
        collide_rects = valid_collision_rects # before #51 commit was -> collide_rects = [sprite.rect for sprite in self.collision_sprites]

        semi_collide_rects = [sprite.rect for sprite in self.semi_collision_sprites]

        # pygame.draw.rect(self.display_surface, YELLOW, floor_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, right_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, left_rect)

        self.on_surface['floor'] = True if floor_rect.collidelist(collide_rects) >= 0 or floor_rect.collidelist(semi_collide_rects) >= 0 and self.direction.y >= 0 else False
        self.on_surface['right'] = True if right_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['left'] = True if left_rect.collidelist(collide_rects) >= 0 else False
        # print(self.on_surface)

        if self.on_surface['floor'] or self.on_surface['left'] or self.on_surface['right']:
            self.can_double_jump = self.pigments['G']
            self.can_dash = self.pigments['R']

    def update_color_and_size(self):
        count = sum(self.pigments.values())

        color = (
            255 if self.pigments['R'] else 0,
            255 if self.pigments['G'] else 0,
            255 if self.pigments['B'] else 0
        )

        new_size = (5 + 2 * count) * UNIT # UNIT = 8

        old_center = self.rect.center
        self.image = pygame.Surface((new_size, new_size))
        self.image.fill(color)

        self.rect = self.image.get_frect()
        self.rect.center = old_center

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

    # def semi_collision(self):
    #     if not self.timers['fall_platform'].active:
    #         for sprite in self.semi_collision_sprites:
    #             if sprite.rect.colliderect(self.rect):
    #                 if self.rect.bottom >= sprite.rect.top and int(self.old_rect.bottom) <= int(sprite.old_rect.top):
    #                     self.rect.bottom = sprite.rect.top
    #                     if self.direction.y > 0:
    #                         self.direction.y = 0
