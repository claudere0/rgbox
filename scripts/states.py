import pygame
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
    LEVEL_COMPLETE = auto()
    SETTINGS = auto()
    SECRETS = auto()

class State:
    def __init__(self, game):
        self.game = game

    def events(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass

# MENU -> LEVEL_SELECT or SECRETS or SETTINGS

class MenuState(State):
    def enter(self):
        self.game.audio.play_music('menu.mp3', fade_ms=2000)

    def __init__(self, game):
        super().__init__(game)
        self.game.audio.play_music('menu.mp3', fade_ms=2000)
        self.options = ["PLAY", "SECRETS", "SETTINGS", "QUIT"]
        self.selected_index = 0
        self.font_large = pygame.font.SysFont('courier', 64)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)

            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key == pygame.K_RETURN:
                selected = self.options[self.selected_index]
                if selected == "PLAY":
                    self.game.change_state(StateID.LEVEL_SELECT)

                elif selected == "SECRETS":
                    self.game.change_state(StateID.SECRETS)

                elif selected == "SETTINGS":
                    self.game.change_state(StateID.SETTINGS)

                elif selected == "QUIT":
                    self.game.running = False

    def draw(self, screen):
        screen.fill(BLACK)

        for i, option in enumerate(self.options):
            if i == self.selected_index:
                color = YELLOW
                text = f"> {option} <"
            else:
                color = WHITE
                text = option
                
            img = self.font_large.render(text, True, color)
            rect = img.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 64 + i * 64))
            screen.blit(img, rect)

# LEVEL_SELECT -> PLAYING or MENU

