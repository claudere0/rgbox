from .settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, surf, *groups):
        super().__init__(*groups)
        self.image = pygame.Surface(surf)
        self.image.fill(RED)
        self.rect = self.image.get_frect(topleft = pos)

    def input(self):
        pass

    def move(self):
        pass

    def update(self):
        self.input()
        self.move()