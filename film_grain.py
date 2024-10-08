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
        self.left_header = tk.Label(left_frame, text="Select Category")
        self.left_header.pack(pady=(0, 5))

        self.right_header = tk.Label(right_frame, text="Edit Category Properties")
        self.right_header.pack(pady=(0, 5))

        self.left_listbox = tk.Listbox(left_frame, exportselection=False)
        self.left_listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        self.entries = {}
        self.create_entries(right_frame)

        self.confirm_button = tk.Button(right_frame, text="Save", command=self.save_changes)
        self.confirm_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.confirm_label = tk.Label(right_frame, text="", fg="green")
        self.confirm_label.pack(side=tk.LEFT, padx=10)

        categories = ["resolutionAberrationDispersal", "resolutionFilmGrainScale", "resolutionFilmGrainStrength"]
        for category in categories:
            self.left_listbox.insert(tk.END, category)

        self.left_listbox.bind('<<ListboxSelect>>', self.on_left_listbox_select)

        self.current_selection = None

        # Start the file watcher thread
        self.stop_watching = False
        self.file_watcher_thread = threading.Thread(target=self.watch_file)
        self.file_watcher_thread.start()

    def create_entries(self, parent):
        self.entries_frame = tk.Frame(parent)
        self.entries_frame.pack(fill=tk.BOTH, expand=True)

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
            selected_category = self.left_listbox.get(selected_index)
            elements = self.data['Data']['RootChunk']['renderSettingFactors'][selected_category]['Elements']

            for widget in self.entries_frame.winfo_children():
                widget.destroy()

            self.entries[selected_category] = []
            for element in elements:
                point_label = tk.Label(self.entries_frame, text=f"Point: {element['Point']}")
                point_label.pack(pady=(10, 0))
                value_entry = tk.Entry(self.entries_frame)
                value_entry.insert(0, element['Value'])
                value_entry.pack(fill=tk.X, padx=10, pady=5)
                self.entries[selected_category].append((element['Point'], value_entry))

    def save_changes(self):
        if self.current_selection is not None:
            selected_category = self.left_listbox.get(self.current_selection)
            elements = self.data['Data']['RootChunk']['renderSettingFactors'][selected_category]['Elements']

            for i, (point, value_entry) in enumerate(self.entries[selected_category]):
                elements[i]['Value'] = float(value_entry.get())

            self.save_json(self.env_file_path)

            # Highlight the selected category
            self.left_listbox.selection_clear(0, tk.END)
            self.left_listbox.selection_set(self.current_selection)
            self.left_listbox.activate(self.current_selection)

            # Show confirmation message
            self.confirm_label.config(text="Changes saved successfully!")
            self.root.after(3000, self.clear_confirmation)

    def clear_confirmation(self):
        self.confirm_label.config(text="")

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
    app = FilmGrainApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
