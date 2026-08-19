from enum import Enum, auto
from pytmx.util_pygame import load_pygame
from os.path import join
from .settings import *
from .level import Level

class StateID(Enum):
    MENU = auto()
    LEVEL_SELECT = auto()
    PLAYING = auto()
    PAUSE = auto()
    GAME_OVER = auto()
    LEVEL_COMPLETE = auto()
    SETTINGS = auto()

class State:
    def __init__(self, game):
        self.game = game

    def events(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

# MENU -> LEVEL_SELECT or SETTINGS

class MenuState(State):
    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # self.game.change_state(StateID.LEVEL_SELECT)
                self.game.states[StateID.PLAYING].load_level("tutorial_zero")
            if event.key == pygame.K_s:
                self.game.change_state(StateID.SETTINGS)
            if event.key == pygame.K_q:
                self.game.running = False

    def draw(self, screen):
        screen.fill(BLACK)

# LEVEL_SELECT -> PLAYING or MENU

class LevelSelectState(State):
    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(StateID.MENU)

    def draw(self, screen):
        screen.fill(BLUE)

# PLAYING -> PAUSE (ESCAPE) or GAME_OVER/LEVEL_COMPLETE

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)
        self.current_stage = None
        self.current_level_name = ""
        self.start_time = 0 

    def load_level(self, level_name):
        self.current_level_name = level_name
        tmx_map = load_pygame(join('data', 'levels', f'{level_name}.tmx'))
        self.current_stage = Level(tmx_map)

        self.start_time = pygame.time.get_ticks()
        self.game.change_state(StateID.PLAYING)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(StateID.PAUSE)

    def update(self, dt):
        if self.current_stage:
            self.current_stage.update(dt)
            if hasattr(self.current_stage, 'is_completed') and self.current_stage.is_completed:
                final_time_ms = pygame.time.get_ticks() - self.start_time

                is_new_record = self.game.save_manager.save_best_time(self.current_level_name, final_time_ms)
                self.game.save_manager.unlock_level("tutorial_one") 

                self.game.change_state(StateID.LEVEL_COMPLETE)

    def draw(self, screen):
        if self.current_stage:
            self.current_stage.draw(screen)

            current_time_ms = pygame.time.get_ticks() - self.start_time
            seconds = (current_time_ms // 1000) % 60
            minutes = (current_time_ms // 60000) % 60
            millis = (current_time_ms % 1000) // 10
            
            font = pygame.font.SysFont(None, 36)

            time_text = font.render(f"TIME: {minutes:02d}:{seconds:02d}:{millis:02d}", True, (255, 0, 0))
            screen.blit(time_text, (20, 20))

# PAUSE -> PLAYING/SETTINGS/MENU

class PauseState(State):
    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(StateID.MENU)

    def draw(self, screen):
        screen.fill(CYAN)

# GAME_OVER -> restart PLAYING or quit to MENU

class GameOverState(State):
    def draw(self, screen):
        screen.fill(RED)

# LEVEL_COMPLETE -> play next level PLAYING(retry or load next level) or quit to MENU

class LevelCompleteState(State):
    def draw(self, screen):
        screen.fill(YELLOW)

# SETTINGS -> go back to MENU/PAUSE

class SettingsState(State):
    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(StateID.MENU)

    def draw(self, screen):
        screen.fill(WHITE)
