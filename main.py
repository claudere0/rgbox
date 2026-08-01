from scripts.settings import *
from scripts.states import *

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