class LevelSelectState(State):
    def __init__(self, game):
        super().__init__(game)
        self.selected_index = 0
        self.font_main = pygame.font.SysFont('courier', 48, bold=True)
        self.font_small = pygame.font.SysFont('courier', 24)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.change_state(StateID.MENU)

            elif event.key == pygame.K_UP:
                if self.selected_index > 0:
                    self.selected_index -= 1

            elif event.key == pygame.K_DOWN:
                if self.selected_index < len(LEVEL_ORDER) - 1:
                    self.selected_index += 1

            elif event.key == pygame.K_RETURN:
                level_name = LEVEL_ORDER[self.selected_index]
                if self.game.save_manager.is_level_unlocked(level_name):
                    self.game.states[StateID.PLAYING].load_level(level_name)

    def draw(self, screen):
        screen.fill(BLUE)

        center_y = WINDOW_HEIGHT / 2
        spacing = 96
        
        for i, level_name in enumerate(LEVEL_ORDER):
            offset = i - self.selected_index 
            is_unlocked = self.game.save_manager.is_level_unlocked(level_name)

            if i == self.selected_index:
                if is_unlocked:
                    color = YELLOW
                    display_name = level_name.upper()
                else:
                    color = (255, 255, 255)
                    display_name = "??? (LOCKED)"

                title_img = self.font_main.render(display_name, True, color)
                title_rect = title_img.get_frect(center=(WINDOW_WIDTH / 2, center_y))
                screen.blit(title_img, title_rect)

                if is_unlocked:
                    best_time = self.game.save_manager.data["best_times"].get(level_name, None)
                    if best_time is not None:
                        seconds = (best_time // 1000) % 60
                        minutes = (best_time // 60000) % 60
                        millis = (best_time % 1000) // 10
                        time_text = f"BEST TIME: {minutes:02d}:{seconds:02d}:{millis:02d}"
                    else:
                        time_text = "NOT COMPLETED YET"
                        
                    time_img = self.font_small.render(time_text, True, WHITE)
                    time_rect = time_img.get_frect(center=(WINDOW_WIDTH / 2, center_y + 48))
                    screen.blit(time_img, time_rect)
                
            else:
                if is_unlocked:
                    color = (255, 255, 255)
                    display_name = level_name.upper()
                else:
                    color = (0, 0, 0) # Темно-серый
                    display_name = "???"
                    
                title_img = self.font_small.render(display_name, True, color)
                title_rect = title_img.get_frect(center=(WINDOW_WIDTH / 2, center_y + (offset * spacing)))
                screen.blit(title_img, title_rect)

# PLAYING -> PAUSE (ESCAPE) or LEVEL_COMPLETE

class PlayingState(State):
    def __init__(self, game):
        super().__init__(game)
        self.current_stage = None
        self.current_level_name = ""
        self.start_time = 0 
        self.last_run_time = 0
        self.pause_start_time = 0

    def load_level(self, level_name):
        self.current_level_name = level_name
        tmx_map = load_pygame(join('data', 'levels', f'{level_name}.tmx'))

        self.current_stage = Level(tmx_map, self)

        self.start_time = pygame.time.get_ticks()
        self.game.audio.play_music('magiksolo-investigation-puzzle.mp3', fade_ms=1000)
        self.game.change_state(StateID.PLAYING)

    def resume_timer(self):
        pause_duration = pygame.time.get_ticks() - self.pause_start_time
        self.start_time += pause_duration

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.pause_start_time = pygame.time.get_ticks()
                self.game.change_state(StateID.PAUSE)

    def update(self, dt):
        if self.current_stage:
            self.current_stage.update(dt)
            
            if hasattr(self.current_stage, 'is_completed') and self.current_stage.is_completed:
                final_time_ms = pygame.time.get_ticks() - self.start_time
                self.last_run_time = final_time_ms

                is_new_record = self.game.save_manager.save_best_time(self.current_level_name, final_time_ms)

                if self.current_level_name in LEVEL_ORDER:
                    current_idx = LEVEL_ORDER.index(self.current_level_name)
                    if current_idx + 1 < len(LEVEL_ORDER):
                        next_level_name = LEVEL_ORDER[current_idx + 1]
                        self.game.save_manager.unlock_level(next_level_name)

                self.game.change_state(StateID.LEVEL_COMPLETE)

    def draw(self, screen):
        if self.current_stage:
            self.current_stage.draw(screen)

            if self.game.current_state == self:
                current_time_ms = pygame.time.get_ticks() - self.start_time
            else:
                current_time_ms = self.pause_start_time - self.start_time

            seconds = (current_time_ms // 1000) % 60
            minutes = (current_time_ms // 60000) % 60
            millis = (current_time_ms % 1000) // 10
            
            font = pygame.font.SysFont('courier', 32)

            time_text = font.render(f"TIME: {minutes:02d}:{seconds:02d}:{millis:02d}", True, (0, 255, 0))
            screen.blit(time_text, (screen.width - (time_text.width + 64), 64)) #y = screen.height - (time_text.height + 64))

# PAUSE -> PLAYING/SETTINGS/MENU

class PauseState(State):
    def __init__(self, game):
        super().__init__(game)
        self.options = ["RESUME", "RESTART LEVEL", "MENU"]
        self.selected_index = 0
        self.font_huge = pygame.font.SysFont('courier', 64, bold=True)
        self.font_large = pygame.font.SysFont('courier', 48, bold=True)

        self.overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 127))

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.states[StateID.PLAYING].resume_timer()
                self.game.change_state(StateID.PLAYING)

            elif event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)

            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key == pygame.K_RETURN:
                selected = self.options[self.selected_index]
                playing_state = self.game.states[StateID.PLAYING]
                
                if selected == "RESUME":
                    playing_state.resume_timer()
                    self.game.change_state(StateID.PLAYING)

                elif selected == "RESTART LEVEL":
                    playing_state.load_level(playing_state.current_level_name)

                elif selected == "MENU":
                    self.game.change_state(StateID.MENU)

    def draw(self, screen):
        self.game.states[StateID.PLAYING].draw(screen)
        screen.blit(self.overlay, (0, 0))

        title = self.font_huge.render("PAUSED", True, WHITE)
        title_rect = title.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 64))
        screen.blit(title, title_rect)

        for i, option in enumerate(self.options):
            if i == self.selected_index:
                color = YELLOW
                text = f"> {option} <" 
            else:
                color = WHITE
                text = option
                
            img = self.font_large.render(text, True, color)
            rect = img.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + i * 64))
            screen.blit(img, rect)

