import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json
import os
import threading
import time

class EditDebugApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Debug")
        self.root.minsize(300, 150)

        self.env_file_path = self.get_env_file_path()
        self.data = self.load_json(self.env_file_path)

        right_frame = tk.Frame(root)
        right_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.right_header = tk.Label(right_frame, text="Edit Global Properties")
        self.right_header.pack(pady=(0, 25))

        self.entries = {}
        self.create_entries(right_frame)

        self.confirm_button = tk.Button(right_frame, text="Save", command=self.save_changes)
        self.confirm_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.confirm_label = tk.Label(right_frame, text="", fg="green")
        self.confirm_label.pack(side=tk.LEFT, padx=10)

        # Start the file watcher thread
        self.stop_watching = False
        self.file_watcher_thread = threading.Thread(target=self.watch_file)
        self.file_watcher_thread.start()

    def create_entries(self, parent):
        labels = ["Min Duration", "Max Duration", "Probability", "Transition Duration"]
        for label in labels:
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(frame, text=label, anchor='w', padx=10).pack(side=tk.LEFT)
            entry = tk.Entry(frame)
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            self.entries[label] = entry

    def get_env_file_path(self):
        if os.path.exists('env_file_path.txt'):
            with open('env_file_path.txt', 'r') as file:
                return file.read().strip()
        else:
            messagebox.showerror("Error", "env_file_path.txt not found.")
            self.root.quit()

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

    def save_changes(self):
        for state in self.data['Data']['RootChunk']['weatherStates']:
            state_data = state['Data']

            self.update_field(state_data, 'minDuration', self.entries["Min Duration"])
            self.update_field(state_data, 'maxDuration', self.entries["Max Duration"])
            self.update_field(state_data, 'probability', self.entries["Probability"])
            self.update_field(state_data, 'transitionDuration', self.entries["Transition Duration"])

        self.save_json(self.env_file_path)

        # Show confirmation message
        self.confirm_label.config(text="Changes saved successfully!")
        self.root.after(3000, self.clear_confirmation)

    def update_field(self, state_data, field_name, entry):
        value = self.get_entry_value(entry)
        if value is None:
            state_data[field_name] = None
        else:
            state_data[field_name] = {
                "InterpolationType": "Linear",
                "LinkType": "ESLT_Normal",
                "Elements": [{"Point": 12, "Value": value}]
            }

    def clear_confirmation(self):
        self.confirm_label.config(text="")

    def get_entry_value(self, entry):
        value = entry.get()
        if value == "":
            return None
        return float(value)

    def watch_file(self):
        last_modified_time = os.path.getmtime(self.env_file_path)
        while not self.stop_watching:
            time.sleep(1)
            current_modified_time = os.path.getmtime(self.env_file_path)
            if current_modified_time != last_modified_time:
                last_modified_time = current_modified_time
                self.reload_json()

    def reload_json(self):
        self.data = self.load_json(self.env_file_path)

    def on_closing(self):
        self.stop_watching = True
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EditDebugApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
