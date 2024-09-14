import tkinter as tk
from tkinter import messagebox
import threading
import subprocess
import os
from modules.gui_components import GUIComponents
from modules.file_manager import FileManager

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather State Manager")
        self.root.minsize(550, 380)

        self.gui_components = GUIComponents(root, self)
        self.file_manager = FileManager(self)

        self.data = self.file_manager.data
        self.populate_right_listbox()
        self.populate_left_listbox(self.file_manager.get_folder_path_from_env_file())

        # Start the file watcher thread
        self.file_watcher_thread = threading.Thread(target=self.file_manager.watch_file)
        self.file_watcher_thread.start()

    def populate_right_listbox(self):
        self.gui_components.right_listbox.delete(0, tk.END)
        for state in self.data.get('Data', {}).get('RootChunk', {}).get('weatherStates', []):
            self.gui_components.right_listbox.insert(tk.END, state['Data']['name']['$value'])

    def populate_left_listbox(self, folder_path):
        self.gui_components.left_listbox.delete(0, tk.END)
        existing_names = {state['Data']['name']['$value'] for state in self.data.get('Data', {}).get('RootChunk', {}).get('weatherStates', [])}
        for file_name in os.listdir(folder_path):
            if file_name.endswith('.envparam'):
                name = file_name.replace('.envparam', '')
                if name not in existing_names:
                    self.gui_components.left_listbox.insert(tk.END, name)

    def move_entries(self):
        selected = self.gui_components.left_listbox.curselection()
        for index in selected:
            file_name = self.gui_components.left_listbox.get(index)
            if file_name not in self.gui_components.right_listbox.get(0, tk.END):
                self.gui_components.right_listbox.insert(tk.END, file_name)
                self.gui_components.left_listbox.delete(index)

    def remove_entries(self):
        selected = self.gui_components.right_listbox.curselection()
        for index in selected:
            file_name = self.gui_components.right_listbox.get(index)
            if file_name not in self.gui_components.left_listbox.get(0, tk.END):
                self.gui_components.left_listbox.insert(tk.END, file_name)
                self.gui_components.right_listbox.delete(index)
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
            for index in range(self.gui_components.right_listbox.size()):
                file_name = self.gui_components.right_listbox.get(index)
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
            self.file_manager.save_json(self.file_manager.env_file_path)

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

    def open_edit_targets(self):
        subprocess.Popen(['python', 'edit_targets.py'])

    def open_edit_properties(self):
        subprocess.Popen(['python', 'edit_properties.py'])

    def open_edit_debug(self):
        subprocess.Popen(['python', 'edit_debug.py'])

    def on_closing(self):
        self.file_manager.stop_watching = True
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
