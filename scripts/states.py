from .settings import *
from enum import Enum, auto

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
        # screen.fill(BLACK)

        # pygame.display.flip()

# MENU -> LEVEL_SELECT or SETTINGS

# LEVEL_SELECT -> PLAYING or MENU

# PLAYING -> PAUSE (ESCAPE) or GAME_OVER/LEVEL_COMPLETE

# PAUSE -> PLAYING/SETTINGS/MENU

# GAME_OVER -> restart PLAYING or quit to MENU

# LEVEL_COMPLETE -> play next level PLAYING(retry or load next level) or quit to MENU

# SETTINGS -> go back to MENU/PAUSE
