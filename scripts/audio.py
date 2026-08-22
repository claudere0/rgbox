import pygame
import os
from os.path import join

class AudioManager:
    def __init__(self):
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
            'jump': 'jump.wav',
            'dash': 'dash.wav',
            'death': 'death.wav',
            'color': 'color_change.wav',
            'secret': 'secret.wav',
            'portal': 'portal.wav'
        }
        
        for name, filename in sfx_files.items():
            path = join('audio', 'sfx', filename)
            if os.path.exists(path):
                self.sfx[name] = pygame.mixer.Sound(path)
            else:
                self.sfx[name] = None
                print(f"Warning: Audio missing -> {path}")

    def play_sfx(self, name):
        if name in self.sfx and self.sfx[name]:
            self.sfx[name].set_volume(self.sfx_volume)
            self.sfx[name].play()

    def play_music(self, filename, loops=-1, fade_ms=2000):
        path = join(self.music_path, filename)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            # fade_ms плавно наращивает громкость
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
        else:
            print(f"Warning: Music missing -> {path}")

    def stop_music(self, fade_ms=1000):
        pygame.mixer.music.fadeout(fade_ms)