import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import json
import os

class EditWeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Edit Weather States")
        self.root.minsize(700, 300)

        self.env_file_path = self.get_env_file_path()
        self.data = self.load_json(self.env_file_path)

        # Create frames for the headers and listboxes
        left_frame = tk.Frame(root)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        middle_frame = tk.Frame(root)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = tk.Frame(root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add headers
        self.left_header = tk.Label(left_frame, text="Preceding States")
        self.left_header.pack(pady=(0, 5))

        self.middle_header = tk.Label(middle_frame, text="Select Weather State")
        self.middle_header.pack(pady=(0, 5))

        self.right_header = tk.Label(right_frame, text="Select Target States")
        self.right_header.pack(pady=(0, 5))

        self.left_listbox = tk.Listbox(middle_frame)
        self.left_listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        self.preceding_vars = {}
        self.target_vars = {}
        self.current_transitions = self.load_current_transitions()

        for state in self.data['Data']['RootChunk']['weatherStates']:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(left_frame, text=state['Data']['name']['$value'], variable=var, command=self.on_checkbox_select)
            chk.pack(anchor='w', padx=10, pady=0)
            self.preceding_vars[state['Data']['name']['$value']] = var

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

            for state_name, var in self.preceding_vars.items():
                var.set(False)

            for state_name, var in self.target_vars.items():
                var.set(False)

            for transition in self.data['Data']['RootChunk']['weatherStateTransitions']:
                if transition['Data']['targetWeatherState']['HandleRefId'] == source_state_id:
                    preceding_state_name = self.get_state_name_by_id(transition['Data']['sourceWeatherState']['HandleRefId'])
                    self.preceding_vars[preceding_state_name].set(True)

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

            selected_preceding = [name for name, var in self.preceding_vars.items() if var.get()]
            for name in selected_preceding:
                preceding_state_id = self.get_state_id_by_name(name)
                if preceding_state_id not in self.current_transitions:
                    self.current_transitions[preceding_state_id] = []
                if source_state_id not in self.current_transitions[preceding_state_id]:
                    self.current_transitions[preceding_state_id].append(source_state_id)

    def save_changes(self):
        new_transitions = []
        selected_index = self.left_listbox.curselection()
        if selected_index:
            selected_state_name = self.left_listbox.get(selected_index)
            selected_state_id = self.get_state_id_by_name(selected_state_name)

            for state_name, var in self.preceding_vars.items():
                if var.get():
                    source_state_id = self.get_state_id_by_name(state_name)
                    transition = {
                        "HandleId": "0",
                        "Data": {
                            "$type": "worldWeatherStateTransition",
                            "probability": None,
                            "sourceWeatherState": {
                                "HandleRefId": source_state_id
                            },
                            "targetWeatherState": {
                                "HandleRefId": selected_state_id
                            },
                            "transitionDuration": None
                        }
                    }
                    new_transitions.append(transition)

            for state_name, var in self.target_vars.items():
                if var.get():
                    target_state_id = self.get_state_id_by_name(state_name)
                    transition = {
                        "HandleId": "0",
                        "Data": {
                            "$type": "worldWeatherStateTransition",
                            "probability": None,
                            "sourceWeatherState": {
                                "HandleRefId": selected_state_id
                            },
                            "targetWeatherState": {
                                "HandleRefId": target_state_id
                            },
                            "transitionDuration": None
                        }
                    }
                    new_transitions.append(transition)

            # Remove transitions related to the selected state that are not in the new transitions
            self.data['Data']['RootChunk']['weatherStateTransitions'] = [
                t for t in self.data['Data']['RootChunk']['weatherStateTransitions']
                if not (t['Data']['sourceWeatherState']['HandleRefId'] == selected_state_id or
                        t['Data']['targetWeatherState']['HandleRefId'] == selected_state_id)
            ]

            self.data['Data']['RootChunk']['weatherStateTransitions'].extend(new_transitions)

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
        handle_id_map = {}

        # Assign unique HandleIds to weatherStates
        for state in self.data['Data']['RootChunk']['weatherStates']:
            state['HandleId'] = str(handle_id)
            handle_id_map[state['HandleId']] = handle_id
            handle_id += 1

        # Assign unique HandleIds to weatherStateTransitions
        for transition in self.data['Data']['RootChunk']['weatherStateTransitions']:
            transition['HandleId'] = str(handle_id)
            handle_id_map[transition['HandleId']] = handle_id
            handle_id += 1

        # Assign unique HandleIds to other elements
        for key, value in self.data['Data']['RootChunk'].items():
            if key not in ['weatherStates', 'weatherStateTransitions']:
                if isinstance(value, list):
                    for item in value:
                        if 'HandleId' in item:
                            item['HandleId'] = str(handle_id)
                            handle_id_map[item['HandleId']] = handle_id
                            handle_id += 1

        # Update HandleRefIds to match new HandleIds
        def update_handle_ref_ids(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == 'HandleRefId' and value in handle_id_map:
                        data[key] = str(handle_id_map[value])
                    else:
                        update_handle_ref_ids(value)
            elif isinstance(data, list):
                for item in data:
                    update_handle_ref_ids(item)

        update_handle_ref_ids(self.data['Data']['RootChunk'])

        # Update HandleRefIds in weatherStateTransitions
        for transition in self.data['Data']['RootChunk']['weatherStateTransitions']:
            source_id = transition['Data']['sourceWeatherState']['HandleRefId']
            target_id = transition['Data']['targetWeatherState']['HandleRefId']
            if source_id in handle_id_map:
                transition['Data']['sourceWeatherState']['HandleRefId'] = str(handle_id_map[source_id])
            if target_id in handle_id_map:
                transition['Data']['targetWeatherState']['HandleRefId'] = str(handle_id_map[target_id])

        # Ensure HandleIds for worldRenderSettings are updated
        for area in self.data['Data']['RootChunk']['worldRenderSettings']['areaParameters']:
            area['HandleId'] = str(handle_id)
            handle_id_map[area['HandleId']] = handle_id
            handle_id += 1

            # Update HandleIds for hdrMode and mode
            if 'hdrMode' in area['Data']:
                area['Data']['hdrMode']['HandleId'] = str(handle_id)
                handle_id_map[area['Data']['hdrMode']['HandleId']] = handle_id
                handle_id += 1

            if 'mode' in area['Data']:
                area['Data']['mode']['HandleId'] = str(handle_id)
                handle_id_map[area['Data']['mode']['HandleId']] = handle_id
                handle_id += 1

if __name__ == "__main__":
    root = tk.Tk()
    app = EditWeatherApp(root)
    root.mainloop()
