import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json, os, threading, time

class EditPropertiesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Edit Weather Properties")
        self.root.minsize(500, 300)

        self.env_file_path = self.get_env_file_path()
        self.data = self.load_json(self.env_file_path)

        # Create frames for the headers and listboxes
        left_frame = tk.Frame(root)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = tk.Frame(root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add headers
        self.left_header = tk.Label(left_frame, text="Select Weather State")
        self.left_header.pack(pady=(0, 5))

        self.right_header = tk.Label(right_frame, text="Edit State Properties")
        self.right_header.pack(pady=(0, 5))

        self.left_listbox = tk.Listbox(left_frame, exportselection=False)
        self.left_listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        self.entries = {}
        self.create_entries(right_frame)

        self.confirm_button = tk.Button(right_frame, text="Save", command=self.save_changes)
        self.confirm_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.confirm_label = tk.Label(right_frame, text="", fg="green")
        self.confirm_label.pack(side=tk.LEFT, padx=10)

        for state in self.data['Data']['RootChunk']['weatherStates']:
            self.left_listbox.insert(tk.END, state['Data']['name']['$value'])

        self.left_listbox.bind('<<ListboxSelect>>', self.on_left_listbox_select)

        self.current_selection = None

        # Start the file watcher thread
        self.stop_watching = False
        self.file_watcher_thread = threading.Thread(target=self.watch_file)
        self.file_watcher_thread.start()

    def create_entries(self, parent):
        labels = ["Min Duration", "Max Duration", "Probability", "Transition Duration", "Effect DepotPath"]
        for label in labels:
            frame = tk.Frame(parent)
            frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(frame, text=label).pack(side=tk.LEFT)
            entry = tk.Entry(frame, justify='right' if label == "Effect DepotPath" else 'left')
            entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            if label == "Effect DepotPath":
                entry.bind("<KeyRelease>", self.scroll_to_end)
            self.entries[label] = entry

    def scroll_to_end(self, event):
        event.widget.xview_moveto(1)

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
            selected_state = self.left_listbox.get(selected_index)
            state_data = self.get_state_data_by_name(selected_state)

            self.entries["Min Duration"].delete(0, tk.END)
            self.entries["Min Duration"].insert(0, self.get_value(state_data, 'minDuration'))

            self.entries["Max Duration"].delete(0, tk.END)
            self.entries["Max Duration"].insert(0, self.get_value(state_data, 'maxDuration'))

            self.entries["Probability"].delete(0, tk.END)
            self.entries["Probability"].insert(0, self.get_value(state_data, 'probability'))

            self.entries["Transition Duration"].delete(0, tk.END)
            self.entries["Transition Duration"].insert(0, self.get_value(state_data, 'transitionDuration'))

            self.entries["Effect DepotPath"].delete(0, tk.END)
            self.entries["Effect DepotPath"].insert(0, self.get_value(state_data, 'effect', 'DepotPath'))
            self.entries["Effect DepotPath"].xview_moveto(1)

    def save_changes(self):
        if self.current_selection is not None:
            selected_state = self.left_listbox.get(self.current_selection)
            state_data = self.get_state_data_by_name(selected_state)

            def update_field(field_name, entry_name):
                value = self.get_entry_value(self.entries[entry_name])
                if value is None:
                    state_data[field_name] = None
                else:
                    state_data[field_name] = {
                        "InterpolationType": "Linear",
                        "LinkType": "ESLT_Normal",
                        "Elements": [{"Point": 12, "Value": value}]
                    }

            update_field('minDuration', 'Min Duration')
            update_field('maxDuration', 'Max Duration')
            update_field('probability', 'Probability')
            update_field('transitionDuration', 'Transition Duration')

            depot_path = self.entries["Effect DepotPath"].get()
            state_data['effect']['DepotPath']['$value'] = depot_path

            if depot_path == "" or depot_path == "0":
                state_data['effect']['DepotPath']['$storage'] = "uint64"
            else:
                state_data['effect']['DepotPath']['$storage'] = "string"

            self.save_json(self.env_file_path)

            # Highlight the selected state
            self.left_listbox.selection_clear(0, tk.END)
            self.left_listbox.selection_set(self.current_selection)
            self.left_listbox.activate(self.current_selection)

            # Show confirmation message
            self.confirm_label.config(text="Changes saved successfully!")
            self.root.after(3000, self.clear_confirmation)

    def clear_confirmation(self):
        self.confirm_label.config(text="")

    def get_value(self, state_data, key, subkey=None):
        if subkey:
            value = state_data.get(key, {}).get(subkey, None)
        else:
            value = state_data.get(key, None)
        if value is None:
            return ""
        if isinstance(value, dict) and 'Elements' in value:
            return value['Elements'][0]['Value']
        if isinstance(value, dict) and '$value' in value:
            return value['$value']
        return value

    def get_entry_value(self, entry):
        value = entry.get()
        if value == "":
            return None
        return float(value)

    def get_state_data_by_name(self, name):
        for state in self.data['Data']['RootChunk']['weatherStates']:
            if state['Data']['name']['$value'] == name:
                return state['Data']
        return None

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
        for state in self.data['Data']['RootChunk']['weatherStates']:
            self.left_listbox.insert(tk.END, state['Data']['name']['$value'])

    def on_closing(self):
        self.stop_watching = True
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EditPropertiesApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
