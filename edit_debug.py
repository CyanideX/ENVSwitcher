import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class EditDebugApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Debug - Global Editor")
        self.root.minsize(200, 150)  # Set minimum width to 400

        self.entries = {
            "Min Duration": tk.StringVar(),
            "Max Duration": tk.StringVar(),
            "Probability": tk.StringVar(),
            "Transition Duration": tk.StringVar()
        }

        self.env_file_path = self.get_env_file_path()
        self.data = self.load_json(self.env_file_path)  # Initialize the data attribute

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Add header
        header = ttk.Label(frame, text="Global overrides")
        header.grid(row=0, column=0, columnspan=2, pady=(0, 0))

        ttk.Label(frame, text="Min Duration:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.entries["Min Duration"]).grid(row=1, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Max Duration:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.entries["Max Duration"]).grid(row=2, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Probability:").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.entries["Probability"]).grid(row=3, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Transition Duration:").grid(row=4, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.entries["Transition Duration"]).grid(row=4, column=1, sticky=(tk.W, tk.E))

        ttk.Button(frame, text="Save Changes", command=self.save_changes).grid(row=5, column=0, columnspan=2, pady=10)

    def save_changes(self):
        for state in self.data['Data']['RootChunk']['weatherStates']:
            state_data = state['Data']

            self.update_field(state_data, 'minDuration', self.entries["Min Duration"])
            self.update_field(state_data, 'maxDuration', self.entries["Max Duration"])
            self.update_field(state_data, 'probability', self.entries["Probability"])
            self.update_field(state_data, 'transitionDuration', self.entries["Transition Duration"])

        self.save_json(self.env_file_path)

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

    def get_entry_value(self, entry):
        value = entry.get()
        if value == "":
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def get_env_file_path(self):
        if os.path.exists('env_file_path.txt'):
            with open('env_file_path.txt', 'r') as file:
                return file.read().strip()
        else:
            messagebox.showerror("Error", "env_file_path.txt not found.")
            self.root.quit()

    def load_json(self, filename):
        with open(filename, 'r') as file:
            return json.load(file)

    def save_json(self, filename):
        with open(filename, 'w') as file:
            json.dump(self.data, file, indent=4)

if __name__ == "__main__":
    root = tk.Tk()
    app = EditDebugApp(root)
    root.mainloop()
