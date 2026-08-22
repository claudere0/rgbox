import pygame
import math
import random
from pygame.math import Vector2

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

LEVEL_ORDER = [
    "tutorial_zero",
    "tutorial_one",
    "level_zero",
    "level_one",
    "level_two",
    "level_three"
]