# LEVEL_COMPLETE -> play next level PLAYING(retry or load next level) or quit to MENU

class LevelCompleteState(State):
    def enter(self):
        pygame.mixer.music.fadeout(1000)

    def __init__(self, game):
        super().__init__(game)
        self.options = ["NEXT LEVEL", "RETRY", "MENU"]
        self.selected_index = 0
        self.font_huge = pygame.font.SysFont('courier', 64, bold=True)
        self.font_large = pygame.font.SysFont('courier', 48, bold=True)
        self.font_small = pygame.font.SysFont('courier', 32)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)

            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key == pygame.K_RETURN:
                selected = self.options[self.selected_index]
                playing_state = self.game.states[StateID.PLAYING]
                
                if selected == "NEXT LEVEL":
                    current_level = playing_state.current_level_name
                    if current_level in LEVEL_ORDER:
                        idx = LEVEL_ORDER.index(current_level)
                        if idx + 1 < len(LEVEL_ORDER):
                            next_level = LEVEL_ORDER[idx + 1]
                            playing_state.load_level(next_level)

                        else:
                            self.game.change_state(StateID.MENU) 
                            
                elif selected == "RETRY":
                    playing_state.load_level(playing_state.current_level_name)
                    
                elif selected == "MENU":
                    self.game.change_state(StateID.MENU)

    def draw(self, screen):
        screen.fill(YELLOW)

        title = self.font_huge.render("LEVEL COMPLETE", True, BLACK)
        title_rect = title.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 96))
        screen.blit(title, title_rect)

        playing_state = self.game.states[StateID.PLAYING]
        run_time = playing_state.last_run_time
        seconds = (run_time // 1000) % 60
        minutes = (run_time // 60000) % 60
        millis = (run_time % 1000) // 10
        
        time_text = self.font_small.render(f"YOUR TIME: {minutes:02d}:{seconds:02d}:{millis:02d}", True, RED)
        time_rect = time_text.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 32))
        screen.blit(time_text, time_rect)

        for i, option in enumerate(self.options):
            if i == self.selected_index:
                color = BLACK
                text = f"> {option} <" 
            else:
                color = RED
                text = option
                
            img = self.font_large.render(text, True, color)
            rect = img.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 32 + i * 64))
            screen.blit(img, rect)

# SETTINGS -> go back to MENU/PAUSE

class SettingsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.options = ["FULLSCREEN", "MINIMALIST", "MUSIC VOL", "SFX VOL", "BACK"]
        self.selected_index = 0
        self.font_large = pygame.font.SysFont('courier', 48, bold=True)
        self.font_huge = pygame.font.SysFont('courier', 64, bold=True)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.options)

            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                selected = self.options[self.selected_index]
                step = -10 if event.key == pygame.K_LEFT else 10
                if selected == "MUSIC VOL":
                    vol = self.game.save_manager.data["settings"].get("music_volume", 100)
                    new_vol = max(0, min(100, vol + step))
                    self.game.save_manager.data["settings"]["music_volume"] = new_vol
                    self.game.save_manager.save()
                    self.game.audio.update_music_volume()

                elif selected == "SFX VOL":
                    vol = self.game.save_manager.data["settings"].get("sfx_volume", 100)
                    new_vol = max(0, min(100, vol + step))
                    self.game.save_manager.data["settings"]["sfx_volume"] = new_vol
                    self.game.save_manager.save()
                    self.game.audio.play_sfx('jump')

            elif event.key == pygame.K_RETURN:
                selected = self.options[self.selected_index]
                if selected == "FULLSCREEN":
                    current_val = self.game.save_manager.data["settings"]["fullscreen"]
                    self.game.save_manager.data["settings"]["fullscreen"] = not current_val
                    self.game.save_manager.save()
                    pygame.display.toggle_fullscreen()

                elif selected == "MINIMALIST":
                    current_val = self.game.save_manager.data["settings"].get("minimalist", False)
                    self.game.save_manager.data["settings"]["minimalist"] = not current_val
                    self.game.save_manager.save()

                elif selected == "BACK":
                    self.game.change_state(StateID.MENU)

    def draw(self, screen):
        screen.fill(BLACK)

        title = self.font_huge.render("SETTINGS", True, WHITE)
        title_rect = title.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 160))
        screen.blit(title, title_rect)

        for i, option in enumerate(self.options):
            display_text = option
            if option == "FULLSCREEN":
                is_on = self.game.save_manager.data["settings"]["fullscreen"]
                display_text = f"FULLSCREEN [{'ON' if is_on else 'OFF'}]"

            elif option == "MINIMALIST":
                is_on = self.game.save_manager.data["settings"].get("minimalist", False)
                display_text = f"MINIMALIST [{'ON' if is_on else 'OFF'}]"

            elif option == "MUSIC VOL":
                vol = self.game.save_manager.data["settings"].get("music_volume", 100)
                display_text = f"MUSIC VOL < {vol}% >"

            elif option == "SFX VOL":
                vol = self.game.save_manager.data["settings"].get("sfx_volume", 100)
                display_text = f"SFX VOL   < {vol}% >"

            color = YELLOW if i == self.selected_index else WHITE
            text = f"> {display_text} <" if i == self.selected_index else display_text
            img = self.font_large.render(text, True, color)
            rect = img.get_frect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 - 24 + i * 64))
            screen.blit(img, rect)

# SECRETS -> MENU

class SecretsState(State):
    def __init__(self, game):
        super().__init__(game)
        self.font_title = pygame.font.SysFont('courier', 64, bold=True)
        self.font_name = pygame.font.SysFont('courier', 32)

        self.cameo_names = ["NINJA", "ELUETTE", "RAPPY", "NANAS"]

        tileset_img = pygame.image.load(join('graphics', 'tilesets', 'demo_tiles.png')).convert_alpha()
        self.cameo_surfaces = []

        for i in range(4):
            surf = pygame.Surface((128, 128), pygame.SRCALPHA)
            surf.blit(tileset_img, (0, 0), (i * 128, 768, 128, 128))
            self.cameo_surfaces.append(surf)

    def events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.game.change_state(StateID.MENU)

    def draw(self, screen):
        screen.fill(BLACK)

        title = self.font_title.render("SECRETS GALLERY", True, YELLOW)
        title_rect = title.get_frect(center=(WINDOW_WIDTH / 2, 80))
        screen.blit(title, title_rect)

        instruction = self.font_name.render("PRESS ESC TO RETURN", True, WHITE)
        inst_rect = instruction.get_frect(center=(WINDOW_WIDTH / 2, 128))
        screen.blit(instruction, inst_rect)

        start_x = WINDOW_WIDTH / 2 - 300
        spacing_x = 200

        for i in range(4):
            x = start_x + (i * spacing_x)
            y = WINDOW_HEIGHT / 2

            is_unlocked = self.game.save_manager.has_secret(i)

            if is_unlocked:
                img_rect = self.cameo_surfaces[i].get_frect(center=(x, y))
                screen.blit(self.cameo_surfaces[i], img_rect)

                name_text = self.font_name.render(self.cameo_names[i], True, WHITE)

            else:
                placeholder = pygame.Surface((128, 128))
                placeholder.fill((255, 0, 255))
                img_rect = placeholder.get_frect(center=(x, y))
                screen.blit(placeholder, img_rect)

                q_text = self.font_title.render("?", True, WHITE)
                q_rect = q_text.get_frect(center=(x, y))
                screen.blit(q_text, q_rect)

                name_text = self.font_name.render("???", True, WHITE)

            name_rect = name_text.get_frect(center=(x, y + 96))
            screen.blit(name_text, name_rect)
