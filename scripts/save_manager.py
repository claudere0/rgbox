import json
import os

class SaveManager:
    def __init__(self, filepath='data/save.json'):
        self.filepath = filepath
        self.data = self.get_default_data()
        self.load()

    def get_default_data(self):
        return {
            "unlocked_levels": ["tutorial_zero"],
            "best_times": {},
            "secrets_found": [],
            "settings": {
                "music_volume": 50.0,
                "sfx_volume": 50.0,
                "fullscreen": False,
                "minimalist": False
            }
        }

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    saved_data = json.load(f)
                    self.data.update(saved_data)
            except:
                print("Error reading save file. Default settings will be used.")
                self.save()
        else:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            self.save()

    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.data, f, indent=4)

    def unlock_level(self, level_name):
        if level_name not in self.data["unlocked_levels"]:
            self.data["unlocked_levels"].append(level_name)
            self.save()

    def is_level_unlocked(self, level_name):
        return level_name in self.data["unlocked_levels"]

    def save_best_time(self, level_name, time_ms):
        current_best = self.data["best_times"].get(level_name, float('inf'))
        if time_ms < current_best:
            self.data["best_times"][level_name] = time_ms
            self.save()
            return True
        return False

    def unlock_secret(self, secret_name):
        if secret_name not in self.data["secrets_found"]:
            self.data["secrets_found"].append(secret_name)
            self.save()

    def has_secret(self, secret_name):
        return secret_name in self.data["secrets_found"]
