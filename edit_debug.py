import tkinter as tk
from tkinter import ttk
import json
import os

class EditDebugApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Debug - Global Editor")

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

        ttk.Label(frame, text="Min Duration:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.entries["Min Duration"]).grid(row=0, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Max Duration:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.entries["Max Duration"]).grid(row=1, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Probability:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.entries["Probability"]).grid(row=2, column=1, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Transition Duration:").grid(row=3, column=0, sticky=tk.W)
        ttk.Entry(frame, textvariable=self.entries["Transition Duration"]).grid(row=3, column=1, sticky=(tk.W, tk.E))

        ttk.Button(frame, text="Save Changes", command=self.save_changes).grid(row=4, column=0, columnspan=2, pady=10)

    def save_changes(self):
        for state in self.data['Data']['RootChunk']['weatherStates']:
            state_data = state['Data']

            if 'minDuration' in state_data and state_data['minDuration'] is not None:
                min_duration = self.get_entry_value(self.entries["Min Duration"])
                if min_duration is not None:
                    state_data['minDuration']['Elements'][0]['Value'] = min_duration

            if 'maxDuration' in state_data and state_data['maxDuration'] is not None:
                max_duration = self.get_entry_value(self.entries["Max Duration"])
                if max_duration is not None:
                    state_data['maxDuration']['Elements'][0]['Value'] = max_duration

            if 'probability' in state_data and state_data['probability'] is not None:
                probability = self.get_entry_value(self.entries["Probability"])
                if probability is not None:
                    state_data['probability']['Elements'][0]['Value'] = probability

            if 'transitionDuration' in state_data and state_data['transitionDuration'] is not None:
                transition_duration = self.get_entry_value(self.entries["Transition Duration"])
                if transition_duration is not None:
                    state_data['transitionDuration']['Elements'][0]['Value'] = transition_duration

        self.save_json(self.env_file_path)

    def get_entry_value(self, entry):
        try:
            return float(entry.get())
        except ValueError:
            return None

    def get_env_file_path(self):
        if os.path.exists('env_file_path.txt'):
            with open('env_file_path.txt', 'r') as file:
                return file.read().strip()
        else:
            tk.messagebox.showerror("Error", "env_file_path.txt not found.")
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
