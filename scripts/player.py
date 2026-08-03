from .settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, surf, collision_check_group, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface(surf)
        self.image.fill(RED)
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()
        self.collision_sprites = collision_check_group
        self.on_surface = {'floor': False, 'left': False, 'right': False}

        self.direction = Vector2(0,0)
        self.speed = 300
        self.gravity = 2400
        self.jump = False
        self.jump_height = 1050

        self.display_surface = pygame.display.get_surface()

    def input(self):
        keys = pygame.key.get_pressed()
        input_vector = Vector2(0,0)
        if keys[pygame.K_RIGHT]:
            input_vector.x += 1
        if keys[pygame.K_LEFT]:
            input_vector.x -= 1
        self.direction.x = input_vector.normalize().x if input_vector else input_vector.x

        if keys[pygame.K_SPACE]:
            self.jump = True

    def move(self, dt):
        self.rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')

        if not self.on_surface['floor'] and any((self.on_surface['left'], self.on_surface['right'])):
            self.direction.y = 0
            self.rect.y += self.gravity / 16 * dt
        else:
            self.direction.y += self.gravity / 2 * dt
            self.rect.y += self.direction.y * dt
            self.direction.y += self.gravity / 2 * dt

        self.collision('vertical')

        if self.jump:
            if self.on_surface['floor']:
                self.direction.y = -self.jump_height
            elif any((self.on_surface['left'], self.on_surface['right'])):
                self.direction.y = -self.jump_height
                self.direction.x = 1 if self.on_surface['left'] else -1
            self.jump = False

    def check_contact(self):
        floor_rect = pygame.Rect(self.rect.bottomleft, (self.rect.width,8))
        right_rect = pygame.Rect(self.rect.topright + Vector2(0, self.rect.height / 4), (8, self.rect.height / 2))
        left_rect = pygame.Rect(self.rect.topleft + Vector2(-8, self.rect.height / 4), (8, self.rect.height / 2))
        collide_rects = [sprite.rect for sprite in self.collision_sprites]

        # pygame.draw.rect(self.display_surface, YELLOW, floor_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, right_rect)
        # pygame.draw.rect(self.display_surface, YELLOW, left_rect)

        self.on_surface['floor'] = True if floor_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['right'] = True if right_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['left'] = True if left_rect.collidelist(collide_rects) >= 0 else False
        # print(self.on_surface)

    def collision(self, axis):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if axis == 'horizontal':
                    if self.rect.left <= sprite.rect.right and self.old_rect.left >= sprite.old_rect.right:
                        self.rect.left = sprite.rect.right
                    if self.rect.right >= sprite.rect.left and self.old_rect.right <= sprite.old_rect.left:
                        self.rect.right = sprite.rect.left
                else:
                    if self.rect.top <= sprite.rect.bottom and self.old_rect.top >= sprite.old_rect.bottom:
                        self.rect.top = sprite.rect.bottom
                    if self.rect.bottom >= sprite.rect.top and self.old_rect.bottom <= sprite.old_rect.top:
                        self.rect.bottom = sprite.rect.top
                    self.direction.y = 0

    def update(self, dt):
        self.old_rect = self.rect.copy()
        self.input()
        self.move(dt)
        self.check_contact()