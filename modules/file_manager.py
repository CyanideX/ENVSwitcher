import json
import os
import time
from tkinter import filedialog, messagebox

class FileManager:
    def __init__(self, app):
        self.app = app
        self.env_file_path = self.get_env_file_path()
        self.data = self.load_json(self.env_file_path)
        self.stop_watching = False

    def get_env_file_path(self):
        if os.path.exists('env_file_path.txt'):
            with open('env_file_path.txt', 'r') as file:
                return file.read().strip()
        else:
            file_path = filedialog.askopenfilename(title="Select main env.json file", filetypes=(("JSON files", "*.json"), ("all files", "*.*")))
            with open('env_file_path.txt', 'w') as file:
                file.write(file_path)
            return file_path

    def get_folder_path_from_env_file(self):
        env_file_path = self.env_file_path.replace('/', '\\')
        folder_path = os.path.dirname(env_file_path).replace('raw', 'archive')
        return folder_path

    def load_json(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON file: {e}")
            return {}

    def save_json(self, file_path):
        try:
            with open(file_path, 'w') as file:
                json.dump(self.data, file, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save JSON file: {e}")

    def watch_file(self):
        last_modified_time = os.path.getmtime(self.env_file_path)
        while not self.stop_watching:
            time.sleep(1)
            current_modified_time = os.path.getmtime(self.env_file_path)
            if current_modified_time != last_modified_time:
                last_modified_time = current_modified_time
                self.app.reload_json()
