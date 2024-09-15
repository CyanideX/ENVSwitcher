import tkinter as tk
from tkinter import filedialog, messagebox
import json, os, subprocess, threading, time

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather State Manager")
        self.root.minsize(550, 380)

        # Create frames for the headers and listboxes
        left_frame = tk.Frame(root)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        right_frame = tk.Frame(root)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add headers
        self.left_header = tk.Label(left_frame, text="Inactive States")
        self.left_header.pack()

        self.right_header = tk.Label(right_frame, text="Active States")
        self.right_header.pack()

        self.left_listbox = tk.Listbox(left_frame)
        self.left_listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        self.right_listbox = tk.Listbox(right_frame)
        self.right_listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        button_width = 15
        button_width_arrows = 6

        # Create a frame to contain the buttons
        button_frame = tk.Frame(root)
        button_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(50, 25))

        self.targets_button = tk.Button(button_frame, text="Transitions", command=self.open_edit_targets, width=button_width)
        self.targets_button.pack(pady=5)

        self.properties_button = tk.Button(button_frame, text="Properties", command=self.open_edit_properties, width=button_width)
        self.properties_button.pack(pady=5)

        # Create a frame for the add and remove buttons
        move_button_frame = tk.Frame(button_frame)
        move_button_frame.pack(pady=5)

        self.remove_button = tk.Button(move_button_frame, text="<<<", command=self.remove_entries, width=button_width_arrows)
        self.remove_button.pack(side=tk.LEFT, padx=5)

        self.add_button = tk.Button(move_button_frame, text=">>>", command=self.move_entries, width=button_width_arrows)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(button_frame, text="Save", command=self.confirm_additions, width=button_width)
        self.save_button.pack(pady=5)

        self.reload_button = tk.Button(button_frame, text="Reload JSON", command=self.reload_json, width=button_width)
        self.reload_button.pack(side=tk.BOTTOM, pady=10)

        self.debug_button = tk.Button(button_frame, text="Debug", command=self.open_edit_debug, width=button_width)
        self.debug_button.pack(side=tk.BOTTOM, pady=5)

        self.env_file_path = self.get_env_file_path()
        self.data = self.load_json(self.env_file_path)
        self.populate_right_listbox()
        self.populate_left_listbox(self.get_folder_path_from_env_file())

        # Start the file watcher thread
        self.stop_watching = False
        self.file_watcher_thread = threading.Thread(target=self.watch_file)
        self.file_watcher_thread.start()

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

    def populate_right_listbox(self):
        self.right_listbox.delete(0, tk.END)
        for state in self.data.get('Data', {}).get('RootChunk', {}).get('weatherStates', []):
            self.right_listbox.insert(tk.END, state['Data']['name']['$value'])

    def populate_left_listbox(self, folder_path):
        self.left_listbox.delete(0, tk.END)
        existing_names = {state['Data']['name']['$value'] for state in self.data.get('Data', {}).get('RootChunk', {}).get('weatherStates', [])}
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.envparam'):
                name = file_name.replace('.envparam', '')
                if name not in existing_names:
                    self.left_listbox.insert(tk.END, name)

    def move_entries(self):
        selected = self.left_listbox.curselection()
        for index in selected:
            file_name = self.left_listbox.get(index)
            if file_name not in self.right_listbox.get(0, tk.END):
                self.right_listbox.insert(tk.END, file_name)
                self.left_listbox.delete(index)

    def remove_entries(self):
        selected = self.right_listbox.curselection()
        for index in selected:
            file_name = self.right_listbox.get(index)
            if file_name not in self.left_listbox.get(0, tk.END):
                self.left_listbox.insert(tk.END, file_name)
                self.right_listbox.delete(index)
                # Find and remove the corresponding weather state and transitions
                for state in self.data['Data']['RootChunk']['weatherStates']:
                    if state['Data']['name']['$value'] == file_name:
                        handle_id = state['HandleId']
                        self.data['Data']['RootChunk']['weatherStates'].remove(state)
                        self.remove_transitions(handle_id)
                        break
    
    def remove_transitions(self, handle_id):
        transitions = self.data['Data']['RootChunk']['weatherStateTransitions']
        self.data['Data']['RootChunk']['weatherStateTransitions'] = [
            transition for transition in transitions
            if transition['Data']['sourceWeatherState']['HandleRefId'] != handle_id and
            transition['Data']['targetWeatherState']['HandleRefId'] != handle_id
        ]

    def confirm_additions(self):
        if messagebox.askyesno("Confirm Save", "Are you sure you want to save the changes?"):
            existing_names = {state['Data']['name']['$value'] for state in self.data.get('Data', {}).get('RootChunk', {}).get('weatherStates', [])}
            for index in range(self.right_listbox.size()):
                file_name = self.right_listbox.get(index)
                name = file_name.replace('.envparam', '')
                if name not in existing_names:
                    self.data['Data']['RootChunk']['weatherStates'].append({
                        'HandleId': "0",
                        'Data': {
                            '$type': 'worldWeatherState',
                            'effect': {
                                'DepotPath': {
                                    '$type': 'ResourcePath',
                                    '$storage': 'uint64',
                                    '$value': "0"
                                },
                                'Flags': "Soft"
                            },
                            'environmentAreaParameters': {
                                'DepotPath': {
                                    '$type': 'ResourcePath',
                                    '$storage': 'string',
                                    '$value': f"base\\weather\\24h_basic\\{file_name}.envparam"
                                },
                                'Flags': "Default"
                            },
                            'maxDuration': {
                                'InterpolationType': "Linear",
                                'LinkType': "ESLT_Normal",
                                'Elements': [
                                    {
                                        'Point': 12,
                                        'Value': 1.5
                                    }
                                ]
                            },
                            'minDuration': None,
                            'name': {
                                '$type': 'CName',
                                '$storage': 'string',
                                '$value': name
                            },
                            'probability': {
                                'InterpolationType': "Linear",
                                'LinkType': "ESLT_Normal",
                                'Elements': [
                                    {
                                        'Point': 12,
                                        'Value': 0.0500000007
                                    }
                                ]
                            },
                            'transitionDuration': {
                                'InterpolationType': "Linear",
                                'LinkType': "ESLT_Normal",
                                'Elements': [
                                    {
                                        'Point': 12,
                                        'Value': 0.25
                                    }
                                ]
                            }
                        }
                    })

            self.ensure_unique_handle_ids()
            self.save_json(self.env_file_path)

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

    def reload_json(self):
        self.data = self.load_json(self.env_file_path)
        self.populate_right_listbox()
        self.populate_left_listbox(self.get_folder_path_from_env_file())

    def watch_file(self):
        last_modified_time = os.path.getmtime(self.env_file_path)
        while not self.stop_watching:
            time.sleep(1)
            current_modified_time = os.path.getmtime(self.env_file_path)
            if current_modified_time != last_modified_time:
                last_modified_time = current_modified_time
                self.reload_json()

    def open_edit_targets(self):
        subprocess.Popen(['python', 'edit_targets.py'])

    def open_edit_properties(self):
        subprocess.Popen(['python', 'edit_properties.py'])

    def open_edit_debug(self):
        subprocess.Popen(['python', 'edit_debug.py'])

    def on_closing(self):
        self.stop_watching = True
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()