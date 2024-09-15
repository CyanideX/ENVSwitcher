import tkinter as tk
from tkinter import messagebox, Toplevel, Label
from tkinter import ttk
import json
import os
import threading
import time

class EditTransitionsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Edit Weather Transitions")

        # Set the initial size of the window
        self.root.geometry("700x400")
        self.root.minsize(700, 300)
        self.root.maxsize(1920, 2160)

        self.env_file_path = self.get_env_file_path()
        self.data = self.load_json(self.env_file_path)

        # Create frames for the headers and listboxes
        left_frame = tk.Frame(root)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        middle_frame = tk.Frame(root)
        middle_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        right_frame = tk.Frame(root)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        # Create a frame for the Save button and center it
        button_frame = tk.Frame(root)
        button_frame.grid(row=1, column=0, columnspan=3, pady=10)

        button_width = 25

        self.confirm_button = tk.Button(button_frame, text="Save", command=self.save_changes, width=button_width)
        self.confirm_button.pack(pady=10)
        
        self.confirm_label = tk.Label(button_frame, text="", fg="green")
        self.confirm_label.pack()

        # Add headers
        self.left_header = tk.Label(left_frame, text="Select Source States")
        self.left_header.pack(pady=(0, 5))

        self.middle_header = tk.Label(middle_frame, text="Select Weather State")
        self.middle_header.pack(pady=(0, 5))

        self.right_header = tk.Label(right_frame, text="Select Target States")
        self.right_header.pack(pady=(0, 5))

        # Add scrollbars to the left and right frames
        left_scrollbar = tk.Scrollbar(left_frame, orient=tk.VERTICAL, width=20)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        right_scrollbar = tk.Scrollbar(right_frame, orient=tk.VERTICAL, width=20)
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.left_listbox = tk.Listbox(middle_frame)
        self.left_listbox.pack(fill=tk.BOTH, expand=True, pady=0)
        self.left_listbox.bind("<Motion>", self.show_tooltip)

        self.preceding_vars = {}
        self.target_vars = {}
        self.current_transitions = self.load_current_transitions()

        left_canvas = tk.Canvas(left_frame, yscrollcommand=left_scrollbar.set)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scrollbar.config(command=left_canvas.yview)

        left_inner_frame = tk.Frame(left_canvas)
        left_canvas.create_window((0, 0), window=left_inner_frame, anchor='nw')

        right_canvas = tk.Canvas(right_frame, yscrollcommand=right_scrollbar.set)
        right_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_scrollbar.config(command=right_canvas.yview)

        right_inner_frame = tk.Frame(right_canvas)
        right_canvas.create_window((0, 0), window=right_inner_frame, anchor='nw')

        # Bind mouse wheel events to the canvases for scrolling
        left_canvas.bind("<Enter>", lambda event: self._bind_mousewheel(event, left_canvas))
        left_canvas.bind("<Leave>", lambda event: self._unbind_mousewheel(event))

        right_canvas.bind("<Enter>", lambda event: self._bind_mousewheel(event, right_canvas))
        right_canvas.bind("<Leave>", lambda event: self._unbind_mousewheel(event))

        for state in self.data['Data']['RootChunk']['weatherStates']:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(left_inner_frame, text=state['Data']['name']['$value'], variable=var, command=self.on_checkbox_select)
            chk.pack(anchor='w', padx=10, pady=0)
            chk.bind("<Motion>", self.show_tooltip)
            self.preceding_vars[state['Data']['name']['$value']] = var

        for state in self.data['Data']['RootChunk']['weatherStates']:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(right_inner_frame, text=state['Data']['name']['$value'], variable=var, command=self.on_checkbox_select)
            chk.pack(anchor='w', padx=10, pady=0)
            chk.bind("<Motion>", self.show_tooltip)
            self.target_vars[state['Data']['name']['$value']] = var

        for state in self.data['Data']['RootChunk']['weatherStates']:
            self.left_listbox.insert(tk.END, state['Data']['name']['$value'])

        self.left_listbox.bind('<<ListboxSelect>>', self.on_left_listbox_select)

        # Configure grid weights and minimum column widths to ensure proper resizing
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1, minsize=200)
        root.grid_columnconfigure(1, weight=1, minsize=200)
        root.grid_columnconfigure(2, weight=1, minsize=200)

        # Update scrollregion when the inner frames change size
        left_inner_frame.bind("<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
        right_inner_frame.bind("<Configure>", lambda e: right_canvas.configure(scrollregion=right_canvas.bbox("all")))

        self.watch_thread = threading.Thread(target=self.watch_file)
        self.watch_thread.daemon = True
        self.watch_thread.start()

        self.tooltip = None

    def show_tooltip(self, event):
        widget = event.widget
        if isinstance(widget, tk.Listbox):
            index = widget.nearest(event.y)
            if index != -1:
                state_name = widget.get(index)
                handle_id = self.get_handle_id_by_name(state_name)
                if handle_id:
                    self.create_tooltip(event, handle_id)
        elif isinstance(widget, ttk.Checkbutton):
            state_name = widget.cget("text")
            handle_id = self.get_handle_id_by_name(state_name)
            if handle_id:
                self.create_tooltip(event, handle_id)

    def create_tooltip(self, event, handle_id):
        if self.tooltip:
            self.tooltip.destroy()
        self.tooltip = Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.geometry(f"+{event.x_root + 20}+{event.y_root + 10}")
        label = Label(self.tooltip, text=f"Handle ID: {handle_id}", background="white", relief="solid", borderwidth=1)
        label.pack()

    def get_handle_id_by_name(self, name):
        for state in self.data.get('Data', {}).get('RootChunk', {}).get('weatherStates', []):
            if state['Data']['name']['$value'] == name:
                return state['HandleId']
        return None

    def _bind_mousewheel(self, event, canvas):
        canvas.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, canvas))

    def _unbind_mousewheel(self, event):
        event.widget.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event, canvas):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

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

    def watch_file(self):
        last_modified_time = os.path.getmtime(self.env_file_path)
        self.stop_watching = False
        while not self.stop_watching:
            time.sleep(1)
            current_modified_time = os.path.getmtime(self.env_file_path)
            if current_modified_time != last_modified_time:
                last_modified_time = current_modified_time
                self.reload_json()

    def reload_json(self):
        self.data = self.load_json(self.env_file_path)
        self.update_ui()

    def update_ui(self):
        self.left_listbox.delete(0, tk.END)
        for state in self.data['Data']['RootChunk']['weatherStates']:
            self.left_listbox.insert(tk.END, state['Data']['name']['$value'])
        self.current_transitions = self.load_current_transitions()

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

    def on_closing(self):
        self.stop_watching = True
        self.watch_thread.join()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EditTransitionsApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
