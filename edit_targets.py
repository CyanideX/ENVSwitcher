import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json
import os

class EditWeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Edit Weather States")
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

        self.right_header = tk.Label(right_frame, text="Select Target States")
        self.right_header.pack(pady=(0, 5))

        self.left_listbox = tk.Listbox(left_frame)
        self.left_listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        self.target_vars = {}
        self.current_transitions = self.load_current_transitions()

        for state in self.data['Data']['RootChunk']['weatherStates']:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(right_frame, text=state['Data']['name']['$value'], variable=var, command=self.on_checkbox_select)
            chk.pack(anchor='w', padx=10, pady=0)
            self.target_vars[state['Data']['name']['$value']] = var

        button_frame = tk.Frame(right_frame)
        button_frame.pack(anchor='w', pady=10)

        self.confirm_button = tk.Button(button_frame, text="Save", command=self.save_changes)
        self.confirm_button.pack(side=tk.LEFT, padx=10)

        self.confirm_label = tk.Label(button_frame, text="", fg="green")
        self.confirm_label.pack(side=tk.LEFT, padx=0)

        for state in self.data['Data']['RootChunk']['weatherStates']:
            self.left_listbox.insert(tk.END, state['Data']['name']['$value'])

        self.left_listbox.bind('<<ListboxSelect>>', self.on_left_listbox_select)

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

    def load_current_transitions(self):
        transitions = {}
        for transition in self.data['Data']['RootChunk']['weatherStateTransitions']:
            source_id = transition['Data']['sourceWeatherState']['HandleRefId']
            target_id = transition['Data']['targetWeatherState']['HandleRefId']
            if source_id not in transitions:
                transitions[source_id] = []
            transitions[source_id].append(target_id)
        return transitions

    def on_left_listbox_select(self, event):
        selected_index = self.left_listbox.curselection()
        if selected_index:
            selected_state = self.left_listbox.get(selected_index)
            source_state_id = self.get_state_id_by_name(selected_state)

            for state_name, var in self.target_vars.items():
                var.set(False)

            if source_state_id in self.current_transitions:
                for target_state_id in self.current_transitions[source_state_id]:
                    target_state_name = self.get_state_name_by_id(target_state_id)
                    self.target_vars[target_state_name].set(True)

    def on_checkbox_select(self):
        selected_index = self.left_listbox.curselection()
        if selected_index:
            source_state_name = self.left_listbox.get(selected_index)
            source_state_id = self.get_state_id_by_name(source_state_name)

            selected_targets = [name for name, var in self.target_vars.items() if var.get()]
            self.current_transitions[source_state_id] = [self.get_state_id_by_name(name) for name in selected_targets]

    def save_changes(self):
        new_transitions = []
        for source_id, target_ids in self.current_transitions.items():
            for target_id in target_ids:
                transition = {
                    "HandleId": "0",
                    "Data": {
                        "$type": "worldWeatherStateTransition",
                        "probability": None,
                        "sourceWeatherState": {
                            "HandleRefId": source_id
                        },
                        "targetWeatherState": {
                            "HandleRefId": target_id
                        },
                        "transitionDuration": None
                    }
                }
                new_transitions.append(transition)

        self.data['Data']['RootChunk']['weatherStateTransitions'] = self.remove_duplicates(new_transitions)
        self.ensure_unique_handle_ids()
        self.save_json(self.env_file_path)

        self.confirm_label.config(text="Changes saved successfully!")
        self.root.after(3000, self.clear_confirmation)

    def clear_confirmation(self):
        self.confirm_label.config(text="")

    def get_state_id_by_name(self, name):
        for state in self.data['Data']['RootChunk']['weatherStates']:
            if state['Data']['name']['$value'] == name:
                return state['HandleId']
        return None

    def get_state_name_by_id(self, id):
        for state in self.data['Data']['RootChunk']['weatherStates']:
            if state['HandleId'] == id:
                return state['Data']['name']['$value']
        return None

    def remove_duplicates(self, transitions):
        unique_transitions = []
        seen = set()
        for transition in transitions:
            source_id = transition['Data']['sourceWeatherState']['HandleRefId']
            target_id = transition['Data']['targetWeatherState']['HandleRefId']
            if (source_id, target_id) not in seen:
                seen.add((source_id, target_id))
                unique_transitions.append(transition)
        return unique_transitions

    def ensure_unique_handle_ids(self):
        handle_id = 0
        for state in self.data['Data']['RootChunk']['weatherStates']:
            state['HandleId'] = str(handle_id)
            handle_id += 1

        for transition in self.data['Data']['RootChunk']['weatherStateTransitions']:
            transition['HandleId'] = str(handle_id)
            handle_id += 1

if __name__ == "__main__":
    root = tk.Tk()
    app = EditWeatherApp(root)
    root.mainloop()
