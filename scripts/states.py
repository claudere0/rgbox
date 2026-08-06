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
                self.game.change_state(StateID.LEVEL_SELECT)
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
        self.tmx_maps = {0: load_pygame(join('data', 'levels', 'demo.tmx'))}
        self.current_stage = Level(self.tmx_maps[0])

    def update(self, dt):
        self.current_stage.update(dt)

    def draw(self, screen):
        self.current_stage.draw(screen)
        # screen.fill(GREEN)

# PAUSE -> PLAYING/SETTINGS/MENU

class PauseState(State):
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
