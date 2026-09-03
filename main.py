import asyncio
from scripts.settings import *
from scripts.states import *
from scripts.save_manager import SaveManager
from scripts.audio import AudioManager

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

    async def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update(dt)
            self.draw(self.screen)
            await asyncio.sleep(0)

        pygame.quit()

async def main():
    game = Game()
    await game.run()

if __name__ == '__main__':
    asyncio.run(main())
