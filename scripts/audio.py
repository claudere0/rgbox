import pygame
import os
from os.path import join

class AudioManager:
    def __init__(self, game):
        self.game = game
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        
        self.sfx = {}
        self.music_path = join('audio', 'music')
        
        self.sfx_volume = 0.5
        self.music_volume = 0.3
        pygame.mixer.music.set_volume(self.music_volume)
        
        self.load_sfx()

    def load_sfx(self):
        sfx_files = {
            'jump': 'jump.mp3',
            'dash': 'dash.mp3',
            'death': 'death_arcade.wav', # can change to death_bubble.mp3
            'color': 'color_change.mp3',
            'secret': 'secret.wav',
            'portal': 'portal.wav'
            , 'button': 'button_press_unpress.mp3'        }
        
        for name, filename in sfx_files.items():
            path = join('audio', 'sfx', filename)
            if os.path.exists(path):
                self.sfx[name] = pygame.mixer.Sound(path)
            else:
                self.sfx[name] = None
                print(f"Warning: Audio missing -> {path}")

    def play_sfx(self, name):
        if name in self.sfx and self.sfx[name]:
            vol = self.game.save_manager.data["settings"].get("sfx_volume", 100) / 100.0
            self.sfx[name].set_volume(vol)
            self.sfx[name].play()

    def play_music(self, filename, loops=-1, fade_ms=2000):
        path = join(self.music_path, filename)
        if os.path.exists(path):
            pygame.mixer.music.load(path)

            vol = self.game.save_manager.data["settings"].get("music_volume", 100) / 100.0
            pygame.mixer.music.set_volume(vol)

            pygame.mixer.music.play(-1, fade_ms=fade_ms)
        else:
            print(f"Warning: Music missing -> {path}")

    def update_music_volume(self):
        vol = self.game.save_manager.data["settings"].get("music_volume", 100) / 100.0
        pygame.mixer.music.set_volume(vol)

    def stop_music(self, fade_ms=1000):
        pygame.mixer.music.fadeout(fade_ms)