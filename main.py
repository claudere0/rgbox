import pygame

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

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('rgbox')
        self.clock = pygame.time.Clock()
        self.running = True

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_q:
                    self.running = False

    def update(self, dt):
        pass

    def draw(self, screen):
        screen.fill(BLACK)

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update(dt)
            self.draw(self.screen)

        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()