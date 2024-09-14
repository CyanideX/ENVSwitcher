import tkinter as tk

class GUIComponents:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.create_frames()
        self.create_buttons()
        self.create_listboxes()

    def create_frames(self):
        self.left_frame = tk.Frame(self.root)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(50, 25))

        self.move_button_frame = tk.Frame(self.button_frame)
        self.move_button_frame.pack(pady=5)

    def create_buttons(self):
        button_width = 15
        button_width_arrows = 6

        self.targets_button = tk.Button(self.button_frame, text="Transitions", command=self.app.open_edit_targets, width=button_width)
        self.targets_button.pack(pady=5)

        self.properties_button = tk.Button(self.button_frame, text="Properties", command=self.app.open_edit_properties, width=button_width)
        self.properties_button.pack(pady=5)

        self.remove_button = tk.Button(self.move_button_frame, text="<<<", command=self.app.remove_entries, width=button_width_arrows)
        self.remove_button.pack(side=tk.LEFT, padx=5)

        self.add_button = tk.Button(self.move_button_frame, text=">>>", command=self.app.move_entries, width=button_width_arrows)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(self.button_frame, text="Save", command=self.app.confirm_additions, width=button_width)
        self.save_button.pack(pady=5)

        self.debug_button = tk.Button(self.button_frame, text="Debug", command=self.app.open_edit_debug, width=button_width)
        self.debug_button.pack(side=tk.BOTTOM, pady=5)

    def create_listboxes(self):
        self.left_header = tk.Label(self.left_frame, text="Inactive States")
        self.left_header.pack()

        self.right_header = tk.Label(self.right_frame, text="Active States")
        self.right_header.pack()

        self.left_listbox = tk.Listbox(self.left_frame)
        self.left_listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        self.right_listbox = tk.Listbox(self.right_frame)
        self.right_listbox.pack(fill=tk.BOTH, expand=True, pady=10)
