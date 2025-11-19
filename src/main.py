import os
import tkinter as tk
from tkinter import ttk, filedialog, PhotoImage
from datetime import datetime
from panda3d.core import (AntialiasAttrib, Loader, TextNode, Mat4,
                          Filename, Texture, loadPrcFile, ClockObject,
                          ColorBlendAttrib, loadPrcFileData)
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.task import Task
from direct.interval.IntervalGlobal import Func
import globals

# --- Load Config and Resources ---
loadPrcFile(globals.CONFIG_DIR)

resources = globals.RESOURCES_DIR
if not os.path.exists(resources):
    os.makedirs(resources)
    print("Please input Corporate Clash extracted phase files!")


class ControlPanel(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.master = master
        self.app = app
        self.pack(fill="both", expand=True)
        self.toggles_frame = None

        # State Variables for Checkbuttons
        self.is_shadow_var = tk.BooleanVar(value=self.app.is_shadow)
        self.is_blend_var = tk.BooleanVar(value=self.app.is_blend)
        self.is_body_var = tk.BooleanVar(value=False)
        self.is_autoplay_var = tk.BooleanVar(value=self.app.is_autoplay)
        self.is_background_black_var = tk.BooleanVar(value=self.app.bool)
        self.is_flattened_var = tk.BooleanVar(value=False)
        self.is_costume_var = tk.BooleanVar(value=False)
        self.loop_body_var = tk.BooleanVar(value=True)
        self.loop_head_var = tk.BooleanVar(value=True)
        self.selected_cog_var = tk.StringVar(value=self.app.current_cog)
        self.TIE_OPTIONS = ["(Default)", "Skinny Tie", "Wide Tie", "Bowtie", "None"]
        self.tie_options_hidden_var = False

        self.head_hpr_vars = {}
        self.prop1_vars = {}
        self.prop2_vars = {}
        self.custom_model_vars = {}
        self.custom_model_tab_frame = None
        self.prop_notebook = None
        self.bottom_notebook = None
        self.selected_tie_var = tk.StringVar(value="(Default)")

        # --- NEW: Prop anim UI storage ---
        self.prop1_anim_frame = None
        self.prop2_anim_frame = None
        self.prop1_anim_listbox = None
        self.prop2_anim_listbox = None
        self.prop1_anim_slider = None
        self.prop2_anim_slider = None
        self.prop1_loop_var = tk.BooleanVar(value=True)
        self.prop2_loop_var = tk.BooleanVar(value=True)

        self.master.title("Corporate Clash Cog Viewer")
        self.master.geometry("600x900")

        # --- NEW TOP-LEVEL NOTEBOOK (Request #1) ---
        top_level_notebook = ttk.Notebook(self)
        top_level_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 1. Cog Tab ---
        cog_tab_frame = ttk.Frame(top_level_notebook)
        top_level_notebook.add(cog_tab_frame, text="Cog")

        # --- 2. Prop Tab ---
        prop_tab_frame = ttk.Frame(top_level_notebook)
        top_level_notebook.add(prop_tab_frame, text="Props")

        # --- [POPULATE COG TAB] ---
        # This pane holds (Cog List + Tie List + Anims) AND (Toggles + HPR)
        main_paned_window = ttk.PanedWindow(cog_tab_frame, orient=tk.VERTICAL)
        main_paned_window.pack(fill="both", expand=True)

        # Top Frame: Cogs, Anims
        top_frame = ttk.Frame(main_paned_window)
        main_paned_window.add(top_frame, weight=20)

        # This pane holds the Cog/Body/Head lists side-by-side
        top_paned_window = ttk.PanedWindow(top_frame, orient=tk.HORIZONTAL)
        top_paned_window.pack(fill="both", expand=True)

        # Cog List
        cog_notebook = ttk.Notebook(top_paned_window)
        top_paned_window.add(cog_notebook, weight=1)

        COG_DEPARTMENTS = {
            "Sellbots": globals.SELLBOTS,
            "Cashbots": globals.CASHBOTS,
            "Lawbots": globals.LAWBOTS,
            "Bossbots": globals.BOSSBOTS,
            "Boardbots": globals.BOARDBOTS,
            "Misc": globals.MISC
        }
        self.DEPT_ICONS = {
            "Sellbots": PhotoImage(file="../resources/ICONS/icon_sellbot.png"),
            "Cashbots": PhotoImage(file="../resources/ICONS/icon_cashbot.png"),
            "Lawbots": PhotoImage(file="../resources/ICONS/icon_lawbot.png"),
            "Bossbots": PhotoImage(file="../resources/ICONS/icon_bossbot.png"),
            "Boardbots": PhotoImage(file="../resources/ICONS/icon_boardbot.png"),
            "Misc": PhotoImage(file="../resources/ICONS/icon_misc.png")
        }
        for dept_name, dept_data in COG_DEPARTMENTS.items():
            frame = self._create_scrollable_radio_list(cog_notebook, dept_name, dept_data, self.selected_cog_var,
                                                       self.on_cog_select_radio)
            cog_notebook.add(frame, image=self.DEPT_ICONS[dept_name], compound="none")

        # Body Anim List
        self.body_anim_frame = self._create_listbox_frame(top_paned_window, "Body Animations")
        self.body_anim_listbox = self.body_anim_frame.listbox
        self.body_anim_listbox.bind('<<ListboxSelect>>', self.on_body_anim_select)
        top_paned_window.add(self.body_anim_frame, weight=1)

        # Head Anim List
        self.head_anim_frame = self._create_listbox_frame(top_paned_window, "Head Animations")
        self.head_anim_listbox = self.head_anim_frame.listbox
        self.head_anim_listbox.bind('<<ListboxSelect>>', self.on_head_anim_select)
        top_paned_window.add(self.head_anim_frame, weight=1)

        # Bottom Frame: Sliders and Toggles
        bottom_frame = ttk.Frame(main_paned_window)
        main_paned_window.add(bottom_frame, weight=1)

        self.bottom_notebook = ttk.Notebook(bottom_frame)
        self.bottom_notebook.pack(fill="both", expand=True)

        bottom_notebook = self.bottom_notebook

        # Toggles Tab
        toggles_frame = ttk.Frame(bottom_notebook, padding=10)
        bottom_notebook.add(toggles_frame, text='Toggles')
        self._create_toggles(toggles_frame)

        # Animation Tab
        anim_sliders_frame = ttk.Frame(bottom_notebook, padding=10)
        bottom_notebook.add(anim_sliders_frame, text='Animation')
        self._create_anim_sliders(anim_sliders_frame)

        # Head HPR Tab
        head_hpr_frame = ttk.Frame(bottom_notebook, padding=10)
        bottom_notebook.add(head_hpr_frame, text='Head HPR')
        self._create_head_hpr_sliders(head_hpr_frame)

        # Accessory Tab
        self.custom_model_tab_frame = ttk.Frame(self.bottom_notebook, padding=10)
        self.bottom_notebook.add(self.custom_model_tab_frame, text='Accessory')
        self.bottom_notebook.hide(self.custom_model_tab_frame)

        prop_paned_window = ttk.PanedWindow(prop_tab_frame, orient=tk.VERTICAL)
        prop_paned_window.pack(fill="both", expand=True)

        prop_list_frame = ttk.Frame(prop_paned_window)
        prop_paned_window.add(prop_list_frame, weight=1)

        middle_paned_window = ttk.PanedWindow(prop_list_frame, orient=tk.HORIZONTAL)
        middle_paned_window.pack(fill="both", expand=True)

        (self.prop1_frame,
         self.prop1_listbox,
         self.prop1_search_entry) = self._create_searchable_listbox_frame(
            middle_paned_window, "Prop 1 (R-Hand)", "Search Prop")
        self.prop1_listbox.bind('<Double-Button-1>', self.on_prop1_select)
        self.prop1_search_entry.bind("<KeyRelease>", self.on_prop1_search)
        middle_paned_window.add(self.prop1_frame, weight=1)

        (self.prop2_frame,
         self.prop2_listbox,
         self.prop2_search_entry) = self._create_searchable_listbox_frame(
            middle_paned_window, "Prop 2 (L-Hand)", "Search Prop")
        self.prop2_listbox.bind('<Double-Button-1>', self.on_prop2_select)
        self.prop2_search_entry.bind("<KeyRelease>", self.on_prop2_search)
        middle_paned_window.add(self.prop2_frame, weight=1)

        self.update_prop_lists()

        prop_controls_frame = ttk.Frame(prop_paned_window)
        prop_paned_window.add(prop_controls_frame, weight=1)

        self.prop_notebook = ttk.Notebook(prop_controls_frame)
        self.prop_notebook.pack(fill="both", expand=True)

        prop1_hpr_frame = ttk.Frame(self.prop_notebook, padding=10)
        self.prop_notebook.add(prop1_hpr_frame, text='Prop 1 HPR')
        self._create_prop_sliders(prop1_hpr_frame, self.app.update_prop_hpr)

        prop2_hpr_frame = ttk.Frame(self.prop_notebook, padding=10)
        self.prop_notebook.add(prop2_hpr_frame, text='Prop 2 HPR')
        self._create_prop_sliders(prop2_hpr_frame, self.app.update_prop2_hpr)

        self.prop1_anim_frame = ttk.Frame(self.prop_notebook, padding=10)
        self.prop_notebook.add(self.prop1_anim_frame, text='Prop 1 Animation')

        (self.prop1_anim_listbox,
         self.prop1_anim_slider) = self._create_anim_controls(
            self.prop1_anim_frame,
            self.app.on_prop1_anim_select,
            self.app.play_prop1_animation,
            self.app.stop_prop1_animation,
            self.app.update_prop1_pose,
            self.prop1_loop_var
        )
        self.prop_notebook.hide(self.prop1_anim_frame)

        self.prop2_anim_frame = ttk.Frame(self.prop_notebook, padding=10)
        self.prop_notebook.add(self.prop2_anim_frame, text='Prop 2 Animation')

        (self.prop2_anim_listbox,
         self.prop2_anim_slider) = self._create_anim_controls(
            self.prop2_anim_frame,
            self.app.on_prop2_anim_select,
            self.app.play_prop2_animation,
            self.app.stop_prop2_animation,
            self.app.update_prop2_pose,
            self.prop2_loop_var
        )
        self.prop_notebook.hide(self.prop2_anim_frame)

    def _create_listbox_frame(self, master, label_text):
        frame = ttk.Labelframe(master, text=label_text)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, exportselection=False)

        scrollbar.config(command=listbox.yview)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill="both", expand=True)

        frame.listbox = listbox
        return frame

    def _create_searchable_listbox_frame(self, master, label_text, placeholder_text="Search..."):
        frame = ttk.Labelframe(master, text=label_text)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        search_entry = ttk.Entry(frame)
        search_entry.pack(fill="x", padx=5, pady=(5, 2))

        search_entry.insert(0, placeholder_text)
        search_entry.config(foreground='grey')
        search_entry.bind("<FocusIn>",
                          lambda e: self._on_entry_focus_in(search_entry, placeholder_text))
        search_entry.bind("<FocusOut>",
                          lambda e: self._on_entry_focus_out(search_entry, placeholder_text))

        list_container = ttk.Frame(frame)
        list_container.pack(fill="both", expand=True, padx=5, pady=(2, 5))

        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL)
        listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set, exportselection=False)

        scrollbar.config(command=listbox.yview)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill="both", expand=True)

        return frame, listbox, search_entry

    # SETTING UP TOGGLES
    def _create_toggles(self, master):
        frame = ttk.Frame(master)
        self.toggles_frame = frame
        frame.pack(fill="x", expand=True)

        frame.columnconfigure(0, weight=1)  # Column 1
        frame.columnconfigure(1, weight=1)  # Column 2
        frame.columnconfigure(2, weight=1)  # Column 3

        # Cog Shadow Toggle
        ttk.Checkbutton(frame, text="Toggle Shadow", variable=self.is_shadow_var,
                        command=self.app.toggle_shadow).grid(row=0, column=0, sticky="w", pady=2)
        # Cog Body Toggle
        ttk.Checkbutton(frame, text="Toggle Body", variable=self.is_body_var,
                        command=self.app.toggle_body).grid(row=1, column=0, sticky="w", pady=2)
        # Autoplay Animation Toggle
        ttk.Checkbutton(frame, text="Autoplay Animations", variable=self.is_autoplay_var,
                        command=self.app.autoplay_animations).grid(row=2, column=0, sticky="w", pady=2)
        # Background Color Toggle
        ttk.Checkbutton(frame, text="Black Background", variable=self.is_background_black_var,
                        command=self.app.toggle_background).grid(row=3, column=0, sticky="w", pady=2)
        # Flatten Cog Toggle
        ttk.Checkbutton(frame, text="Flatten Cog", variable=self.is_flattened_var,
                        command=self.app.toggle_flatten).grid(row=4, column=0, sticky="w", pady=2)
        # Manager Costume Toggle
        self.costume_button = ttk.Checkbutton(frame, text="Toggle Costume", variable=self.is_costume_var,
                                              command=self.app.toggle_costume)
        self.costume_button.grid(row=5, column=0, sticky="w", pady=2)
        self.costume_button.grid_remove()

        self.tie_frame = self._create_radio_list(frame, "Necktie Toggles", self.TIE_OPTIONS, self.selected_tie_var,
                                                 self.on_tie_select_radio)
        self.tie_frame.grid(row=0, column=2, rowspan=5, sticky="nsew", padx=5, pady=2)

        suit_frame = ttk.Labelframe(frame, text="Suit Toggles")
        suit_frame.grid(row=5, column=2, rowspan=3, sticky="nsew", padx=5, pady=2)

        # Standard Toggles
        self.is_executive_var = tk.BooleanVar(value=False)
        self.is_fired_var = tk.BooleanVar(value=False)
        self.is_waiter_var = tk.BooleanVar(value=False)

        self.suit_exec_check = ttk.Checkbutton(suit_frame, text="Make Executive",
                                               variable=self.is_executive_var,
                                               command=lambda: self.app.set_suit_texture("exec"))
        self.suit_exec_check.pack(anchor="w", padx=5)

        self.suit_fired_check = ttk.Checkbutton(suit_frame, text="Make Fired",
                                                variable=self.is_fired_var,
                                                command=lambda: self.app.set_suit_texture("fired"))
        self.suit_fired_check.pack(anchor="w", padx=5)

        self.suit_waiter_check = ttk.Checkbutton(suit_frame, text="Make Waiter",
                                                 variable=self.is_waiter_var,
                                                 command=lambda: self.app.set_suit_texture("waiter"))
        self.suit_waiter_check.pack(anchor="w", padx=5)

        # Unique Toggles
        self.unique_suit_button = ttk.Button(suit_frame, text="Cycle Unique Texture",
                                             command=self.app.toggle_unique_suit)
        self.unique_suit_button.pack(anchor="w", fill="x", padx=5, pady=5)

        self.ds_frame = ttk.Frame(suit_frame)
        self.ds_l_btn = ttk.Button(self.ds_frame, text="Cycle Left Slot",
                                   command=self.app.cycle_slot_l)
        self.ds_l_btn.pack(fill="x", expand=True, pady=1)

        self.ds_m_btn = ttk.Button(self.ds_frame, text="Cycle Mid Slot",
                                   command=self.app.cycle_slot_m)
        self.ds_m_btn.pack(fill="x", expand=True, pady=1)

        self.ds_r_btn = ttk.Button(self.ds_frame, text="Cycle Right Slot",
                                   command=self.app.cycle_slot_r)
        self.ds_r_btn.pack(fill="x", expand=True, pady=1)

        # Hide all suit toggles by default
        self.suit_exec_check.pack_forget()
        self.suit_fired_check.pack_forget()
        self.unique_suit_button.pack_forget()
        self.suit_waiter_check.pack_forget()
        self.ds_frame.pack_forget()

        ttk.Button(frame, text="Toggle Virtualize",
                   command=self.app.toggle_virtualize).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Cycle Health Meter",
                   command=self.app.toggle_skele_meter_color).grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        self.suit_toggle_button = ttk.Button(frame, text="Toggle Suit Type",
                                             command=self.app.toggle_suit)
        self.suit_toggle_button.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        self.suit_toggle_button.grid_remove()

        ttk.Button(frame, text="Reset Camera",
                   command=self.app.reset_camera_pos).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Reset Camera Roll",
                   command=self.app.reset_camera_roll).grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Upload Suit Texture",
                   command=self.app.upload_suit_texture).grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Upload Accessory",
                   command=self.app.upload_custom_model).grid(row=5, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Take Screenshot",
                   command=self.app.take_screenshot).grid(row=6, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Render Frames",
                   command=self.app.take_screenshot_frames).grid(row=7, column=1, sticky="ew", padx=5, pady=2)

    def _create_anim_controls(self, master, list_select_cmd, play_cmd, stop_cmd, slider_cmd, loop_var):
        # Anim List
        list_frame = ttk.Labelframe(master, text="Animations")
        list_frame.pack(fill="x", expand=True, padx=5, pady=5)

        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        anim_listbox = tk.Listbox(list_frame, yscrollcommand=list_scrollbar.set, exportselection=False, height=5)
        list_scrollbar.config(command=anim_listbox.yview)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        anim_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        anim_listbox.bind('<<ListboxSelect>>', list_select_cmd)

        # Slider and Controls
        slider_frame = ttk.Labelframe(master, text="Controls")
        slider_frame.pack(fill="x", expand=True, padx=5, pady=5)

        ttk.Label(slider_frame, text="Animation Frame").pack(fill="x", expand=True)

        anim_slider = ttk.Scale(slider_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                command=slider_cmd, length=300, name="anim_slider")
        anim_slider.set(0)
        anim_slider.pack(fill="x", expand=True, pady=(0, 10))

        button_frame = ttk.Frame(slider_frame)
        button_frame.pack(fill="x", expand=True)

        ttk.Button(button_frame, text="Play", command=play_cmd).pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        ttk.Button(button_frame, text="Stop", command=stop_cmd).pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        ttk.Checkbutton(button_frame, text="Loop", variable=loop_var).pack(side=tk.LEFT, fill="x", expand=True, padx=5)

        return anim_listbox, anim_slider

    def _create_anim_controls_only(self, master, slider_cmd, play_cmd, stop_cmd, loop_var):
        # Slider and Controls
        slider_frame = ttk.Labelframe(master, text="Controls")
        slider_frame.pack(fill="x", expand=True, padx=5, pady=5)

        ttk.Label(slider_frame, text="Animation Frame").pack(fill="x", expand=True)

        anim_slider = ttk.Scale(slider_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                command=slider_cmd, length=300, name="anim_slider")
        anim_slider.set(0)
        anim_slider.pack(fill="x", expand=True, pady=(0, 10))

        button_frame = ttk.Frame(slider_frame)
        button_frame.pack(fill="x", expand=True)

        ttk.Button(button_frame, text="Play", command=play_cmd).pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        ttk.Button(button_frame, text="Stop", command=stop_cmd).pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        ttk.Checkbutton(button_frame, text="Loop", variable=loop_var).pack(side=tk.LEFT, fill="x", expand=True, padx=5)

        return anim_slider

    def _create_anim_sliders(self, master):
        # Body
        body_frame = ttk.Labelframe(master, text="Body Animation")
        body_frame.pack(fill="x", expand=True, padx=5, pady=5)

        self.body_frame_slider = self._create_anim_controls_only(
            body_frame,
            self.app.update_body_pose,
            self.app.play_body_animation,
            self.app.stop_body_animation,
            self.loop_body_var
        )

        # Head
        head_frame = ttk.Labelframe(master, text="Head Animation")
        head_frame.pack(fill="x", expand=True, padx=5, pady=5)

        self.head_frame_slider = self._create_anim_controls_only(
            head_frame,
            self.app.update_head_pose,
            self.app.play_head_animation,
            self.app.stop_head_animation,
            self.loop_head_var
        )

    def _create_head_hpr_sliders(self, master):
        slider_defs = [
            ("Heading (H)", "h", -360, 360, 0.0),
            ("Pitch (P)", "p", -180, 180, 0.0),
            ("Roll (R)", "r", -360, 360, 0.0),
        ]

        main_frame = ttk.Frame(master)
        main_frame.pack(fill="x", expand=True)

        for label, axis, min_val, max_val, default_val in slider_defs:
            var = tk.DoubleVar(value=default_val)
            self.head_hpr_vars[axis] = var

            # Row frame
            row = ttk.Frame(main_frame)
            row.pack(fill="x", expand=True, pady=2)

            # Label
            ttk.Label(row, text=label, width=10, anchor="w").pack(side=tk.LEFT, padx=(0, 5))

            # Slider
            scale = ttk.Scale(row, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var)
            scale.pack(side=tk.LEFT, fill="x", expand=True, padx=5)

            # Text Entry
            entry = ttk.Entry(row, textvariable=var, width=7)
            entry.pack(side=tk.LEFT, padx=5)

            # Reset Button
            reset_btn = ttk.Button(row, text="Reset", width=6,
                                   command=lambda v=var, val=default_val: v.set(val))
            reset_btn.pack(side=tk.LEFT)

            var.trace_add("write", self._create_hpr_trace_callback(var, axis))

        # Reset All Button
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill='x', expand=True, pady=10)
        reset_all_btn = ttk.Button(main_frame, text="Reset All Head HPR", command=self.reset_head_hpr)
        reset_all_btn.pack(fill="x", expand=True)

    def _create_prop_sliders(self, master, update_callback):
        is_prop1 = (update_callback == self.app.update_prop_hpr)
        vars_dict = self.prop1_vars if is_prop1 else self.prop2_vars

        slider_defs = [
            ("Pos X", "x", -30, 30, 0.0),
            ("Pos Y", "y", -30, 30, 0.0),
            ("Pos Z", "z", -30, 30, 0.0),
            ("Heading", "h", -360, 360, 0.0),
            ("Pitch", "p", -180, 180, 0.0),
            ("Roll", "r", -360, 360, 0.0),
            ("Scale", "scale", 0.1, 15, 1.0),
        ]

        # Frame for all controls
        main_frame = ttk.Frame(master)
        main_frame.pack(fill="x", expand=True)

        for label, axis, min_val, max_val, default_val in slider_defs:
            var = tk.DoubleVar(value=default_val)
            vars_dict[axis] = var

            # Row frame
            row = ttk.Frame(main_frame)
            row.pack(fill="x", expand=True, pady=2)

            # Label
            ttk.Label(row, text=label, width=10, anchor="w").pack(side=tk.LEFT, padx=(0, 5))

            # Slider
            scale = ttk.Scale(row, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var)
            scale.pack(side=tk.LEFT, fill="x", expand=True, padx=5)

            # Text Entry
            entry = ttk.Entry(row, textvariable=var, width=7)
            entry.pack(side=tk.LEFT, padx=5)

            # Reset Button
            reset_btn = ttk.Button(row, text="Reset", width=6,
                                   command=lambda v=var, val=default_val: v.set(val))
            reset_btn.pack(side=tk.LEFT)

            var.trace_add("write", self._create_prop_trace_callback(var, axis, update_callback))

        # Reset All Button
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill='x', expand=True, pady=10)
        reset_all_btn = ttk.Button(main_frame, text="Reset All Prop Controls",
                                   command=lambda d=vars_dict: self.reset_prop_sliders(d))
        reset_all_btn.pack(fill="x", expand=True)

    def _create_scrollable_radio_list(self, master, label_text, items, variable, command, width=200):
        frame = ttk.Labelframe(master, text=label_text)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set, borderwidth=0, highlightthickness=0, width=width,
                           height=100)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)

        scrollbar.config(command=canvas.yview)
        inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        for item in items:
            ttk.Radiobutton(
                inner_frame,
                text=item,
                variable=variable,
                value=item,
                command=command
            ).pack(anchor="nw", fill="x", padx=5, pady=1)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", on_frame_configure)

        def _on_mouse_wheel(event):
            if event.num == 5 or event.delta < 0:
                delta = 1
            else:
                delta = -1
            canvas.yview_scroll(delta, "units")

        widgets_to_bind = [canvas, inner_frame] + inner_frame.winfo_children()
        for widget in widgets_to_bind:
            widget.bind("<MouseWheel>", _on_mouse_wheel, add='+')
            widget.bind("<Button-4>", _on_mouse_wheel, add='+')
            widget.bind("<Button-5>", _on_mouse_wheel, add='+')

        return frame

    # Same thing as scrollable_radio_list but not scrollable basically
    def _create_radio_list(self, master, label_text, items, variable, command):
        frame = ttk.Labelframe(master, text=label_text)
        self.radio_list_frame = ttk.Frame(frame)

        for item in items:
            ttk.Radiobutton(
                self.radio_list_frame,
                text=item,
                variable=variable,
                value=item,
                command=command).pack(anchor="nw", fill="x", padx=5, pady=1)

        self.radio_list_frame.pack(fill="both", expand=True)

        return frame

    # Hide tie list
    def hide_tie_list(self):
        self.radio_list_frame.grid_forget()
        self.tie_options_hidden_var = True

    # Show tie list
    def show_tie_list(self):
        self.radio_list_frame.grid(row=0, column=2, rowspan=5, sticky="nsew", padx=5, pady=2)
        self.tie_options_hidden_var = False

    def _on_entry_focus_in(self, entry_widget, placeholder_text):
        if entry_widget.get() == placeholder_text:
            entry_widget.delete(0, tk.END)
            entry_widget.config(foreground='black')

    def _on_entry_focus_out(self, entry_widget, placeholder_text):
        if not entry_widget.get():
            entry_widget.config(foreground='grey')
            entry_widget.insert(0, placeholder_text)

    def filter_listbox(self, listbox_widget, search_term):
        all_props = sorted(list(self.app.available_props.keys()), key=str.lower)

        listbox_widget.delete(0, tk.END)

        if not search_term:
            for prop in all_props:
                listbox_widget.insert(tk.END, prop)
        else:
            for prop in all_props:
                if search_term in prop.lower():
                    listbox_widget.insert(tk.END, prop)

    def on_prop1_search(self, event):
        search_term = self.prop1_search_entry.get().lower()

        if search_term == "search prop":
            search_term = ""

        self.filter_listbox(self.prop1_listbox, search_term)

    def on_prop2_search(self, event):
        search_term = self.prop2_search_entry.get().lower()

        if search_term == "search prop":
            search_term = ""

        self.filter_listbox(self.prop2_listbox, search_term)

    def update_animation_lists(self, body_anims, head_anims):
        self.body_anim_listbox.delete(0, tk.END)
        for anim in body_anims:
            if not anim == "lose" and not anim == "lose_zero":
                self.body_anim_listbox.insert(tk.END, anim)

        self.head_anim_listbox.delete(0, tk.END)
        for anim in head_anims:
            self.head_anim_listbox.insert(tk.END, anim)

    def update_prop_lists(self):
        search_term1 = self.prop1_search_entry.get().lower()
        if search_term1 == "search prop":
            search_term1 = ""

        search_term2 = self.prop2_search_entry.get().lower()
        if search_term2 == "search prop":
            search_term2 = ""

        self.filter_listbox(self.prop1_listbox, search_term1)
        self.filter_listbox(self.prop2_listbox, search_term2)

    def setup_prop_anim_ui(self, listbox, slider, anim_frame, actor):
        anims = actor.getAnimNames()
        listbox.delete(0, tk.END)
        for anim in anims:
            listbox.insert(tk.END, anim)

        try:
            self.prop_notebook.add(anim_frame)  # 'add' also un-hides a hidden tab
        except tk.TclError:
            pass  # Tab already visible

    def hide_prop_anim_ui(self, anim_frame):
        try:
            self.prop_notebook.hide(anim_frame)  # Hide the tab
        except tk.TclError:
            pass  # Tab already hidden

    def update_prop_slider_range(self, slider, num_frames):
        if num_frames <= 1: num_frames = 1
        slider.config(to=num_frames - 1)
        slider.set(0)

    def update_anim_slider_range(self, slider_name, num_frames):
        if num_frames <= 1:
            num_frames = 1

        if slider_name == "body":
            self.body_frame_slider.config(to=num_frames - 1)
            self.body_frame_slider.set(0)
        elif slider_name == "head":
            self.head_frame_slider.config(to=num_frames - 1)
            self.head_frame_slider.set(0)

    def _create_hpr_trace_callback(self, var, axis):
        def trace_callback(*args):
            try:
                self.app.update_hpr(axis, var.get())
            except tk.TclError:
                pass

        return trace_callback

    def _create_prop_trace_callback(self, var, axis, update_func):
        def trace_callback(*args):
            try:
                update_func(axis, var.get())
            except tk.TclError:
                pass

        return trace_callback

    def reset_head_hpr(self):
        for var in self.head_hpr_vars.values():
            var.set(0.0)

    def reset_prop_sliders(self, vars_dict):
        for axis, var in vars_dict.items():
            if axis == "scale":
                var.set(1.0)
            else:
                var.set(0.0)

    def setup_custom_model_tab(self):
        self._create_prop_sliders(self.custom_model_tab_frame, self.app.update_custom_model_hpr)

    def show_custom_model_tab(self, show=True):
        if show:
            try:
                self.bottom_notebook.add(self.custom_model_tab_frame, text='Accessory HPR')
            except tk.TclError:
                pass
        else:
            try:
                self.bottom_notebook.hide(self.custom_model_tab_frame)
            except tk.TclError:
                pass

    def on_cog_select_radio(self):
        cog_name = self.selected_cog_var.get()
        if cog_name:
            self.app.load_cog(cog_name)

    def _get_selected_from_listbox(self, event):
        widget = event.widget
        selection = widget.curselection()
        if selection:
            index = selection[0]
            return widget.get(index)
        return None

    def on_tie_select_radio(self):
        tie_name = self.selected_tie_var.get()
        if tie_name:
            self.app.set_necktie(tie_name)

    def on_body_anim_select(self, event):
        anim_name = self._get_selected_from_listbox(event)
        if anim_name:
            self.app.set_animation(anim_name)
            if self.is_autoplay_var.get():  # Autoplay on
                self.app.play_body_animation()
            else:  # Autoplay off
                self.app.stop_body_animation()

    def on_head_anim_select(self, event):
        anim_name = self._get_selected_from_listbox(event)
        if anim_name:
            self.app.set_head_animation(anim_name)

            if self.is_autoplay_var.get():  # Autoplay on
                self.app.play_head_animation()
            else:  # Autoplay off
                self.app.stop_head_animation()

    def on_prop1_select(self, event):
        prop_name = self._get_selected_from_listbox(event)
        if prop_name:
            self.app.set_prop(prop_name)

    def on_prop2_select(self, event):
        prop_name = self._get_selected_from_listbox(event)
        if prop_name:
            self.app.set_prop2(prop_name)


