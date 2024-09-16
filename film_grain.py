import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
import time

class FilmGrainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Edit Film Grain Properties")
        self.root.minsize(500, 300)

        self.env_file_path = self.get_env_file_path()
        self.data = self.load_json(self.env_file_path)

        # Create frames for the headers and listboxes
        left_frame = tk.Frame(root)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = tk.Frame(root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add headers
        self.left_header = tk.Label(left_frame, text="Select Resolution")
        self.left_header.pack(pady=(0, 5))

        self.right_header = tk.Label(right_frame, text="Edit Resolution Properties")
        self.right_header.pack(pady=(0, 5))

        self.left_listbox = tk.Listbox(left_frame, exportselection=False)
        self.left_listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        self.entries = {}
        self.create_entries(right_frame)

        self.confirm_button = tk.Button(right_frame, text="Save", command=self.save_changes)
        self.confirm_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.confirm_label = tk.Label(right_frame, text="", fg="green")
        self.confirm_label.pack(side=tk.LEFT, padx=10)

        resolutions = [900, 1080, 2160]
        for res in resolutions:
            self.left_listbox.insert(tk.END, res)

        self.left_listbox.bind('<<ListboxSelect>>', self.on_left_listbox_select)

        self.current_selection = None

        # Start the file watcher thread
        self.stop_watching = False
        self.file_watcher_thread = threading.Thread(target=self.watch_file)
        self.file_watcher_thread.start()

    def create_entries(self, parent):
        labels = ["Aberration Dispersal", "Film Grain Scale", "Film Grain Strength"]
        for label in labels:
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(frame, text=label).pack(side=tk.LEFT)
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

    def on_left_listbox_select(self, event):
        selected_index = self.left_listbox.curselection()
        if selected_index:
            self.current_selection = selected_index[0]
            selected_res = self.left_listbox.get(selected_index)
            res_data = self.get_res_data_by_point(selected_res)

            self.entries["Aberration Dispersal"].delete(0, tk.END)
            self.entries["Aberration Dispersal"].insert(0, self.get_value(res_data, 'resolutionAberrationDispersal'))

            self.entries["Film Grain Scale"].delete(0, tk.END)
            self.entries["Film Grain Scale"].insert(0, self.get_value(res_data, 'resolutionFilmGrainScale'))

            self.entries["Film Grain Strength"].delete(0, tk.END)
            self.entries["Film Grain Strength"].insert(0, self.get_value(res_data, 'resolutionFilmGrainStrength'))

    def save_changes(self):
        if self.current_selection is not None:
            selected_res = self.left_listbox.get(self.current_selection)
            res_data = self.get_res_data_by_point(selected_res)

            def update_field(field_name, entry_name):
                value = self.get_entry_value(self.entries[entry_name])
                if value is None:
                    res_data[field_name] = None
                else:
                    for element in res_data[field_name]['Elements']:
                        if element['Point'] == int(selected_res):
                            element['Value'] = value

            update_field('resolutionAberrationDispersal', 'Aberration Dispersal')
            update_field('resolutionFilmGrainScale', 'Film Grain Scale')
            update_field('resolutionFilmGrainStrength', 'Film Grain Strength')

            self.save_json(self.env_file_path)

            # Highlight the selected resolution
            self.left_listbox.selection_clear(0, tk.END)
            self.left_listbox.selection_set(self.current_selection)
            self.left_listbox.activate(self.current_selection)

            # Show confirmation message
            self.confirm_label.config(text="Changes saved successfully!")
            self.root.after(3000, self.clear_confirmation)

    def clear_confirmation(self):
        self.confirm_label.config(text="")

    def get_value(self, res_data, key):
        for element in res_data[key]['Elements']:
            if element['Point'] == int(self.left_listbox.get(self.current_selection)):
                return element['Value']
        return ""

    def get_entry_value(self, entry):
        value = entry.get()
        if value == "":
            return None
        return float(value)

    def get_res_data_by_point(self, point):
        return self.data['Data']['RootChunk']['renderSettingFactors']

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
        self.populate_listbox()

    def populate_listbox(self):
        self.left_listbox.delete(0, tk.END)
        resolutions = [980, 1080, 2160]
        for res in resolutions:
            self.left_listbox.insert(tk.END, res)

    def on_closing(self):
        self.stop_watching = True
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FilmGrainApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