class CogViewer(ShowBase):
    def __init__(self):
        loadPrcFileData("", "want-tk #t")
        ShowBase.__init__(self)
        self.base = base
        self.render = render
        self.clock = ClockObject.getGlobalClock()
        self.screenshot_path = globals.SCREENSHOT_DIR
        self.frame_index = 0
        self.available_props = globals.PROPS_DICT
        self.bool = False
        self.cog_data = None
        self.actor = None
        self.available_animations = []
        self.available_head_animations = []
        self.is_autoplay = True  # Used for autoplay animation toggle
        self.is_shadow = True  # Used for toggle shadow
        self.is_posed = False
        self.is_blend = True
        self.is_costume_active = False  # Used for toggle costume
        self.is_body = True  # Used for toggle body
        self.current_animation = "zero"
        self.current_head_animation = "zero"
        self.current_prop1 = "zero"
        self.previous_prop1 = "zero"
        self.prop_item1 = "zero"
        self.current_prop2 = "zero"
        self.previous_prop2 = "zero"
        self.prop_item2 = "zero"
        self.last_pose_frame = 0
        self.cog_list = list(globals.COG_DATA)
        self.current_cog_index = 0
        self.current_cog = self.cog_list[self.current_cog_index]
        self.custom_model = None
        self.suit_is_executive = False
        self.suit_is_fired = False
        self.prop_item1_actor = None
        self.prop_item2_actor = None

        self.control_panel = ControlPanel(self.base.tkRoot, self)
        self.control_panel.setup_custom_model_tab()
        self.shadow = loader.loadModel(globals.SHADOW_MODEL)
        self.shadow.setScale(globals.SHADOW_SCALE)
        self.shadow.setColor(globals.SHADOW_COLOR)

        self.skele_i = 0
        self.skele_meter_color = 0
        self.flatten_switch = 0
        self.it = 0
        self.it2 = 0
        self.it_l = 0
        self.it_m = 0
        self.it_r = 0

        self.current_cog_index = 0
        self.current_cog = self.cog_list[self.current_cog_index]
        self.build_cog()

        self.reset_actor_pos()
        self.reset_camera_pos()

        self.accept("r", self.reset_camera_roll)
        self.accept("f9", self.take_screenshot)
        self.accept("f10", self.take_screenshot_frames)
        self.accept("control-z", self.reset_camera_pos)

    def load_cog(self, cog_name):
        self.current_cog = cog_name
        self.build_cog()

        try:
            self.control_panel.selected_cog_var.set(cog_name)
        except Exception as e:
            print(f"Could not update cog selection: {e}")

    def update_hpr(self, axis, value):
        if not hasattr(self, 'head') or self.head.isEmpty():
            return
        if axis == "h":
            self.head.setH(value)
        elif axis == "p":
            self.head.setP(value)
        elif axis == "r":
            self.head.setR(value)

    def _get_selected_from_listbox(self, event):
        widget = event.widget
        selection = widget.curselection()
        if selection:
            index = selection[0]
            return widget.get(index)
        return None

    def update_prop_hpr(self, axis, value):
        item_to_move = self.prop_item1_actor if self.prop_item1_actor else self.prop_item1

        if item_to_move != "zero" and not item_to_move.isEmpty():
            if axis == "x":
                item_to_move.setX(value)
            elif axis == "y":
                item_to_move.setY(value)
            elif axis == "z":
                item_to_move.setZ(value)
            elif axis == "h":
                item_to_move.setH(value)
            elif axis == "p":
                item_to_move.setP(value)
            elif axis == "r":
                item_to_move.setR(value)
            elif axis == "scale":
                item_to_move.setScale(value)

    def update_prop2_hpr(self, axis, value):
        item_to_move = self.prop_item2_actor if self.prop_item2_actor else self.prop_item2

        if item_to_move != "zero" and not item_to_move.isEmpty():
            if axis == "x":
                item_to_move.setX(value)
            elif axis == "y":
                item_to_move.setY(value)
            elif axis == "z":
                item_to_move.setZ(value)
            elif axis == "h":
                item_to_move.setH(value)
            elif axis == "p":
                item_to_move.setP(value)
            elif axis == "r":
                item_to_move.setR(value)
            elif axis == "scale":
                item_to_move.setScale(value)

    def set_prop(self, prop):
        if self.prop_item1_actor:
            self.prop_item1_actor.cleanup()
            self.prop_item1_actor.removeNode()
            self.prop_item1_actor = None
        if self.prop_item1 != "zero" and not self.prop_item1.isEmpty():
            self.prop_item1.removeNode()
            self.prop_item1 = "zero"
        self.control_panel.hide_prop_anim_ui(self.control_panel.prop1_anim_frame)

        if self.current_prop1 == prop:
            # Clicked same prop, toggle off
            self.current_prop1 = "zero"
            return

        self.current_prop1 = prop
        prop_data = globals.PROPS_DICT[prop]

        if prop_data.get("anims"):
            # It's an animated prop
            self.prop_item1_actor = Actor(prop_data["model"], prop_data["anims"])
            self.prop_item1_actor.reparentTo(self.actor.find('**/joint_Rhold'))
            self.control_panel.setup_prop_anim_ui(
                self.control_panel.prop1_anim_listbox,
                self.control_panel.prop1_anim_slider,
                self.control_panel.prop1_anim_frame,
                self.prop_item1_actor
            )
        else:
            # It's a static prop
            self.prop_item1 = loader.loadModel(prop_data["model"])
            self.prop_item1.reparentTo(self.actor.find('**/joint_Rhold'))

        if prop == "flintbass":  # i hate this prop
            try:
                texture_path = os.path.join(globals.RESOURCES_DIR, "phase_12", "maps", "flintbass.png")
                tex_node = self.prop_item1_actor if self.prop_item1_actor else self.prop_item1
                if os.path.isfile(texture_path):
                    prop_texture = loader.loadTexture(texture_path)
                    tex_node.setTexture(prop_texture, 1)
                else:
                    print(f"Warning: Looked for {texture_path} but didn't find it.")
            except Exception as e:
                print(f"Error applying flintbass texture: {e}")

        self.control_panel.reset_prop_sliders(self.control_panel.prop1_vars)

    def set_prop2(self, prop2):
        if self.prop_item2_actor:
            self.prop_item2_actor.cleanup()
            self.prop_item2_actor.removeNode()
            self.prop_item2_actor = None
        if self.prop_item2 != "zero" and not self.prop_item2.isEmpty():
            self.prop_item2.removeNode()
            self.prop_item2 = "zero"
        self.control_panel.hide_prop_anim_ui(self.control_panel.prop2_anim_frame)

        if self.current_prop2 == prop2:
            self.current_prop2 = "zero"
            return

        self.current_prop2 = prop2
        prop_data = globals.PROPS_DICT[prop2]

        if prop_data.get("anims"):
            # It's an animated prop
            self.prop_item2_actor = Actor(prop_data["model"], prop_data["anims"])
            self.prop_item2_actor.reparentTo(self.actor.find('**/joint_Lhold'))
            self.control_panel.setup_prop_anim_ui(
                self.control_panel.prop2_anim_listbox,
                self.control_panel.prop2_anim_slider,
                self.control_panel.prop2_anim_frame,
                self.prop_item2_actor
            )
        else:
            # It's a static prop
            self.prop_item2 = loader.loadModel(prop_data["model"])
            self.prop_item2.reparentTo(self.actor.find('**/joint_Lhold'))

        if prop2 == "flintbass":
            try:
                texture_path = os.path.join(globals.RESOURCES_DIR, "phase_12", "maps", "flintbass.png")
                tex_node = self.prop_item2_actor if self.prop_item2_actor else self.prop_item2
                if os.path.isfile(texture_path):
                    prop_texture = loader.loadTexture(texture_path)
                    tex_node.setTexture(prop_texture, 1)
                else:
                    print(f"Warning: Looked for {texture_path} but didn't find it.")
            except Exception as e:
                print(f"Error applying flintbass texture: {e}")

        self.control_panel.reset_prop_sliders(self.control_panel.prop2_vars)

    def set_head_animation(self, animation):
        self.current_head_animation = animation
        self.head.loop(animation)
        self.is_posed = False

        try:
            num_frames = self.head.getNumFrames(self.current_head_animation)
            self.control_panel.update_anim_slider_range("head", num_frames)
        except:
            self.control_panel.update_anim_slider_range("head", 0)

    def set_animation(self, animation):
        self.current_animation = animation
        self.actor.loop(animation)
        self.is_posed = False

        try:
            num_frames = self.actor.getNumFrames(self.current_animation)
            self.control_panel.update_anim_slider_range("body", num_frames)
        except:
            self.control_panel.update_anim_slider_range("body", 0)

    def take_screenshot(self):
        path = globals.SCREENSHOT_DIR
        if not os.path.exists(path):
            os.makedirs(path)
        now = datetime.now()
        date_string = now.strftime("%d-%m-%Y-%H-%M-%S")
        screenshot_name = os.path.join(path, "ss-{}-{}.png".format(self.current_cog, date_string))
        self.base.screenshot(screenshot_name, False)

    def toggle_background(self):
        self.bool = self.control_panel.is_background_black_var.get()
        if self.bool:
            self.setBackgroundColor(0, 0, 0)
        else:
            self.setBackgroundColor(105 / 255, 105 / 255, 105 / 255)

    def enable_mouse_cam(self):
        mat = Mat4(camera.getMat())
        mat.invertInPlace()
        base.mouseInterfaceNode.setMat(mat)
        base.enableMouse()

    def disable_mouse_cam(self):
        base.disableMouse()

    def reset_camera_roll(self):
        self.disable_mouse_cam()
        camera.setR(0)
        self.enable_mouse_cam()

    def reset_actor_pos(self):
        if self.actor:
            self.actor.setPosHpr(*globals.DEFAULT_POS, *globals.DEFAULT_HPR)

    def reset_camera_pos(self):
        self.disable_mouse_cam()
        base.camera.setPosHpr(*globals.DEFAULT_CAMERA_POS, 0, 0, 0)
        self.enable_mouse_cam()

    def play_body_animation(self):
        if self.actor and self.current_animation != "zero":
            self.is_posed = False
            if self.control_panel.loop_body_var.get():
                self.actor.loop(self.current_animation)
            else:
                self.actor.play(self.current_animation)

    def stop_body_animation(self):
        if self.actor and self.current_animation != "zero":
            self.is_posed = True
            self.actor.pose(self.current_animation, 0)
            self.control_panel.body_frame_slider.set(0)

    def play_head_animation(self):
        if hasattr(self, 'head') and self.head and self.current_head_animation != "zero":
            self.is_posed = False
            if self.control_panel.loop_head_var.get():
                self.head.loop(self.current_head_animation)
            else:
                self.head.play(self.current_head_animation)

    def stop_head_animation(self):
        if hasattr(self, 'head') and self.head and self.current_head_animation != "zero":
            self.is_posed = True
            self.head.pose(self.current_head_animation, 0)
            self.control_panel.head_frame_slider.set(0)

    def on_prop1_anim_select(self, event):
        anim_name = self._get_selected_from_listbox(event)
        if anim_name and self.prop_item1_actor:
            self.prop_item1_actor.stop()
            num_frames = self.prop_item1_actor.getNumFrames(anim_name)
            self.control_panel.update_prop_slider_range(self.control_panel.prop1_anim_slider, num_frames)

            if self.control_panel.is_autoplay_var.get():
                self.play_prop1_animation(anim_name)
            else:
                self.prop_item1_actor.pose(anim_name, 0)

    def play_prop1_animation(self, anim_name=None):
        if not self.prop_item1_actor: return
        if not anim_name:
            anim_name = self.prop_item1_actor.getCurrentAnim()
        if not anim_name: return

        if self.control_panel.prop1_loop_var.get():
            self.prop_item1_actor.loop(anim_name)
        else:
            self.prop_item1_actor.play(anim_name)
        self.prop_item1_actor.setBlend(frameBlend=self.is_blend)

    def stop_prop1_animation(self):
        if self.prop_item1_actor and self.prop_item1_actor.getCurrentAnim():
            anim_name = self.prop_item1_actor.getCurrentAnim()
            self.prop_item1_actor.pose(anim_name, 0)
            self.control_panel.prop1_anim_slider.set(0)

    def update_prop1_pose(self, frame_value):
        if self.prop_item1_actor and self.prop_item1_actor.getCurrentAnim():
            frame = int(round(float(frame_value)))
            self.prop_item1_actor.pose(self.prop_item1_actor.getCurrentAnim(), frame)

    def on_prop2_anim_select(self, event):
        anim_name = self._get_selected_from_listbox(event)
        if anim_name and self.prop_item2_actor:
            self.prop_item2_actor.stop()
            num_frames = self.prop_item2_actor.getNumFrames(anim_name)
            self.control_panel.update_prop_slider_range(self.control_panel.prop2_anim_slider, num_frames)

            if self.control_panel.is_autoplay_var.get():
                self.play_prop2_animation(anim_name)
            else:
                self.prop_item2_actor.pose(anim_name, 0)

    def play_prop2_animation(self, anim_name=None):
        if not self.prop_item2_actor: return
        if not anim_name:
            anim_name = self.prop_item2_actor.getCurrentAnim()
        if not anim_name: return

        if self.control_panel.prop2_loop_var.get():
            self.prop_item2_actor.loop(anim_name)
        else:
            self.prop_item2_actor.play(anim_name)
        self.prop_item2_actor.setBlend(frameBlend=self.is_blend)

    def stop_prop2_animation(self):
        if self.prop_item2_actor and self.prop_item2_actor.getCurrentAnim():
            anim_name = self.prop_item2_actor.getCurrentAnim()
            self.prop_item2_actor.pose(anim_name, 0)
            self.control_panel.prop2_anim_slider.set(0)

    def update_prop2_pose(self, frame_value):
        if self.prop_item2_actor and self.prop_item2_actor.getCurrentAnim():
            frame = int(round(float(frame_value)))
            self.prop_item2_actor.pose(self.prop_item2_actor.getCurrentAnim(), frame)

    def toggle_blend(self):
        self.is_blend = not self.is_blend
        self.control_panel.is_blend_var.set(self.is_blend)
        if self.actor:
            self.actor.setBlend(frameBlend=self.is_blend)
        if hasattr(self, 'head') and self.head:
            self.head.setBlend(frameBlend=self.is_blend)

    def build_cog(self):
        pos = (0, 0, 0)
        hpr = (180, 0, 0)

        self.skele_i = 0
        self.skele_meter_color = 0
        self.flatten_switch = 0
        self.it = 0
        self.it2 = 0
        self.it_l, self.it_m, self.it_r = 0, 0, 0

        self.current_head_animation = "zero"
        self.current_animation = "zero"
        self.is_posed = False

        if not self.actor == None:
            pos = self.actor.getPos()
            hpr = self.actor.getHpr()
            self.actor.cleanup()
            self.actor.removeNode()

        body_path = ""
        body_animations = {}

        head_path = ""
        head_animations = {}

        cog_data = globals.COG_DATA[self.current_cog]
        self.cog_data = cog_data
        suit_type = cog_data["suit"]
        dept = cog_data["dept"]
        body_path = globals.SUIT_MODEL_DICT.get(suit_type, None)

        if body_path is None:
            print(f"Warning: Suit type '{suit_type}' not recognized.")

        if (suit_type in ["a", "af", "hr", "as", "mph", "cch", "erfit"]):
            body_animations = globals.SUIT_A_ANIMATION_DICT
            self.available_animations = globals.SUIT_A_ANIMATIONS
        elif (suit_type in ["b", "bf", "bc", "ps", "rm", "bs"]):
            body_animations = globals.SUIT_B_ANIMATION_DICT
            self.available_animations = globals.SUIT_B_ANIMATIONS
        elif (suit_type in ["c", "cf", "cs"]):
            body_animations = globals.SUIT_C_ANIMATION_DICT
            self.available_animations = globals.SUIT_C_ANIMATIONS
        elif (suit_type in ["bossCog"]):
            body_animations = globals.BOSS_COG_ANIMATION_DICT
            self.available_animations = globals.BOSS_COG_ANIMATIONS

        self.actor = Actor(body_path, body_animations)
        self.shadow.reparentTo(self.actor.find('**/joint_shadow'))

        ##### SET SUIT/NECKTIE TEXTURE ########################################
        tx_suit = loader.loadTexture(cog_data["suitTex"])
        if cog_data["cog"] == ["counterfit"] or cog_data['name'] in ["ttcc_ene_counterfit"]:
            self.actor.find('**/body').setTexture(tx_suit, 1)
        else:
            self.actor.find('**/body').setTexture(tx_suit, 1)
            self.actor.find('**/necktie-s').setTexture(tx_suit, 1)
            self.actor.find('**/necktie-w').setTexture(tx_suit, 1)
            self.actor.find('**/bowtie').setTexture(tx_suit, 1)

        # Fix for Bellringer & Insider, set their hand textures
        if cog_data["suit"] == "bc":
            self.actor.find('**/hands').setTexture(tx_suit, 1)

        if (suit_type == "mph"):
            tx_body = loader.loadTexture(cog_data["bodyTex"])
            self.actor.find('**/bowtie').setTexture(tx_body, 1)
            self.actor.find('**/highroller_body').setTexture(tx_body, 1)

        # Call build_necktie function
        self.build_necktie()

        self.head = loader.loadModel(cog_data["head"])

        # Check to make sure our actor is not a filthy skelecog!!
        if (suit_type not in ["as", "bs", "cs", "bossCog"]):
            self.actor.find('**/hands').setColor(cog_data["hands"])

            medallion = cog_data["emblem"]
            chest_null = self.actor.find("**/joint_attachMeter")
            # icons = loader.loadModel(globals.COG_ICONS)
            self.iconbase = loader.loadModel(globals.COG_ICONS_BASE)
            self.iconbase.reparentTo(chest_null)

            # icons.setPosHprScale(*globals.COG_ICON_HPR)
            chest_null.setH(0)

            self.iconbase.setPosHprScale(*globals.COG_ICON_HPR)

            self.iconbase.find('**/emblem_hp').hide()
            self.iconbase.find('**/glow').hide()
            self.iconbase.find('**/emblem_sales').hide()
            self.iconbase.find('**/emblem_money').hide()
            self.iconbase.find('**/emblem_legal').hide()
            self.iconbase.find('**/emblem_corp').hide()
            self.iconbase.find('**/emblem_board').hide()

            # If our actor is High Roller, hide the emblem
            if suit_type == "hr":
                self.iconbase.hide()

            emblem = cog_data["emblem"]
            self.iconbase.find(f'**/{emblem}').show()

            # self.iconbase = iconbase

            if suit_type in ["a", "af", "cch", "mph"]:
                self.iconbase.setY(-0.10)
            elif suit_type in ["c"]:
                self.iconbase.setY(0.10)
            elif suit_type in ["cf"]:
                self.iconbase.setY(0.02)
                self.iconbase.setZ(0.23)
                self.iconbase.setP(2.5)
            elif suit_type in ["erfit"]:
                self.iconbase.setPosHprScale(0.00, 0.04, 0.00, 180.00, 349.70, 0.00, 1.00, 1.00, 1.00)
            else:
                self.iconbase.setY(0.00)

        # If they are a skelecog:
        else:
            self.health_meter = self.actor.find("**/emblem_healthmeter")
            self.meter_glow = self.actor.find('**/glow')
            self.health_meter
            self.meter_glow

        # Set up head animations

        cog_name = cog_data["name"]
        head_anim_dict, head_anims = globals.HEAD_ANIMATION_PATH(cog_name)
        self.available_head_animations = head_anims

        head_path = cog_data["head"]
        head_animations = head_anim_dict

        if len(head_anims) > 1:
            self.head = Actor(head_path, head_animations)
        else:
            self.head = loader.loadModel(head_path)

        self.head.reparentTo(self.actor.find('**/joint_head'))

        # Head resize for specific cogs
        if "headSize" in cog_data:
            self.head.setScale(cog_data["headSize"])

        if cog_data["name"] in ["ttcc_ene_prethinker"]:
            self.head.find('**/brain').setScale(0.95)

        # Move down treekiller's head
        if "headPos" in cog_data:
            self.head.setZ(cog_data["headPos"])
            if "headPosY" in cog_data:
                self.head.setY(cog_data["headPosY"])
            if "headPosP" in cog_data:
                self.head.setP(cog_data["headPosP"])
            if "headPosH" in cog_data:
                self.head.setH(cog_data["headPosH"])

        # Satellite Investor Colors
        if "bodyColor" in cog_data:
            self.actor.find('**/body').setColor(cog_data["bodyColor"])
            self.head.setColor(cog_data["bodyColor"])

        # Skelecog Head Texture
        if "headTex" in cog_data:
            head_texture = loader.loadTexture(cog_data["headTex"])
            self.head.setTexture(head_texture, 1)

        # Chainsaw and Scapegoat Fix
        if cog_data["name"] in ["ttcc_ene_chainsaw", "ttcc_ene_scapegoat"]:
            self.actor.setTwoSided(True)

        # Conveyancer Belt Fix
        if "belt" in cog_data:
            belt = loader.loadModel(cog_data["belt"])
            belt.reparentTo(self.head)

        self.actor.setScale(cog_data["scale"])

        self.actor.setPos(pos)
        self.actor.setHpr(hpr)

        self.actor.reparentTo(render)
        self.actor.setBlend(frameBlend=self.is_blend)
        if hasattr(self.head, "getAnimNames"):
            self.head.setBlend(frameBlend=self.is_blend)
        # self.actor.find("**/joint_attachMeter").setHpr(*globals.COG_ICON_HPR)

        self.suit_type = suit_type

        self.control_panel.update_animation_lists(
            self.available_animations,
            self.available_head_animations
        )

        # Reset Toggles
        self.control_panel.update_anim_slider_range("body", 0)
        self.control_panel.update_anim_slider_range("head", 0)

        self.control_panel.is_shadow_var.set(True)
        self.is_shadow = True
        self.shadow.show()
        self.is_costume_active = False
        self.control_panel.is_body_var.set(True)
        self.control_panel.is_flattened_var.set(False)
        self.control_panel.is_costume_var.set(False)
        self.control_panel.is_executive_var.set(False)
        self.control_panel.is_fired_var.set(False)
        self.control_panel.is_waiter_var.set(False)
        self.is_body = True

        self.control_panel.reset_head_hpr()

        if self.cog_data.get("hasHalloween") == 1:
            self.control_panel.costume_button.grid()
        else:
            self.control_panel.costume_button.grid_remove()

        suitToggle = self.cog_data.get("suitToggle")
        dept = self.cog_data.get("dept")

        self.control_panel.suit_exec_check.pack_forget()
        self.control_panel.suit_fired_check.pack_forget()
        self.control_panel.suit_waiter_check.pack_forget()
        self.control_panel.unique_suit_button.pack_forget()
        self.control_panel.ds_frame.pack_forget()
        self.control_panel.suit_toggle_button.grid_remove()

        if suitToggle in ["y", "s", "u"]:
            # Show standard toggles
            self.control_panel.suit_exec_check.pack(anchor="w", padx=5)
            self.control_panel.suit_fired_check.pack(anchor="w", padx=5)
            # Show waiter check *only* for Bossbots
            if dept == "c":
                self.control_panel.suit_waiter_check.pack(anchor="w", padx=5)

        if suitToggle in ["hr", "rm", "dj", "u", "cch", "chainsaw"]:
            # Show unique cycle button
            self.control_panel.unique_suit_button.pack(anchor="w", fill="x", padx=5, pady=5)

        elif suitToggle == "ds3":
            # Show Duck Shuffler buttons
            self.control_panel.ds_frame.pack(anchor="w", fill="x", padx=5, pady=5)

        elif suitToggle:
            # Show the old "Toggle Suit Type" button as a fallback
            self.control_panel.suit_toggle_button.grid()

        if self.custom_model and not self.custom_model.isEmpty():
            self.custom_model.removeNode()
            self.custom_model = None
        self.control_panel.show_custom_model_tab(False)

        self.control_panel.selected_tie_var.set("(Default)")

    def build_necktie(self):
        cog_data = self.cog_data
        self.control_panel.hide_tie_list()

        if cog_data["suit"] not in ["erfit"]:  # Make sure it's not Erfit, as his suit doesn't have tie geomnodes
            # We hide the neckties by default, then re-enable them for departments
            self.actor.find('**/necktie-s').hide()  # Hide Sellbot necktie
            self.actor.find('**/necktie-w').hide()  # Hide Cash/Boss/Board necktie
            self.actor.find('**/bowtie').hide()  # Hide Law bowtie

            # Tieless Cogs
            if cog_data["cog"] not in globals.NO_NECKTIE_COGS:
                if self.control_panel.tie_options_hidden_var:
                    self.control_panel.show_tie_list()
                necktie_map = globals.NECKTIE_MAP
                necktie = necktie_map.get(cog_data["cog"]) or necktie_map.get(
                    cog_data["dept"])  # Search by cog name or department
                self.actor.find(necktie).show()  # Find the appropriate necktie and unhide it

    def set_suit_texture(self, trigger=None):
        """Applies Executive, Fired, or Waiter textures."""
        if not self.cog_data: return

        is_exec = self.control_panel.is_executive_var.get()
        is_fired = self.control_panel.is_fired_var.get()
        is_waiter = self.control_panel.is_waiter_var.get()

        if trigger == "fired" and is_fired:
            self.control_panel.is_executive_var.set(False)
            self.control_panel.is_waiter_var.set(False)
            is_exec = False
            is_waiter = False

        elif trigger == "exec" and is_exec:
            self.control_panel.is_fired_var.set(False)
            is_fired = False

        elif trigger == "waiter" and is_waiter:
            self.control_panel.is_fired_var.set(False)
            is_fired = False

        cog_name = self.cog_data["name"]
        dept = self.cog_data["dept"]
        suitToggle = self.cog_data.get("suitToggle")

        paths = globals.SUIT_TEXTURE_PATH

        tex_key = dept
        if suitToggle == "s":
            tex_key = dept + "s"
        elif cog_name in paths:
            tex_key = cog_name

        tex_list = paths.get(tex_key)
        if not tex_list: return

        tex_to_apply = tex_list[0]  # Default

        if is_fired:
            tex_to_apply = tex_list[-1]

        elif is_waiter and tex_key in ["c", "cs"] and len(tex_list) > 3:
            if is_exec:
                tex_to_apply = tex_list[3]  # Waiter Executive
            else:
                tex_to_apply = tex_list[2]  # Waiter (Normal)

        elif is_exec and len(tex_list) > 1:
            tex_to_apply = tex_list[1]  # Standard Executive

        # Apply the texture
        tx_suit = loader.loadTexture(tex_to_apply)
        self.actor.find('**/body').setTexture(tx_suit, 1)
        self.actor.find('**/necktie-s').setTexture(tx_suit, 1)
        self.actor.find('**/necktie-w').setTexture(tx_suit, 1)
        self.actor.find('**/bowtie').setTexture(tx_suit, 1)

        if suitToggle == "s":
            self.head.setTexture(tx_suit, 1)  # Skelecogs

        elif cog_name in ["cc_a_ene_bagholder", "cc_a_ene_insider", "cc_a_ene_headhoncho"]:  # stupid boardbots
            head_tex_list = globals.HEAD_TEXTURE_PATH.get(tex_key)
            if head_tex_list:
                head_tex = head_tex_list[0]
                if is_fired:
                    head_tex = head_tex_list[-1]
                elif is_exec:
                    head_tex = head_tex_list[1]
                self.head.setTexture(loader.loadTexture(head_tex), 1)

    def toggle_unique_suit(self):
        """Handles the 'cycle' button for unique suit toggles."""
        if not self.cog_data: return

        cog_name = self.cog_data["name"]
        suitToggle = self.cog_data.get("suitToggle")

        if suitToggle == "u":
            suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_name)
            head_paths = globals.HEAD_TEXTURE_PATH.get(cog_name)
            self.it = (self.it + 1) % len(suit_paths)
            tx_suit = loader.loadTexture(suit_paths[self.it])
            tx_head = loader.loadTexture(head_paths[self.it])
            self.actor.find('**/body').setTexture(tx_suit, 1)
            self.actor.find('**/necktie-w').setTexture(tx_suit, 1)
            self.head.setTexture(tx_head, 1)
            if cog_name in ["ttcc_ene_chainsaw", "ttcc_ene_chainsaw_hw"]:
                if self.it > 1:
                    self.head.find('**/bulbLeft').hide()
                else:
                    self.head.find('**/bulbLeft').show()

        elif suitToggle == "chainsaw":
            suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_name)
            head_paths = globals.HEAD_TEXTURE_PATH.get(cog_name)
            self.it = (self.it + 1) % len(suit_paths)
            tx_suit = loader.loadTexture(suit_paths[self.it])
            tx_head = loader.loadTexture(head_paths[self.it])
            self.actor.find('**/body').setTexture(tx_suit, 1)
            self.actor.find('**/necktie-w').setTexture(tx_suit, 1)
            self.head.setTexture(tx_head, 1)
            if self.it > 1:
                self.head.find('**/bulbLeft').hide()
            else:
                self.head.find('**/bulbLeft').show()

        elif suitToggle == "cch":
            suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_name)
            head_paths = globals.HEAD_TEXTURE_PATH.get(cog_name)
            self.it = (self.it + 1) % len(suit_paths)
            tx_head = loader.loadTexture(head_paths[self.it])
            self.head.setTexture(tx_head, 1)
            if self.it > 1:
                self.head.find('**/bulbLeft').hide()
            else:
                self.head.find('**/bulbLeft').show()

        elif suitToggle == "hr":
            suit_paths = globals.SUIT_TEXTURE_PATH.get("hr")
            body_paths = globals.HEAD_TEXTURE_PATH.get("hr")
            self.it = (self.it + 1) % len(suit_paths)
            tx_suit = loader.loadTexture(suit_paths[self.it])
            tx_body = loader.loadTexture(body_paths[self.it])
            self.actor.find('**/body').setTexture(tx_suit, 1)
            self.actor.find('**/highroller_body').setTexture(tx_body, 1)

        elif suitToggle == "rm":
            for Hair in self.head.findAllTextureStages("*hair"):
                self.it2 += 0.2
                if self.it2 == 1: self.it2 = 0
                self.head.setTexOffset(Hair, 0, self.it2)

        elif suitToggle == "dj":
            suit_paths = globals.SUIT_TEXTURE_PATH.get("dj")
            self.it = (self.it + 1) % len(suit_paths)
            tx_suit = loader.loadTexture(suit_paths[self.it])
            self.actor.find('**/body').setTexture(tx_suit, 1)
            self.actor.find('**/bowtie').setTexture(tx_suit, 1)

    def cycle_slot_l(self):
        if not self.head or self.head.isEmpty(): return
        slotL = self.head.find('**/slotL')
        if not slotL.isEmpty():
            self.it_l = (self.it_l + 0.25) % 1.0
            slotL.setTexOffset(TextureStage.getDefault(), 0, self.it_l)

    def cycle_slot_m(self):
        if not self.head or self.head.isEmpty(): return
        slotM = self.head.find('**/slotMid')
        if not slotM.isEmpty():
            self.it_m = (self.it_m + 0.25) % 1.0
            slotM.setTexOffset(TextureStage.getDefault(), 0, self.it_m)

    def cycle_slot_r(self):
        if not self.head or self.head.isEmpty(): return
        slotR = self.head.find('**/slotR')
        if not slotR.isEmpty():
            self.it_r = (self.it_r + 0.25) % 1.0
            slotR.setTexOffset(TextureStage.getDefault(), 0, self.it_r)

    def set_necktie(self, override=None):
        cog_data = self.cog_data

        self.actor.find('**/necktie-s').hide()
        self.actor.find('**/necktie-w').hide()
        self.actor.find('**/bowtie').hide()

        if cog_data["cog"] in globals.NO_NECKTIE_COGS:
            return

        tie_to_show = None
        if override and override != "(Default)":
            if override == "Skinny Tie":
                tie_to_show = "**/necktie-s"
            elif override == "Wide Tie":
                tie_to_show = "**/necktie-w"
            elif override == "Bowtie":
                tie_to_show = "**/bowtie"
            elif override == "None":
                return
        else:
            necktie_map = globals.NECKTIE_MAP
            tie_to_show = necktie_map.get(cog_data["cog"]) or necktie_map.get(cog_data["dept"])

        if tie_to_show:
            self.actor.find(tie_to_show).show()

    def _swap_head_model(self, new_model_path):
        if not new_model_path or not os.path.isfile(new_model_path):
            return None
        new_head = None

        anim_dict = {}
        if isinstance(self.head, Actor):
            if hasattr(self.head, "_anim_dict"):
                anim_dict = self.head._anim_dict
            elif hasattr(self.head, "getAnimNames"):
                anim_names = self.head.getAnimNames()
                for anim in anim_names:
                    anim_dict[anim] = self.head.getAnimFilename(anim)
            else:
                anim_dict = getattr(globals, "HEAD_ANIM_DICT", {}).get(self.current_cog, {})

        try:
            if anim_dict:
                new_head = Actor(new_model_path, anim_dict)
            else:
                new_head = loader.loadModel(new_model_path)
        except Exception as e:
            new_head = loader.loadModel(new_model_path)

        joint = self.actor.find('**/joint_head')
        if not joint.isEmpty():
            new_head.reparentTo(joint)
        else:
            new_head.reparentTo(self.actor)

        if hasattr(self, "head") and not self.head.isEmpty():
            new_head.setPos(self.head.getPos())
            new_head.setHpr(self.head.getHpr())
            new_head.setScale(self.head.getScale())

        return new_head

    def toggle_costume(self):  # Toggle halloween costumes for managers
        cog_data = globals.COG_DATA.get(self.current_cog, None)
        if not cog_data: return

        if not hasattr(self, "is_costume_active"):
            self.is_costume_active = False

        cog_name = cog_data["name"]
        suit_type = cog_data.get("suit", "a")

        def get_valid_texture_path(tex_value):
            if not tex_value:
                return None
            if isinstance(tex_value, (list, tuple)):
                tex_value = tex_value[0]
            if isinstance(tex_value, (str, bytes, os.PathLike)) and os.path.isfile(tex_value):
                return tex_value
            return None

        hw_head_model_path = cog_data.get("headModel_HW")

        # Toggle ON
        if not self.is_costume_active:

            if hw_head_model_path and os.path.isfile(hw_head_model_path):
                self.head.detachNode()
                self.head = self._swap_head_model(hw_head_model_path)

            head_tex_path = get_valid_texture_path(cog_data.get("headTex_HW"))
            if head_tex_path:
                hw_head_tex = loader.loadTexture(head_tex_path)
                if "ttcc_ene_rainmaker" in cog_name:
                    rainHW = loader.loadTexture(cog_data.get("headTex_HW"))
                    rainHair = loader.loadTexture(cog_data.get("hairTex_HW"))

                    geomNode = self.head.find("**/head").node()

                    state0 = geomNode.getGeomState(0)
                    tex_attr0 = state0.getAttrib(TextureAttrib)
                    if tex_attr0:
                        for stage in tex_attr0.getOnStages():
                            if stage.getName() == "ttcc_ene_rainmaker_hair":
                                new_state = state0.setAttrib(tex_attr0.addOnStage(stage, rainHair))
                                geomNode.setGeomState(0, new_state)
                    state1 = geomNode.getGeomState(1)
                    tex_attr1 = state1.getAttrib(TextureAttrib)
                    if tex_attr1:
                        for stage in tex_attr1.getOnStages():
                            if stage.getName() == "rainmaker":
                                new_state = state1.setAttrib(tex_attr1.addOnStage(stage, rainHW))
                                geomNode.setGeomState(1, new_state)

                else:
                    self.head.setTexture(hw_head_tex, 1)

                if "ttcc_ene_duckshuffler" in cog_name:
                    slot_tex = loader.loadTexture(cog_data["slotTex"])
                    for part in ['slotL', 'slotMid', 'slotR']:
                        np = self.head.find(f'**/{part}')
                        if not np.isEmpty():
                            np.setTexture(slot_tex, 1)
                elif suit_type == "mph":
                    self.head.find('**/he_teeths').hide()
                elif "ttcc_ene_prethinker" in cog_name:
                    glass = loader.loadTexture(cog_data["glassTex"])
                    self.head.find('**/brain').setTexture(hw_head_tex, 1)
                    self.head.find('**/glass').setTexture(glass, 1)
                    self.head.find('**/head').setTexture(hw_head_tex, 1)

            suit_tex_path = get_valid_texture_path(cog_data.get("suitTex_HW"))
            if suit_tex_path:
                hw_suit_tex = loader.loadTexture(suit_tex_path)
                if (suit_type == "mph"):
                    tx_body = loader.loadTexture(cog_data["bodyTex_HW"])
                    self.actor.find('**/bowtie').setTexture(tx_body, 1)
                    self.actor.find('**/highroller_body').setTexture(tx_body, 1)
                    self.actor.find('**/body').setTexture(hw_suit_tex, 1)

                else:
                    for part in ['body', 'necktie-s', 'necktie-w', 'bowtie']:
                        np = self.actor.find(f'**/{part}')
                        if not np.isEmpty():
                            np.setTexture(hw_suit_tex, 1)

            if (suit_type not in ["as", "bs", "cs", "bossCog"]):
                if "handsHW" in cog_data:
                    self.actor.find('**/hands').setColor(cog_data["handsHW"])

            self.is_costume_active = True

        # Toggle OFF
        else:
            if hw_head_model_path and os.path.isfile(hw_head_model_path):
                self.head.detachNode()
                self.head = self._swap_head_model(cog_data.get("head"))

            if "ttcc_ene_rainmaker" in cog_name:
                rainHW = loader.loadTexture(cog_data.get("headTex1"))
                rainHair = loader.loadTexture(cog_data.get("hairTex"))

                geomNode = self.head.find("**/head").node()

                state0 = geomNode.getGeomState(0)
                tex_attr0 = state0.getAttrib(TextureAttrib)
                if tex_attr0:
                    for stage in tex_attr0.getOnStages():
                        if stage.getName() == "ttcc_ene_rainmaker_hair":
                            new_state = state0.setAttrib(tex_attr0.addOnStage(stage, rainHair))
                            geomNode.setGeomState(0, new_state)
                state1 = geomNode.getGeomState(1)
                tex_attr1 = state1.getAttrib(TextureAttrib)
                if tex_attr1:
                    for stage in tex_attr1.getOnStages():
                        if stage.getName() == "rainmaker":
                            new_state = state1.setAttrib(tex_attr1.addOnStage(stage, rainHW))
                            geomNode.setGeomState(1, new_state)
            else:
                self.head.clearTexture()

            if "ttcc_ene_duckshuffler" in cog_name:
                slot_tex = loader.loadTexture(cog_data["slotTex"])
                for part in ['slotL', 'slotMid', 'slotR']:
                    np = self.head.find(f'**/{part}')
                    if not np.isEmpty():
                        np.clearTexture()
            elif suit_type == "mph":
                self.head.find('**/he_teeths').show()
            elif "ttcc_ene_prethinker" in cog_name:
                self.head.find('**/brain').clearTexture()
                self.head.find('**/glass').clearTexture()
                self.head.find('**/head').clearTexture()

            suit_tex_path = get_valid_texture_path(cog_data.get("suitTex"))
            if suit_tex_path:
                normal_suit_tex = loader.loadTexture(suit_tex_path)
                if (suit_type == "mph"):
                    tx_body_normal = loader.loadTexture(cog_data["bodyTex"])
                    self.actor.find('**/bowtie').setTexture(tx_body_normal, 1)
                    self.actor.find('**/highroller_body').setTexture(tx_body_normal, 1)
                    self.actor.find('**/body').setTexture(normal_suit_tex, 1)
                else:
                    for part in ['body', 'necktie-s', 'necktie-w', 'bowtie']:
                        np = self.actor.find(f'**/{part}')
                        if not np.isEmpty():
                            np.setTexture(normal_suit_tex, 1)

            if (suit_type not in ["as", "bs", "cs", "bossCog"]):
                if "hands" in cog_data:
                    self.actor.find('**/hands').setColor(cog_data["hands"])

            self.is_costume_active = False

    def toggle_body(self):  # Used to toggle the cog's body on or off (head renders)
        hands = self.actor.find(
            '**/hands')  # Used to check if the actor has hand geomnodes, cause Skelecogs don't got those
        hr_body = self.actor.find('**/highroller_body')  # Used to hide Halloween Dave's inner suit thingy

        # HIDE BODY
        if self.is_body:
            self.actor.find('**/body').hide()  # Hiding body & all suit parts
            self.actor.find("**/joint_attachMeter").hide()
            if self.cog_data["cog"] not in [
                "counterfit"]:  # Make sure the cog isn't Count Erfit (he lacks necktie geomnodes)
                self.actor.find('**/necktie-s').hide()
                self.actor.find('**/necktie-w').hide()
                self.actor.find('**/bowtie').hide()
            # Hide shadow
            self.shadow.hide()
            self.control_panel.is_shadow_var.set(False)
            self.is_shadow = False  # Also tell the tkpanel to uncheck the shadow
            if not hands.is_empty():  # If hand geomnodes exist, hide them (not a skelecog)
                hands.hide()
                if not hr_body.is_empty():  # If this is Halloween Dave Brubot, hide his inner suit
                    hr_body.hide()
            else:  # Hide Body (Skelecog)
                self.actor.find("**/emblem_healthmeter").hide()  # Hides the skelecog light hp
                self.actor.find('**/glow').hide()  # Hides the hp light glow
            self.is_body = False  # Flip bool var to true for show body

        # SHOW BODY
        else:
            self.actor.find('**/body').show()  # Show the body
            self.actor.find("**/joint_attachMeter").show()
            # Show shadow
            self.shadow.show()
            self.control_panel.is_shadow_var.set(True)
            self.is_shadow = True  # Also tell the tkpanel to re-check the shadow
            if not hands.is_empty():  # If hand geomnodes exist, show them (not a skelecog)
                hands.show()
                if not hr_body.is_empty():  # It's halloween dave brubot again show his inner suit
                    hr_body.show()
            else:  # Show Body (Skelecog)
                self.actor.find("**/emblem_healthmeter").show()  # Shows the skelecog hp light
                self.actor.find('**/glow').show()  # Shows the glow
            self.set_necktie(override=None)  # Set default tie
            self.is_body = True  # Flip bool var to false for hide body
            self.control_panel.selected_tie_var.set("(Default)")

        self.control_panel.is_body_var.set(self.is_body)  # Update the tkpanel status
        self.control_panel.is_background_black_var.set(self.bool)
        self.control_panel.is_executive_var.set(False)
        self.control_panel.is_fired_var.set(False)

        if self.prop_item1_actor: self.prop_item1_actor.cleanup()
        if self.prop_item2_actor: self.prop_item2_actor.cleanup()
        if self.prop_item1 != "zero": self.prop_item1.removeNode()
        if self.prop_item2 != "zero": self.prop_item2.removeNode()
        self.prop_item1_actor = None
        self.prop_item2_actor = None
        self.prop_item1 = "zero"
        self.prop_item2 = "zero"
        self.current_prop1 = "zero"
        self.current_prop2 = "zero"
        self.control_panel.hide_prop_anim_ui(self.control_panel.prop1_anim_frame)
        self.control_panel.hide_prop_anim_ui(self.control_panel.prop2_anim_frame)

    def toggle_shadow(self):
        self.is_shadow = not self.is_shadow
        self.control_panel.is_shadow_var.set(self.is_shadow)
        if self.is_shadow:
            self.shadow.show()
        else:
            self.shadow.hide()

    def autoplay_animations(self):
        self.is_autoplay = self.control_panel.is_autoplay_var.get()

    def toggle_virtualize(self):
        if not hasattr(self, 'skele_color_index'):
            self.skele_color_index = 0

        self.skele_color_index = (self.skele_color_index + 1) % len(globals.SKELECOG_METER_COLORS)

        if self.skele_color_index == 0:
            self.actor.clearColorScale()
            self.actor.clearAttrib(ColorBlendAttrib.getClassType())
            self.actor.setDepthWrite(True)
            self.actor.setBin('default', 0)
        else:
            new_color = globals.SKELECOG_METER_COLORS[self.skele_color_index]
            self.actor.setColorScale(new_color)
            self.actor.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))
            self.actor.setDepthWrite(False)
            self.actor.setBin('fixed', 1)

    def toggle_flatten(self):
        is_flat = self.control_panel.is_flattened_var.get()
        if is_flat:
            self.actor.setSy(0.01)
        else:
            self.actor.setSy(1 * self.cog_data.get("scale", 1.0))
        self.flatten_switch = 1 if is_flat else 0

    def on_tie_select(self, event=None):
        selection = self.control_panel.tie_listbox.curselection()
        if selection:
            selected_tie = self.control_panel.tie_listbox.get(selection[0])
            self.set_necktie(selected_tie)

    def toggle_skele_meter_color(self):
        emblem_hp = self.iconbase.find('**/emblem_hp')
        glow = self.iconbase.find('**/glow')
        self.skele_meter_color = globals.SKELECOG_METER_COLORS[self.skele_i]
        if (self.suit_type in ["as", "bs", "cs"]):
            self.health_meter.setColor(self.skele_meter_color)
            self.meter_glow.setColor(self.skele_meter_color)
        elif self.skele_i < 6:
            emblem_hp.show()
            glow.show()
            emblem_hp.setColor(self.skele_meter_color)
            glow.setColor(self.skele_meter_color)
        elif self.skele_i == 6:
            emblem_hp.hide()
            glow.hide()
        self.skele_i += 1
        self.skele_i %= 7

    def toggle_suit(self):
        cog_data = globals.COG_DATA[self.current_cog]
        dept = cog_data["dept"]
        suitToggle = cog_data["suitToggle"]
        if "suitToggle" in cog_data:
            if suitToggle == "y":
                suit_paths = globals.SUIT_TEXTURE_PATH.get(dept)
                # Cycle through available suit textures for the department
                self.it = (self.it + 1) % len(suit_paths)
                tx_suit = loader.loadTexture(suit_paths[self.it])
                self.actor.find('**/body').setTexture(tx_suit, 1)
                self.actor.find('**/necktie-s').setTexture(tx_suit, 1)
                self.actor.find('**/necktie-w').setTexture(tx_suit, 1)
                self.actor.find('**/bowtie').setTexture(tx_suit, 1)
                if dept == "c" and self.it == 2 or self.it == 3:  # Toggle tie model for bossbot waiters
                    self.actor.find('**/necktie-w').hide()
                    self.actor.find('**/bowtie').show()
                elif dept == "c" and self.it < 2 or self.it > 3:
                    self.actor.find('**/necktie-w').show()
                    self.actor.find('**/bowtie').hide()
            elif suitToggle == "s":  # Skelecogs
                dept = dept + "s"
                suit_paths = globals.SUIT_TEXTURE_PATH.get(dept)
                self.it = (self.it + 1) % len(suit_paths)
                tx_suit = loader.loadTexture(suit_paths[self.it])
                self.actor.find('**/body').setTexture(tx_suit, 1)
                self.actor.find('**/necktie-s').setTexture(tx_suit, 1)
                self.actor.find('**/necktie-w').setTexture(tx_suit, 1)
                self.actor.find('**/bowtie').setTexture(tx_suit, 1)
                self.head.setTexture(tx_suit, 1)
                if dept == "cs" and self.it == 2:  # Toggle tie model for skelecog waiters
                    self.actor.find('**/necktie-w').hide()
                    self.actor.find('**/bowtie').show()
                elif dept == "c" and self.it < 2 or self.it > 2:
                    self.actor.find('**/necktie-w').show()
                    self.actor.find('**/bowtie').hide()
            elif suitToggle == "u":  # Cogs with unique head/body textures
                suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_data["name"])
                head_paths = globals.HEAD_TEXTURE_PATH.get(cog_data["name"])
                self.it = (self.it + 1) % len(suit_paths)
                tx_suit = loader.loadTexture(suit_paths[self.it])
                tx_head = loader.loadTexture(head_paths[self.it])
                self.actor.find('**/body').setTexture(tx_suit, 1)
                self.actor.find('**/necktie-w').setTexture(tx_suit, 1)
                self.head.setTexture(tx_head, 1)
                if cog_data["cog"] in ["chainsawconsultant"]:
                    if self.it > 1:
                        self.head.find('**/bulbLeft').hide()
                    else:
                        self.head.find('**/bulbLeft').show()

            elif suitToggle == "cch":
                suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_name)
                head_paths = globals.HEAD_TEXTURE_PATH.get(cog_name)
                self.it = (self.it + 1) % len(suit_paths)
                tx_head = loader.loadTexture(head_paths[self.it])
                self.head.setTexture(tx_head, 1)
                if self.it > 1:
                    self.head.find('**/bulbLeft').hide()
                else:
                    self.head.find('**/bulbLeft').show()

            elif suitToggle == "hr":  # High roller
                suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_data["suitToggle"])
                body_paths = globals.HEAD_TEXTURE_PATH.get(cog_data["suitToggle"])
                self.it = (self.it + 1) % len(suit_paths)
                tx_suit = loader.loadTexture(suit_paths[self.it])
                tx_body = loader.loadTexture(body_paths[self.it])
                self.actor.find('**/body').setTexture(tx_suit, 1)
                self.actor.find('**/highroller_body').setTexture(tx_body, 1)
            elif suitToggle == "rm":  # Rainmaker
                for Hair in self.head.findAllTextureStages("*hair"):
                    self.it2 += 0.2
                    if self.it2 == 1:
                        self.it2 = 0
                    self.head.setTexOffset(Hair, 0, self.it2)
            elif suitToggle == "ds":
                slotL = self.head.find('**/slotL')
                slotM = self.head.find('**/slotMid')
                slotR = self.head.find('**/slotR')
                self.it += 0.25
                if self.it == 1:
                    self.it = 0
                slotL.setTexOffset(TextureStage.getDefault(), 0, self.it)
                slotM.setTexOffset(TextureStage.getDefault(), 0, self.it)
                slotR.setTexOffset(TextureStage.getDefault(), 0, self.it)
            elif suitToggle == "dj":  # Desk Jockey
                suit_paths = globals.SUIT_TEXTURE_PATH.get("dj")
                self.it = (self.it + 1) % len(suit_paths)
                tx_suit = loader.loadTexture(suit_paths[self.it])
                self.actor.find('**/body').setTexture(tx_suit, 1)
                self.actor.find('**/bowtie').setTexture(tx_suit, 1)

    def upload_suit_texture(self):
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(
            title="Select Suit Texture",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.bmp *.tga"),
                ("All Files", "*.*")
            ]
        )

        if not file_path:
            print("Texture upload canceled.")
            return

        try:
            panda_path = Filename.fromOsSpecific(file_path)
            panda_path.makeTrueCase()

            new_tex = loader.loadTexture(panda_path)
            if not new_tex:
                print("Error: Failed to load texture.")
                return

            self.actor.find('**/body').setTexture(new_tex, 1)
            self.actor.find('**/necktie-s').setTexture(new_tex, 1)
            self.actor.find('**/necktie-w').setTexture(new_tex, 1)
            self.actor.find('**/bowtie').setTexture(new_tex, 1)

            print(f"Applied new suit texture: {file_path}")

        except Exception as e:
            print(f"Failed to apply texture: {e}")

    def update_custom_model_hpr(self, axis, value):
        """Callback for the custom model's HPR/XYZ/Scale sliders."""
        if self.custom_model and not self.custom_model.isEmpty():
            if axis == "x":
                self.custom_model.setX(value)
            elif axis == "y":
                self.custom_model.setY(value)
            elif axis == "z":
                self.custom_model.setZ(value)
            elif axis == "h":
                self.custom_model.setH(value)
            elif axis == "p":
                self.custom_model.setP(value)
            elif axis == "r":
                self.custom_model.setR(value)
            elif axis == "scale":
                self.custom_model.setScale(value)

    def upload_custom_model(self):
        """Opens a dialog to load a custom .bam file."""
        if not self.actor or self.actor.isEmpty():
            print("Please load a Cog before adding a custom model.")
            return

        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Select Custom .bam Model",
            filetypes=[("Panda3D Models", "*.bam"), ("All Files", "*.*")]
        )
        if not file_path:
            print("Custom model upload canceled.")
            return

        try:
            panda_path = Filename.fromOsSpecific(file_path)
            panda_path.makeTrueCase()

            if self.custom_model and not self.custom_model.isEmpty():
                self.custom_model.removeNode()
                self.custom_model = None

            self.custom_model = loader.loadModel(panda_path)
            if not self.custom_model:
                print(f"Error: Failed to load model {panda_path}")
                return

            head_joint = self.actor.find('**/joint_head')
            if not head_joint.isEmpty():
                self.custom_model.reparentTo(head_joint)
            else:
                self.custom_model.reparentTo(self.actor)  # Fallback

            self.control_panel.show_custom_model_tab(True)
            self.control_panel.reset_prop_sliders(self.control_panel.custom_model_vars)

            print(f"Loaded custom model: {file_path}")

        except Exception as e:
            print(f"Failed to load custom model: {e}")

    def update_frame(self, task):
        if not self.actor or self.current_animation == "zero":
            print("Cannot take screenshot frames: No actor or animation selected.")
            if self.bool:
                self.setBackgroundColor(0, 0, 0)
            else:
                self.setBackgroundColor(105 / 255, 105 / 255, 105 / 255)
            return task.done

        total_frames = self.actor.getNumFrames(self.current_animation)

        has_head_anim = False
        total_head_frames = 0
        if hasattr(self, 'head') and self.head and self.current_head_animation != "zero":
            try:
                total_head_frames = self.head.getNumFrames(self.current_head_animation)
                has_head_anim = True
            except:
                has_head_anim = False

        if self.frame_index < total_frames:
            self.actor.stop()
            if has_head_anim and hasattr(self.head, 'stop'):
                self.head.stop()

            self.actor.pose(self.current_animation, self.frame_index)

            if has_head_anim:
                head_frame = 0
                if total_head_frames > 0:
                    head_frame = self.frame_index % total_head_frames
                self.head.pose(self.current_head_animation, head_frame)

            self.graphicsEngine.renderFrame()
            screenshot_name = os.path.join(self.screenshot_path, f"{self.frame_index:03d}.png")
            self.screenshot(screenshot_name, False)
            self.frame_index += 1

            return task.cont
        else:
            print(f"Finished taking {total_frames} screenshots.")
            if self.bool:
                self.setBackgroundColor(0, 0, 0)
            else:
                self.setBackgroundColor(105 / 255, 105 / 255, 105 / 255)

            self.play_body_animation()
            if has_head_anim:
                self.play_head_animation()

            return task.done

    def start_screenshots(self, task):
        self.frame_index = 0
        self.setBackgroundColor(0, 0, 0)

        if self.actor:
            self.actor.stop()
        if hasattr(self, 'head') and self.head and hasattr(self.head, 'stop'):
            self.head.stop()

        self.taskMgr.add(self.update_frame, "TakeScreenshotsTask")
        return task.done

    def take_screenshot_frames(self):
        if not os.path.exists(self.screenshot_path):
            os.makedirs(self.screenshot_path)
        self.taskMgr.doMethodLater(1 / 24, self.start_screenshots, "StartScreenshotsTask")

    def update_body_pose(self, frame_value):
        if self.current_animation != "zero" and self.actor:
            frame = int(round(float(frame_value)))
            self.actor.pose(self.current_animation, frame)

    def update_head_pose(self, frame_value):
        if self.current_head_animation != "zero" and self.head:
            frame = int(round(float(frame_value)))
            self.head.pose(self.current_head_animation, frame)


app = CogViewer()
app.render.setAntialias(AntialiasAttrib.MMultisample)
app.run()
