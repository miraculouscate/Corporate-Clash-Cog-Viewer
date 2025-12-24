import os
import tkinter as tk
from tkinter import ttk, filedialog, PhotoImage
from datetime import datetime
import random
from panda3d.core import (AntialiasAttrib, Loader, TextNode, Mat4,
                          Filename, Texture, loadPrcFile, ClockObject,
                          ColorBlendAttrib, loadPrcFileData)
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.task import Task
from direct.interval.IntervalGlobal import Func
from panda3d.core import TextureAttrib, TextureStage
import glob
import globals
from tkinter.colorchooser import askcolor

# i view da cog
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
        self.suit_library_frame = None
        self.head_hpr_frame = None

        # State Variables for Checkbuttons
        self.is_shadow_var = tk.BooleanVar(value=self.app.is_shadow)
        self.is_blend_var = tk.BooleanVar(value=self.app.is_blend)
        self.is_body_var = tk.BooleanVar(value=False)
        self.is_autoplay_var = tk.BooleanVar(value=self.app.is_autoplay)
        self.is_background_black_var = tk.BooleanVar(value=self.app.bool)
        self.is_costume_var = tk.BooleanVar(value=False)
        self.loop_body_var = tk.BooleanVar(value=True)
        self.loop_head_var = tk.BooleanVar(value=True)
        self.selected_cog_var = tk.StringVar(value=self.app.current_cog)
        self.TIE_OPTIONS = ["(Default)", "Thin Tie", "Wide Tie", "Bowtie", "None"]
        self.tie_options_hidden_var = False

        self.head_hpr_vars = {}
        self.flatten_body_vars = {}
        self.flatten_head_vars = {}
        self.prop1_vars = {}
        self.prop2_vars = {}
        self.custom_model_vars = {}
        self.custom_model_tab_frame = None
        self.prop_notebook = None
        self.bottom_notebook = None
        self.selected_tie_var = tk.StringVar(value="(Default)")

        self.prop1_anim_frame = None
        self.prop2_anim_frame = None
        self.prop1_anim_listbox = None
        self.prop2_anim_listbox = None
        self.prop1_anim_slider = None
        self.prop2_anim_slider = None
        self.prop1_loop_var = tk.BooleanVar(value=True)
        self.prop2_loop_var = tk.BooleanVar(value=True)

        self.master.title("Corporate Clash Cog Viewer")
        self.master.geometry("700x900")

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
        bottom_notebook.add(toggles_frame, text='Main')
        self._create_toggles(toggles_frame)

        # Animation Tab
        anim_sliders_frame = ttk.Frame(bottom_notebook, padding=10)
        bottom_notebook.add(anim_sliders_frame, text='Animation')
        self._create_anim_sliders(anim_sliders_frame)

        # Suit Library Tab
        self.suit_library_frame = ttk.Frame(bottom_notebook, padding=10)
        bottom_notebook.add(self.suit_library_frame, text='Suit Library')
        self._create_suit_library(self.suit_library_frame)

        # Head HPR Tab
        self.head_hpr_frame = ttk.Frame(bottom_notebook, padding=10)
        bottom_notebook.add(self.head_hpr_frame, text='Head HPR')
        self._create_head_hpr_sliders(self.head_hpr_frame)

        # Flatten Tab
        self.flatten_frame = ttk.Frame(bottom_notebook, padding=10)
        bottom_notebook.add(self.flatten_frame, text='Set Scale')
        self._create_flatten_sliders(self.flatten_frame)

        self.color_tab_frame = ttk.Frame(self.bottom_notebook, padding=10)
        self.bottom_notebook.add(self.color_tab_frame, text='Set Color')
        self._create_color_controls(self.color_tab_frame)

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

        # Autoplay Animation Toggle
        ttk.Checkbutton(frame, text="Autoplay Animations", variable=self.is_autoplay_var,
                        command=self.app.autoplay_animations).grid(row=0, column=0, sticky="w", pady=2)
        # Cog Shadow Toggle
        ttk.Checkbutton(frame, text="Toggle Shadow", variable=self.is_shadow_var,
                        command=self.app.toggle_shadow).grid(row=1, column=0, sticky="w", pady=2)
        # Cog Body Toggle
        self.body_toggle_btn = ttk.Checkbutton(frame, text="Toggle Body", variable=self.is_body_var,
                                               command=self.app.toggle_body)
        self.body_toggle_btn.grid(row=2, column=0, sticky="w", pady=2)

        # Background Color Toggle
        # ttk.Checkbutton(frame, text="Black Background", variable=self.is_background_black_var,
        # command=self.app.toggle_background).grid(row=3, column=0, sticky="w", pady=2)

        # Manager Costume Toggle
        self.costume_button = ttk.Checkbutton(frame, text="Toggle Costume", variable=self.is_costume_var,
                                              command=self.app.toggle_costume)
        self.costume_button.grid(row=3, column=0, sticky="w", pady=2)
        self.costume_button.grid_remove()

        # self.tie_frame = self._create_radio_list(frame, "Necktie Toggles", self.TIE_OPTIONS, self.selected_tie_var,
        #                                          self.on_tie_select_radio)
        # self.tie_frame.grid(row=0, column=2, rowspan=5, sticky="nsew", padx=5, pady=2)

        suit_frame = ttk.Labelframe(frame, text="Suit Toggles")
        suit_frame.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=5, pady=2)

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

        ttk.Button(frame, text="Upload Head Texture",
                   command=self.app.upload_head_texture).grid(row=5, column=0, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Add Pie Splat",
                   command=self.app.add_pie_splat).grid(row=6, column=0, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Clear Pie Splats",
                   command=self.app.clear_pie_splats).grid(row=7, column=0, sticky="ew", padx=5, pady=2)

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
        ttk.Button(frame, text="Upload Accessory",
                   command=self.app.upload_custom_model).grid(row=4, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Upload Suit Texture",
                   command=self.app.upload_suit_texture).grid(row=5, column=1, sticky="ew", padx=5, pady=2)
        ttk.Button(frame, text="Upload Head Part Texture",
                   command=self.app.upload_additional_head_texture).grid(row=5, column=2, sticky="ew", padx=5, pady=2)
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

    def _create_flatten_sliders(self, master):
        default_body = self.app.cog_data.get("scale", 1.0)
        flatten_slider_body_defs = [
            ("Profile (Sx)", "Sx", 0.01, 15, default_body),
            ("Portrait (Sy)", "Sy", 0.01, 15, default_body),
            ("Height (Sz)", "Sz", 0.01, 15, default_body),
        ]
        default_head = self.app.cog_data.get("headSize", 1.0)
        flatten_slider_head_defs = [
            ("Profile (Sx)", "Sx", 0.01, 15, default_head),
            ("Portrait (Sy)", "Sy", 0.01, 15, default_head),
            ("Height (Sz)", "Sz", 0.01, 15, default_head),
        ]

        # Body
        body_frame = ttk.Labelframe(master, text="Cog Scale")
        body_frame.pack(fill="x", expand=True, padx=5, pady=0)

        for label, axis, min_val, max_val, default_val in flatten_slider_body_defs:
            var = tk.DoubleVar(value=default_val)
            self.flatten_body_vars[axis] = var
            # Row frame
            row = ttk.Frame(body_frame)
            row.pack(fill="x", expand=True, pady=2)
            # Label
            ttk.Label(row, text=label, width=11, anchor="w").pack(side=tk.LEFT)
            # Slider
            scale = ttk.Scale(row, from_=min_val, to=max_val, orient=tk.HORIZONTAL, variable=var)
            scale.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
            # Text Entry
            entry = ttk.Entry(row, textvariable=var, width=7)
            entry.pack(side=tk.LEFT, padx=5)
            # Reset Buttons
            reset_btn = ttk.Button(row, text="Reset", width=6,
                                   command=lambda axis=axis, v=var: self.reset_flat_body_axis(axis, v))
            reset_btn.pack(side=tk.LEFT)
            var.trace_add("write", self._create_flatten_trace_callback(var, axis))

        # Head
        head_frame = ttk.Labelframe(master, text="Head Scale")
        head_frame.pack(fill="x", expand=True, padx=5, pady=0)

        for label, axis, min_val, max_val, default_val in flatten_slider_head_defs:
            var = tk.DoubleVar(value=default_val)
            self.flatten_head_vars[axis] = var
            # Row frame
            row = ttk.Frame(head_frame)
            row.pack(fill="x", expand=True, pady=2)
            # Label
            ttk.Label(row, text=label, width=11, anchor="w").pack(side=tk.LEFT)
            # Slider
            slider = ttk.Scale(row, from_=min_val, to=max_val,
                               orient=tk.HORIZONTAL, variable=var)
            slider.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
            # Text Entry
            entry = ttk.Entry(row, textvariable=var, width=7)
            entry.pack(side=tk.LEFT, padx=5)
            # Reset Buttons
            reset_btn = ttk.Button(row, text="Reset", width=6,
                                   command=lambda axis=axis: self.reset_flat_head_axis(axis))
            reset_btn.pack(side=tk.LEFT)
            var.trace_add("write", self._create_flatten_head_trace_callback(var, axis))

        # Reset all scale
        ttk.Separator(master, orient=tk.HORIZONTAL).pack(fill="x", pady=5)
        reset_all_btn = ttk.Button(master, text="Reset All Controls", command=self.reset_flatten)
        reset_all_btn.pack(fill="x", expand=True)

    def _create_color_controls(self, master):  # i color the cog
        entry_frame = ttk.Frame(master)
        entry_frame.pack(fill='x', pady=5)

        ttk.Label(entry_frame, text="Hex (#RRGGBB):").pack(side=tk.LEFT, padx=(0, 5))

        self.hex_color_var = tk.StringVar(value="#FFFFFF")
        self.hex_entry = ttk.Entry(entry_frame, textvariable=self.hex_color_var, width=10)
        self.hex_entry.pack(side=tk.LEFT, padx=5)

        def open_picker():
            color = askcolor(color=self.hex_color_var.get())[1]
            if color:
                self.hex_color_var.set(color)

        picker_btn = ttk.Button(entry_frame, text="Picker", width=6, command=open_picker)
        picker_btn.pack(side=tk.LEFT, padx=5)

        btn_frame = ttk.Frame(master)
        btn_frame.pack(fill='x', pady=5)

        ttk.Button(btn_frame, text="Set Cog ColorScale",
                   command=lambda: self.app.apply_body_colorscale(self.hex_color_var.get())
                   ).pack(fill='x', pady=2)

        ttk.Button(btn_frame, text="Set Head Color",
                   command=lambda: self.app.apply_head_color(self.hex_color_var.get())
                   ).pack(fill='x', pady=2)

        ttk.Button(btn_frame, text="Set Hand Color",
                   command=lambda: self.app.apply_hand_color(self.hex_color_var.get())
                   ).pack(fill='x', pady=2)

        ttk.Button(btn_frame, text="Reset Cog Colors",
                   command=self.app.reset_cog_colors
                   ).pack(fill='x', pady=5)

        ttk.Separator(btn_frame, orient=tk.HORIZONTAL).pack(fill='x', expand=True, pady=5)

        ttk.Button(btn_frame, text="Set Background Color",
                   command=lambda: self.app.apply_background_color(self.hex_color_var.get())
                   ).pack(fill='x', pady=2)

        ttk.Button(btn_frame, text="Reset Background Color",
                   command=self.app.reset_background_color
                   ).pack(fill='x', pady=5)

    def _create_head_hpr_sliders(self, master):
        default = self.app.get_head_hpr_default_values()
        slider_defs = [
            ("Left/Right", "x", -15, 15, default["x"]),
            ("Front/Back", "y", -15, 15, default["y"]),
            ("Up/Down", "z", -15, 15, default["z"]),
            ("Heading", "h", -180, 180, default["h"]),
            ("Pitch", "p", -180, 180, default["p"]),
            ("Roll", "r", -180, 180, default["r"]),
            ("Scale", "scale", 0.0, 15, default["scale"])
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
                                   command=lambda axis=axis, v=var: self.reset_head_axis(axis, v))
            reset_btn.pack(side=tk.LEFT)

            var.trace_add("write", self._create_hpr_trace_callback(var, axis))

        # Reset All Button
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill='x', expand=True, pady=5)
        reset_all_btn = ttk.Button(main_frame, text="Reset All Head Controls", command=self.reset_head_hpr)
        reset_all_btn.pack(fill="x", expand=True)

    def update_head_hpr_sliders(self):
        if not hasattr(self.app, "store_head_hpr"):
            return

        for axis, var in self.head_hpr_vars.items():
            if axis in self.app.store_head_hpr:
                var.set(self.app.store_head_hpr[axis])

    def _create_color_frame(self):
        master = self.color_inner_frame
        master.update_idletasks()

    def _create_suit_library(self, master):
        # -------- SUIT TEXTURES --------#
        SUIT_TEXTURES = globals.SUIT_TEXTURES

        suit_notebook = ttk.Notebook(master)
        suit_notebook.grid(row=0, column=0, sticky="nsew")
        suit_categories = ["Standard", "Manager", "Halloween", "Skelecog"]  # Each of the suit categories
        self.selected_suit_tex_var = tk.StringVar()

        # This part fills the categories
        for category in suit_categories:
            category_suit_data = SUIT_TEXTURES.get(category, {})  # Get the data from suit textures dictionary
            tex_frame = self._create_scrollable_radio_list(suit_notebook, f"{category} Suit Textures",
                                                           list(category_suit_data.keys()), self.selected_suit_tex_var,
                                                           self.on_suit_tex_select, 225, 225)
            suit_notebook.add(tex_frame, text=category)

        # -------- SUIT MODELS --------#
        SUIT_MODEL_DICT = list(globals.SUIT_MODEL_DICT.keys())[:-1]  # fuDGE you bosscog model
        suit_model_names = [(globals.SUIT_MODEL_NAMES[k], k) for k in SUIT_MODEL_DICT]

        suit_mod_notebook = ttk.Notebook(master)
        suit_mod_notebook.grid(row=0, column=1, sticky="e")
        self.selected_suit_mod_var = tk.StringVar()

        mod_frame = self._create_scrollable_radio_list(suit_mod_notebook, "Suit Models", suit_model_names,
                                                       self.selected_suit_mod_var, self.on_suit_mod_select, 225, 225,
                                                       True)
        suit_mod_notebook.add(mod_frame, text="Suit Models")

        # -------- SUIT EMBLEMS --------#
        self.selected_emblem_var = tk.StringVar()
        emblem_dict = list(globals.EMBLEM_MAP.keys())
        emblem_frame = self._create_radio_list(suit_mod_notebook, "Chest Emblems", emblem_dict,
                                                          self.selected_emblem_var, self.on_emblem_select)
        suit_mod_notebook.add(emblem_frame, text="Emblems")

        # ---------- SUIT NECKTIES --------------#
        tie_frame = self._create_radio_list(suit_mod_notebook, "Necktie Models", self.TIE_OPTIONS,
                                                 self.selected_tie_var, self.on_tie_select_radio)
        suit_mod_notebook.add(tie_frame, text="Neckties")

    def on_suit_tex_select(self):
        suit_name = self.selected_suit_tex_var.get()
        if suit_name:
            for category in globals.SUIT_TEXTURES:
                if suit_name in globals.SUIT_TEXTURES[category]:
                    texture_path = globals.SUIT_TEXTURES[category].get(suit_name)
                    if texture_path:
                        self.app.apply_suit_texture(texture_path)

    def on_suit_mod_select(self):
        suit_key = self.selected_suit_mod_var.get()
        if suit_key in globals.SUIT_MODEL_DICT:
            self.app.apply_suit_model(suit_key)

    def on_emblem_select(self):
        emblem_key = self.selected_emblem_var.get()
        emblem_name = globals.EMBLEM_MAP.get(emblem_key)
        if emblem_key in globals.EMBLEM_MAP:
            self.app.apply_emblem(emblem_name)
            # Override health meter
            self.app.store_health_meter = False

    def _create_prop_sliders(self, master, update_callback):
        is_prop1 = (update_callback == self.app.update_prop_hpr)
        vars_dict = self.prop1_vars if is_prop1 else self.prop2_vars

        slider_defs = [
            ("Left/Right", "x", -30, 30, 0.0),
            ("Front/Back", "y", -30, 30, 0.0),
            ("Up/Down", "z", -30, 30, 0.0),
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

    def _create_scrollable_radio_list(self, master, label_text, items, variable, command, width=200, height=100,
                                      set_text=False):
        frame = ttk.Labelframe(master, text=label_text)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set, borderwidth=0, highlightthickness=0, width=width,
                           height=height)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=canvas.yview)
        inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        if not set_text:
            for item in items:
                ttk.Radiobutton(
                    inner_frame,
                    text=item,
                    variable=variable,
                    value=item,
                    command=command
                ).pack(anchor="nw", fill="x", padx=5, pady=1)
        else:
            for display_text, key in items:
                ttk.Radiobutton(
                    inner_frame,
                    text=display_text,
                    variable=variable,
                    value=key,
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

        # Derrick Hand broken skelecog anim fix
        if self.app.current_cog == "Derrick Hand":
            head_anims = (anim for anim in head_anims if "skele" not in anim.lower())

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
                value = var.get()
                self.app.update_head_hpr(axis, value)
            except tk.TclError:
                pass

        return trace_callback

    def _create_flatten_trace_callback(self, var, axis):
        def trace_callback(*args):
            try:
                value = var.get()
                self.app.update_flatten_body(axis, value)
            except tk.TclError:
                pass

        return trace_callback

    def _create_flatten_head_trace_callback(self, var, axis):
        def trace_callback(*args):
            try:
                value = var.get()
                self.app.update_flatten_head(axis, value)
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

    def reset_head_axis(self, axis, var):
        default_val = self.app.get_head_hpr_default_values()[axis]
        var.set(default_val)
        if hasattr(self.app, "store_head_hpr"):
            self.app.store_head_hpr[axis] = default_val

        self.app.update_head_hpr(axis, default_val)

    def reset_head_hpr(self):
        default = self.app.get_head_hpr_default_values()
        for axis, var in self.head_hpr_vars.items():
            var.set(default[axis])

        self.app.store_head_hpr = globals.HEAD_HPR_DEFAULTS.copy()

    def reset_flat_body_axis(self, axis, var):
        default_val = self.app.cog_data.get("scale", 1.0)
        var.set(default_val)

        self.app.update_flatten_body(axis, default_val)

    def reset_flat_head_axis(self, axis):
        default = self.app.cog_data.get("headSize", 1.0)
        self.flatten_head_vars[axis].set(default)
        self.app.update_flatten_head(axis, default)

    def reset_flatten(self):
        default_body = self.app.cog_data.get("scale", 1.0)
        default_head = self.app.cog_data.get("headSize", 1.0)
        # Reset Flatten Body
        for axis, var in self.flatten_body_vars.items():
            var.set(default_body)
            self.app.update_flatten_body(axis, default_body)
        # Reset Flatten Head
        for axis, var in self.flatten_head_vars.items():
            var.set(default_head)
            self.app.update_flatten_head(axis, default_head)

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

    def show_suit_library(self, show=True):
        if show:
            try:
                self.bottom_notebook.add(self.suit_library_frame, text='Suit Library')
            except tk.TclError:
                pass
        else:
            try:
                self.bottom_notebook.hide(self.suit_library_frame)
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
        self.app.store_necktie = tie_name
        if tie_name:
            self.app.set_necktie(tie_name)

    def on_body_anim_select(self, event):
        anim_name = self._get_selected_from_listbox(event)
        if anim_name:
            self.app.set_animation(anim_name)
            self.app.check_body_autoplay()

    def on_head_anim_select(self, event):
        anim_name = self._get_selected_from_listbox(event)
        if anim_name:
            self.app.set_head_animation(anim_name)
            self.app.check_head_autoplay()

    def on_prop1_select(self, event):
        prop_name = self._get_selected_from_listbox(event)
        if prop_name:
            self.app.set_prop(prop_name)

    def on_prop2_select(self, event):
        prop_name = self._get_selected_from_listbox(event)
        if prop_name:
            self.app.set_prop2(prop_name)

    def show_body_toggle(self, show=True):
        if show:
            self.body_toggle_btn.grid()
        else:
            self.body_toggle_btn.grid_remove()


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
        self.previous_prop1 = "zero"
        self.prop_item1 = "zero"
        self.previous_prop2 = "zero"
        self.prop_item2 = "zero"
        self.last_pose_frame = 0
        self.cog_list = list(globals.COG_DATA)
        self.current_cog_index = 0
        self.current_cog = self.cog_list[self.current_cog_index]
        self.cog_data = globals.COG_DATA[self.current_cog]
        self.custom_model = None
        self.suit_is_executive = False
        self.suit_is_fired = False
        self.prop_item1_actor = None
        self.prop_item2_actor = None
        self.splat_stages = []
        self.suit_type = None
        self.background_color = (105 / 255, 105 / 255, 105 / 255)

        self.control_panel = ControlPanel(self.base.tkRoot, self)
        self.control_panel.setup_custom_model_tab()
        self.shadow = loader.loadModel(globals.SHADOW_MODEL)
        self.shadow.setScale(globals.SHADOW_SCALE)
        self.shadow.setColor(globals.SHADOW_COLOR)

        self.skele_i = 0
        self.skele_meter_color = 0
        self.skele_color_index = 0
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

        # Store a bunch of data
        self.store_head_texture = None
        self.store_suit_texture = None
        self.store_skelecog_texture = None
        self.store_health_meter = False
        self.store_emblem = "emblem_sales"
        self.store_necktie = "(Default)"
        self.store_costume = None
        self.store_virtualize = False
        self.store_head_hpr = globals.HEAD_HPR_DEFAULTS.copy()
        # Stored unique toggles
        self.store_unique_suit_toggle = False
        self.store_cycle_slot_l = False
        self.store_cycle_slot_m = False
        self.store_cycle_slot_r = False
        # Stored Body anims
        self.store_body_anim = None
        self.store_body_frame = 0
        self.store_body_loop = False
        self.store_body_adjusted = False
        self.store_body_playing = False
        # Stored Head anims
        self.store_head_anim = None
        self.store_head_frame = 0
        self.store_head_loop = False
        self.store_head_adjusted = False
        self.store_head_playing = False
        # Stored Scale vals
        self.store_flatten_body = {
            "Sx": self.cog_data.get("scale", 1.0),
            "Sy": self.cog_data.get("scale", 1.0),
            "Sz": self.cog_data.get("scale", 1.0),
        }
        self.store_flatten_head = {
            "Sx": self.cog_data.get("headSize", 1.0),
            "Sy": self.cog_data.get("headSize", 1.0),
            "Sz": self.cog_data.get("headSize", 1.0),
        }
        # Stored Colors
        self.store_body_hex_color = None
        self.store_body_color = False
        self.store_head_hex_color = None
        self.store_head_color = False
        self.store_hand_hex_color = None
        self.store_hand_color = False
        # Stored Props
        self.current_prop1 = "zero"
        self.current_prop2 = "zero"
        self.store_prop1 = "zero"
        self.store_prop2 = "zero"
        self.store_prop1_hpr = globals.HEAD_HPR_DEFAULTS.copy()
        self.store_prop2_hpr = globals.HEAD_HPR_DEFAULTS.copy()
        self.store_custom_model = None
        self.store_custom_model_hpr = globals.HEAD_HPR_DEFAULTS.copy()

    def load_cog(self, cog_name):
        self.current_cog = cog_name
        self.build_cog()

        try:
            self.control_panel.selected_cog_var.set(cog_name)
        except Exception as e:
            print(f"Could not update cog selection: {e}")

    def set_POSHPR(self, target, axis, value):
        POSHPR_DICT = {
            "x": target.setX,
            "y": target.setY,
            "z": target.setZ,
            "h": target.setH,
            "p": target.setP,
            "r": target.setR,
            "scale": target.setScale
        }
        pos = POSHPR_DICT.get(axis)
        if pos:
            pos(value)

    def set_depth(self, target, axis, value):
        # Store scale vals
        if hasattr(self, "store_flatten_body"):
            if target == self.actor:
                self.store_flatten_body[axis] = value
            else:
                self.store_flatten_head[axis] = value

        SCALE_DICT = {
            "Sx": target.setSx,
            "Sy": target.setSy,
            "Sz": target.setSz,
        }
        func = SCALE_DICT.get(axis)
        if func:
            func(value)

    def update_head_hpr(self, axis, value):
        if not hasattr(self, 'head') or self.head.isEmpty():
            return
        self.set_POSHPR(self.head, axis, value)
        self.store_head_hpr[axis] = value

    def update_flatten_body(self, axis, value):
        if not hasattr(self, 'actor') or self.actor is None:
            return
        self.set_depth(self.actor, axis, value)

    def update_flatten_head(self, axis, value):
        if not hasattr(self, "head") or self.head.isEmpty():
            return
        self.set_depth(self.head, axis, value)

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
            self.set_POSHPR(item_to_move, axis, value)
            self.store_prop1_hpr[axis] = value

    def update_prop2_hpr(self, axis, value):
        item_to_move = self.prop_item2_actor if self.prop_item2_actor else self.prop_item2

        if item_to_move != "zero" and not item_to_move.isEmpty():
            self.set_POSHPR(item_to_move, axis, value)
            self.store_prop2_hpr[axis] = value

    def set_prop(self, prop, check_prop=True):
        if self.prop_item1_actor:
            self.prop_item1_actor.cleanup()
            self.prop_item1_actor.removeNode()
            self.prop_item1_actor = None
        if self.prop_item1 != "zero" and not self.prop_item1.isEmpty():
            self.prop_item1.removeNode()
            self.prop_item1 = "zero"
        self.control_panel.hide_prop_anim_ui(self.control_panel.prop1_anim_frame)

        if check_prop:
            if self.current_prop1 == prop:
                # Clicked same prop, toggle off
                self.current_prop1 = "zero"
                self.store_prop1 = "zero"
                return

        self.current_prop1 = prop
        self.store_prop1 = prop
        prop_data = globals.PROPS_DICT[prop]

        if prop_data.get("anims"):
            # It's an animated prop
            self.prop_item1_actor = Actor(prop_data["model"], prop_data["anims"])
            if self.cog_data.get("cog_type") == "boss":
                self.prop_item1_actor.reparentTo(self.boss_parts["torso"].find('**/joint17'))
            else:
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
            if self.cog_data.get("cog_type") == "boss":
                self.prop_item1.reparentTo(self.boss_parts["torso"].find('**/joint17'))
            else:
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
        if check_prop:
            self.control_panel.reset_prop_sliders(self.control_panel.prop1_vars)

    def set_prop2(self, prop2, check_prop=True):
        if self.prop_item2_actor:
            self.prop_item2_actor.cleanup()
            self.prop_item2_actor.removeNode()
            self.prop_item2_actor = None
        if self.prop_item2 != "zero" and not self.prop_item2.isEmpty():
            self.prop_item2.removeNode()
            self.prop_item2 = "zero"
        self.control_panel.hide_prop_anim_ui(self.control_panel.prop2_anim_frame)

        if check_prop:
            if self.current_prop2 == prop2:
                self.current_prop2 = "zero"
                self.store_prop2 = "zero"
                return

        self.current_prop2 = prop2
        self.store_prop2 = prop2
        prop_data = globals.PROPS_DICT[prop2]

        if prop_data.get("anims"):
            # It's an animated prop
            self.prop_item2_actor = Actor(prop_data["model"], prop_data["anims"])
            if self.cog_data.get("cog_type") == "boss":
                self.prop_item2_actor.reparentTo(self.boss_parts["torso"].find('**/joint17'))
            else:
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
            if self.cog_data.get("cog_type") == "boss":
                self.prop_item2.reparentTo(self.boss_parts["torso"].find('**/joint17'))
            else:
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
        if check_prop:
            self.control_panel.reset_prop_sliders(self.control_panel.prop2_vars)

    def add_pie_splat(self):
        cog_data = globals.COG_DATA[self.current_cog]
        if not self.actor: return
        splat_dir = os.path.join(globals.RESOURCES_DIR, "phase_5", "maps")
        search_pattern = os.path.join(splat_dir, "splat_*.png")

        possible_splats = glob.glob(search_pattern)

        possible_splats = [f for f in possible_splats if "splat_grayscale.png" not in f]
        possible_splats = [f for f in possible_splats if "splat_fruit.png" not in f]

        if not possible_splats:
            print(f"No splat textures found in: {splat_dir}")
            return

        # 2. Pick a random texture from the found files
        chosen_path = random.choice(possible_splats)

        # Convert to Panda3D filename to ensure cross-platform compatibility
        p3d_path = Filename.fromOsSpecific(chosen_path)
        pie_tex = loader.loadTexture(p3d_path)

        if not pie_tex:
            print("Failed to load texture.")
            return

        # 3. Configure Texture Wrapping
        pie_tex.setWrapU(Texture.WMBorderColor)
        pie_tex.setWrapV(Texture.WMBorderColor)
        pie_tex.setBorderColor((0, 0, 0, 0))  # Transparent border

        # 4. Create a unique TextureStage
        # Sort > 10 ensures it draws on top of the suit texture and previous splats
        stage_name = f"splatStage_{len(self.splat_stages)}"
        decal_stage = TextureStage(stage_name)
        decal_stage.setMode(TextureStage.MDecal)
        decal_stage.setSort(10 + len(self.splat_stages))

        # 5. Randomize Position and Size
        # Scale: Higher number = Smaller splat (UV coordinates are inverse)
        # We vary the scale slightly so they don't all look identical
        scale_x = random.uniform(0.75, 0.5)
        scale_y = random.uniform(0.75, 0.5)
        offset_x = random.uniform(0.0, 0.50)
        offset_y = random.uniform(0.0, 0.25)

        # 6. Apply to the Body node
        if cog_data["suit"] in ["boss"]:
            body = self.boss_parts["torso"]
        else:
            body = self.actor.find('**/body')
        if not body.isEmpty():
            body.setTexture(decal_stage, pie_tex)
            body.setTexScale(decal_stage, scale_x, scale_y)
            body.setTexOffset(decal_stage, offset_x, offset_y)

            self.splat_stages.append(decal_stage)

        head = self.head
        if not head.isEmpty():
            head.setTexture(decal_stage, pie_tex)
            head.setTexScale(decal_stage, scale_x, scale_y)
            head.setTexOffset(decal_stage, offset_x, offset_y)

            self.splat_stages.append(decal_stage)

    def clear_pie_splats(self):
        cog_data = globals.COG_DATA[self.current_cog]
        if not self.actor: return

        if cog_data["suit"] in ["boss"]:
            body = self.boss_parts["torso"]
        else:
            body = self.actor.find('**/body')
        if not body.isEmpty():
            for stage in self.splat_stages:
                body.clearTexture(stage)
        head = self.head
        if not head.isEmpty():
            for stage in self.splat_stages:
                head.clearTexture(stage)

        self.splat_stages = []

    def set_head_animation(self, animation):
        self.current_head_animation = animation
        self.head.loop(animation)
        self.is_posed = False

        if self.current_head_animation != self.store_head_anim:
            self.store_head_frame = 0
            self.store_head_adjusted = False

        try:
            num_frames = self.head.getNumFrames(self.current_head_animation)
            self.control_panel.update_anim_slider_range("head", num_frames)
            self.store_head_anim = self.current_head_animation
        except:
            self.control_panel.update_anim_slider_range("head", 0)
            self.store_head_anim = None

    def set_animation(self, animation):
        self.current_animation = animation
        self.actor.loop(animation)
        self.is_posed = False

        if self.current_animation != self.store_body_anim:
            self.store_body_frame = 0
            self.store_body_adjusted = False

        try:
            num_frames = self.actor.getNumFrames(self.current_animation)
            self.control_panel.update_anim_slider_range("body", num_frames)
            self.store_body_anim = self.current_animation
        except:
            self.control_panel.update_anim_slider_range("body", 0)
            self.store_body_anim = None

    def check_body_autoplay(self):
        if self.control_panel.is_autoplay_var.get():  # Autoplay on
            self.play_body_animation()
        else:  # Autoplay off
            self.stop_body_animation()

    def check_head_autoplay(self):
        if self.control_panel.is_autoplay_var.get():  # Autoplay on
            self.play_head_animation()
        else:  # Autoplay off
            self.stop_head_animation()

    def take_screenshot(self):
        cog_data = globals.COG_DATA[self.current_cog]
        path = globals.SCREENSHOT_DIR
        if not os.path.exists(path):
            os.makedirs(path)
        now = datetime.now()
        date_string = now.strftime("%d-%m-%Y-%H-%M-%S")
        screenshot_name = os.path.join(path, "ss-{}-{}.png".format(cog_data["cog"], date_string))
        self.setBackgroundColor(0, 0, 0)
        self.graphicsEngine.renderFrame()
        self.graphicsEngine.renderFrame()
        self.base.screenshot(screenshot_name, False)
        self.setBackgroundColor(self.background_color)

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
            # Check if the current loaded cog is a boss
            if self.cog_data.get("cog_type") == "boss":
                self.actor.setH(0)
            else:
                self.actor.setH(180)

    def reset_camera_pos(self):
        self.disable_mouse_cam()
        base.camera.setPosHpr(*globals.DEFAULT_CAMERA_POS, 0, 0, 0)
        self.enable_mouse_cam()

    def play_body_animation(self):
        if self.current_animation != "zero":
            self.is_posed = False
            self.store_body_adjusted = False
            self.store_body_playing = True
            self.store_body_frame = 0

            # Check if this is a Boss Cog
            if self.cog_data.get("cog_type") == "boss" and hasattr(self, "boss_parts"):
                # Loop through all parts (legs, torso) but exclude the head
                for part_name, part_actor in self.boss_parts.items():
                    if part_name == "head": continue  # Head is controlled separately

                    if isinstance(part_actor, Actor):
                        # Use try/except or check valid animations to prevent crashing
                        # if a specific part doesn't share the animation name
                        if self.control_panel.loop_body_var.get():
                            part_actor.loop(self.current_animation)
                        else:
                            part_actor.play(self.current_animation)

            # Standard Cog behavior
            elif self.actor:
                if self.control_panel.loop_body_var.get():
                    self.actor.loop(self.current_animation)
                else:
                    self.actor.play(self.current_animation)

    def stop_body_animation(self):
        if self.current_animation != "zero":
            self.is_posed = True
            self.store_body_adjusted = True
            self.store_body_playing = False
            self.store_body_frame = 0

            # Boss Cog Behavior
            if self.cog_data.get("cog_type") == "boss" and hasattr(self, "boss_parts"):
                for part_name, part_actor in self.boss_parts.items():
                    if part_name == "head": continue
                    if isinstance(part_actor, Actor):
                        part_actor.pose(self.current_animation, 0)

            # Standard Cog Behavior
            elif self.actor:
                self.actor.pose(self.current_animation, 0)

            self.control_panel.body_frame_slider.set(0)

    def play_head_animation(self):
        if hasattr(self, 'head') and self.head and self.current_head_animation != "zero":
            self.is_posed = False
            self.store_head_adjusted = False
            self.store_head_playing = True
            self.store_head_frame = 0

            if self.control_panel.loop_head_var.get():
                self.head.loop(self.current_head_animation)
            else:
                self.head.play(self.current_head_animation)

    def stop_head_animation(self):
        if hasattr(self, 'head') and self.head and self.current_head_animation != "zero":
            self.is_posed = True
            self.store_head_adjusted = True
            self.store_head_playing = False
            self.store_head_frame = 0

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
        self.prop_item1_actor.setTwoSided(True)

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
        self.prop_item2_actor.setTwoSided(True)

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

    def build_cog(self, suit_type=None, refresh_cog=True):
        pos = (0, 0, 0)
        hpr = (180, 0, 0)

        self.skele_meter_color = 0
        self.flatten_switch = 0

        self.current_head_animation = "zero"
        self.current_animation = "zero"
        self.is_posed = False
        self.control_panel.show_suit_library(True)
        self.control_panel.show_body_toggle(True)

        if not self.actor == None:
            pos = self.actor.getPos()
            current_hpr = self.actor.getHpr()

            prev_is_boss = False
            if self.cog_data:
                prev_is_boss = self.cog_data.get("cog_type") == "boss"

            if prev_is_boss:
                hpr = globals.DEFAULT_HPR
            else:
                hpr = current_hpr

            self.actor.cleanup()
            self.actor.removeNode()

        if hasattr(self, 'boss_parts'):  # Cleanup old boss parts
            for part in self.boss_parts.values():
                if isinstance(part, Actor): part.cleanup()
                part.removeNode()
        self.boss_parts = {}  # Reset

        head_path = ""
        head_animations = {}

        cog_data = globals.COG_DATA[self.current_cog]
        self.cog_data = cog_data
        dept = cog_data["dept"]

        self.clear_pie_splats()

        if suit_type == None:
            suit_type = self.cog_data["suit"]

        if cog_data.get("cog_type") == "boss":
            self.build_boss_cog(cog_data)
            return

        self.build_body(suit_type)

        ##### SET SUIT/NECKTIE TEXTURE ########################################
        tx_suit = loader.loadTexture(cog_data["suitTex"])
        if suit_type in ["erfit"] or cog_data['name'] in ["ttcc_ene_counterfit"]:
            self.actor.find('**/body').setTexture(tx_suit, 1)
        else:
            self.actor.find('**/body').setTexture(tx_suit, 1)
            self.actor.find('**/necktie-s').setTexture(tx_suit, 1)
            self.actor.find('**/necktie-w').setTexture(tx_suit, 1)
            self.actor.find('**/bowtie').setTexture(tx_suit, 1)

        # Fix for Bellringer & Insider, set their hand textures
        if suit_type == "bc":
            self.actor.find('**/hands').setTexture(tx_suit, 1)

        if (suit_type == "mph"):
            tx_body = loader.loadTexture(globals.MP_BODY)
            self.actor.find('**/bowtie').setTexture(tx_body, 1)
            self.actor.find('**/highroller_body').setTexture(tx_body, 1)

        # Call build_necktie function
        if suit_type not in globals.NO_NECKTIE_SUITS:
            self.build_necktie()
        else:
            self.control_panel.hide_tie_list()
            if suit_type not in ["erfit"]:
                self.actor.find('**/necktie-s').hide()  # Hide Sellbot necktie
                self.actor.find('**/necktie-w').hide()  # Hide Cash/Boss/Board necktie
                self.actor.find('**/bowtie').hide()  # Hide Law bowtie

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

            emblem = cog_data["emblem"]
            self.iconbase.find(f'**/{emblem}').show()

            if suit_type in ["a", "af", "cch", "mph", "hr"]:
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

            # If our actor is High Roller, hide the emblem
            if suit_type is "hr":
                self.iconbase.hide()

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
        self.control_panel.is_costume_var.set(False)
        self.control_panel.is_executive_var.set(False)
        self.control_panel.is_fired_var.set(False)
        self.control_panel.is_waiter_var.set(False)
        self.is_body = True

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

        if suitToggle in ["hr", "rm", "dj", "u", "cch", "chainsaw", "ms"]:
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

        # Used to refresh the store variables used for apply suit model function
        if refresh_cog:
            self.reset_stored_vals()

    def build_body(self, suit_type):
        body_path = ""
        body_animations = {}

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

    def build_necktie(self):
        cog_data = self.cog_data
        self.control_panel.show_tie_list()

        # We hide the neckties by default, then re-enable them for departments
        self.actor.find('**/necktie-s').hide()  # Hide Sellbot necktie
        self.actor.find('**/necktie-w').hide()  # Hide Cash/Boss/Board necktie
        self.actor.find('**/bowtie').hide()  # Hide Law bowtie

        if cog_data["cog"] not in globals.NO_NECKTIE_COGS:
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
        is_skelecog = self.suit_type in ["as", "bs", "cs"]
        not_erfit = self.suit_type != "erfit"

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

        # Waiter bowtie:
        if not is_skelecog and not_erfit:
            if is_waiter:
                self.actor.find('**/bowtie').show()
                self.actor.find('**/necktie-s').hide()
                self.actor.find('**/necktie-w').hide()
            else:
                self.control_panel.on_tie_select_radio()

        cog_name = self.cog_data["name"]
        dept = self.cog_data["dept"]

        paths = globals.SUIT_TEXTURE_PATH

        tex_key = dept
        if is_skelecog:
            tex_key = dept + "s"
        elif cog_name in paths:
            tex_key = cog_name

        tex_list = paths.get(tex_key)
        if not tex_list: return

        tex_index = 0  # Default

        if is_fired:
            tex_index = -1

        elif is_waiter and tex_key in ["c", "cs"] and len(tex_list) > 3:
            if is_exec:
                tex_index = 3
            else:
                tex_index = 2

        elif is_exec and len(tex_list) > 1:
            tex_index = 1

        # Apply the texture
        tex_to_apply = tex_list[tex_index]
        tx_suit = loader.loadTexture(tex_to_apply)
        self.actor.find('**/body').setTexture(tx_suit, 1)
        if not_erfit:
            self.actor.find('**/necktie-s').setTexture(tx_suit, 1)
            self.actor.find('**/necktie-w').setTexture(tx_suit, 1)
            self.actor.find('**/bowtie').setTexture(tx_suit, 1)

        if not is_skelecog:
            self.store_suit_texture = tex_to_apply
        else:
            self.store_skelecog_texture = tex_to_apply

        if self.cog_data["suitToggle"] in ["s"]:
            tex_key = dept + "s"
            tex_list = paths.get(tex_key)
            tex_to_apply = tex_list[tex_index]
            tx_suit = loader.loadTexture(tex_to_apply)
            self.head.setTexture(tx_suit, 1)  # Skelecogs
            self.store_head_texture = tex_to_apply

        elif cog_name in ["cc_a_ene_bagholder", "cc_a_ene_insider", "cc_a_ene_headhoncho"]:  # stupid boardbots
            head_tex_list = globals.HEAD_TEXTURE_PATH.get(tex_key)
            if head_tex_list:
                head_tex = head_tex_list[0]
                if is_fired:
                    head_tex = head_tex_list[-1]
                elif is_exec:
                    head_tex = head_tex_list[1]
                self.head.setTexture(loader.loadTexture(head_tex), 1)
                self.store_head_texture = head_tex

    def toggle_unique_suit(self, iterate=True):
        """Handles the 'cycle' button for unique suit toggles."""
        if not self.cog_data: return

        self.store_unique_suit_toggle = True
        cog_name = self.cog_data["name"]
        suitToggle = self.cog_data.get("suitToggle")

        # Chainsaw Consultant
        if suitToggle == "chainsaw":
            suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_name)
            head_paths = globals.HEAD_TEXTURE_PATH.get(cog_name)
            if iterate:
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

        # Chainsaw Consultant (Halloween)
        elif suitToggle == "cch":
            suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_name)
            head_paths = globals.HEAD_TEXTURE_PATH.get(cog_name)
            if iterate:
                self.it = (self.it + 1) % len(suit_paths)
            tx_head = loader.loadTexture(head_paths[self.it])
            self.head.setTexture(tx_head, 1)
            if self.it > 1:
                self.head.find('**/bulbLeft').hide()
            else:
                self.head.find('**/bulbLeft').show()

        # Multislacker
        elif suitToggle == "ms":
            suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_name)
            head_paths = globals.HEAD_TEXTURE_PATH.get(cog_name)
            if iterate:
                self.it = (self.it + 1) % len(suit_paths)
            tx_head = loader.loadTexture(head_paths[self.it])
            self.head.setTexture(tx_head, 1)
            self.store_head_texture = head_paths[self.it]

        # High Roller
        elif suitToggle == "hr":
            suit_paths = globals.SUIT_TEXTURE_PATH.get("hr")
            body_paths = globals.HEAD_TEXTURE_PATH.get("hr")
            if iterate:
                self.it = (self.it + 1) % len(suit_paths)
            tx_suit = loader.loadTexture(suit_paths[self.it])
            tx_body = loader.loadTexture(body_paths[self.it])
            self.actor.find('**/body').setTexture(tx_suit, 1)
            # check if the suit has the high roller model
            if self.suit_type in ["hr"]:
                self.actor.find('**/highroller_body').setTexture(tx_body, 1)
            self.store_suit_texture = suit_paths[self.it]

        # Rainmaker
        elif suitToggle == "rm":
            for Hair in self.head.findAllTextureStages("*hair"):
                if iterate:
                    self.it2 += 0.2
                if self.it2 == 1: self.it2 = 0
                self.head.setTexOffset(Hair, 0, self.it2)

        # Desk Jockey
        elif suitToggle == "dj":
            suit_paths = globals.SUIT_TEXTURE_PATH.get("dj")
            self.it = (self.it + 1) % len(suit_paths)
            tx_suit = loader.loadTexture(suit_paths[self.it])
            self.actor.find('**/body').setTexture(tx_suit, 1)
            self.actor.find('**/bowtie').setTexture(tx_suit, 1)
            self.store_suit_texture = suit_paths[self.it]

    def cycle_slot_l(self, iterate=True):
        if not self.head or self.head.isEmpty(): return
        self.store_cycle_slot_l = True
        slotL = self.head.find('**/slotL')
        if not slotL.isEmpty():
            if iterate:
                self.it_l = (self.it_l + 0.25) % 1.0
            slotL.setTexOffset(TextureStage.getDefault(), 0, self.it_l)

    def cycle_slot_m(self, iterate=True):
        if not self.head or self.head.isEmpty(): return
        self.store_cycle_slot_m = True
        slotM = self.head.find('**/slotMid')
        if not slotM.isEmpty():
            if iterate:
                self.it_m = (self.it_m + 0.25) % 1.0
            slotM.setTexOffset(TextureStage.getDefault(), 0, self.it_m)

    def cycle_slot_r(self, iterate=True):
        if not self.head or self.head.isEmpty(): return
        self.store_cycle_slot_r = True
        slotR = self.head.find('**/slotR')
        if not slotR.isEmpty():
            if iterate:
                self.it_r = (self.it_r + 0.25) % 1.0
            slotR.setTexOffset(TextureStage.getDefault(), 0, self.it_r)

    def set_necktie(self, override=None):
        if self.suit_type in ["erfit"]:
            return

        cog_data = self.cog_data

        self.actor.find('**/necktie-s').hide()
        self.actor.find('**/necktie-w').hide()
        self.actor.find('**/bowtie').hide()

        tie_to_show = None
        if override and override != "(Default)":
            tie_override = {
                "Thin Tie": "**/necktie-s",
                "Wide Tie": "**/necktie-w",
                "Bowtie": "**/bowtie",
            }
            if override == "None":
                return
            tie_to_show = tie_override.get(override)
        else:
            if cog_data["cog"] in globals.NO_NECKTIE_COGS:
                return
            else:
                necktie_map = globals.NECKTIE_MAP
                tie_to_show = necktie_map.get(cog_data["cog"]) or necktie_map.get(cog_data["dept"])

        if tie_to_show:
            self.actor.find(tie_to_show).show()

        if self.suit_type in globals.NO_NECKTIE_SUITS:
            self.actor.find(tie_to_show).hide()

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

    def toggle_costume(self, check_stored=True):  # Toggle halloween costumes for managers
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
                if check_stored:
                    self.set_stored_vals()
                self.head.detachNode()
                self.head = self._swap_head_model(hw_head_model_path)
                if check_stored:
                    self.update_cog_attributes(None, True)

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

            if self.suit_type not in ["as", "bs", "cs", "boss"]:
                if "handsHW" in cog_data:
                    self.actor.find('**/hands').setColor(cog_data["handsHW"])

            self.is_costume_active = True

        # Toggle OFF
        else:
            if hw_head_model_path and os.path.isfile(hw_head_model_path):
                self.set_stored_vals()
                self.head.detachNode()
                self.head = self._swap_head_model(cog_data.get("head"))
                self.update_cog_attributes(None, True)

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
                    tx_body_normal = loader.loadTexture(globals.MP_BODY)
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
                "counterfit", "VP", "CFO", "CLO",
                "CEO"]:  # Make sure the cog isn't Count Erfit (he lacks necktie geomnodes)
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

            self.control_panel.is_body_var.set(self.is_body)  # Update the tkpanel status
            self.control_panel.is_background_black_var.set(self.bool)
            self.control_panel.is_executive_var.set(False)
            self.control_panel.is_fired_var.set(False)

            # Hide props
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
            tie_to_set = self.control_panel.selected_tie_var.get()
            self.set_necktie(tie_to_set)
            self.is_body = True  # Flip bool var to false for hide body

            self.load_stored_props()


    def toggle_shadow(self):
        self.is_shadow = not self.is_shadow
        self.control_panel.is_shadow_var.set(self.is_shadow)
        if self.is_shadow:
            self.shadow.show()
        else:
            self.shadow.hide()

    def hex_to_p3d_color(self, hex_code):
        try:
            hex_code = hex_code.lstrip('#')
            if len(hex_code) != 6:
                print(f"Invalid Hex Code: {hex_code}")
                return None
            r, g, b = tuple(int(hex_code[i:i + 2], 16) for i in (0, 2, 4))
            return (r / 255.0, g / 255.0, b / 255.0, 1.0)
        except ValueError:
            print("Invalid Hex input")
            return None

    def apply_body_colorscale(self, hex_code):
        color = self.hex_to_p3d_color(hex_code)
        if not color: return

        if self.actor and not self.boss_parts:
            self.actor.setColorScale(color)

        if hasattr(self, 'boss_parts') and self.boss_parts:
            for part_name, part_node in self.boss_parts.items():
                if part_node and not part_node.isEmpty():
                    part_node.setColorScale(color)
        self.store_body_hex_color = hex_code
        self.store_body_color = True

    def apply_head_color(self, hex_code):
        color = self.hex_to_p3d_color(hex_code)
        if not color: return

        if self.head:
            self.head.setColor(color)
        self.store_head_hex_color = hex_code
        self.store_head_color = True

    def apply_hand_color(self, hex_code):
        color = self.hex_to_p3d_color(hex_code)
        if not color: return

        if self.actor:
            hands = self.actor.find('**/hands')
            if not hands.isEmpty():
                hands.setColor(color)
            else:
                print("Hands node not found (Is this a Skelecog or a boss cog?)")
        self.store_hand_hex_color = hex_code
        self.store_hand_color = True

    def reset_cog_colors(self):
        if self.actor:
            self.actor.clearColorScale()
            hands = self.actor.find('**/hands')
            if not hands.isEmpty():
                hands.clearColor()
                if self.cog_data and "hands" in self.cog_data:
                    hands.setColor(self.cog_data["hands"])
        if self.head:
            self.head.clearColor()

        if hasattr(self, 'boss_parts') and self.boss_parts:
            for part_node in self.boss_parts.values():
                if part_node and not part_node.isEmpty():
                    part_node.clearColorScale()
        self.store_hand_color = False
        self.store_head_color = False
        self.store_body_color = False
        print("Colors reset.")

    def apply_background_color(self, hex_code):
        color = self.hex_to_p3d_color(hex_code)
        if not color: return
        self.background_color = color
        self.setBackgroundColor(color)

    def reset_background_color(self):
        self.background_color = (105 / 255, 105 / 255, 105 / 255)
        self.setBackgroundColor(self.background_color)

    def autoplay_animations(self):
        self.is_autoplay = self.control_panel.is_autoplay_var.get()

    def build_boss_cog(self, cog_data):
        self.control_panel.hide_tie_list()  # Hides necktie options on toggles
        self.control_panel.show_suit_library(False)  # hides suit library
        self.control_panel.show_body_toggle(False)  # hides toggle body

        parts = cog_data["parts"]
        anims = cog_data.get("anims", {})
        cog_name = cog_data["name"]

        if "legs" in parts:
            root_part_name = "legs"
        elif "body" in parts:
            root_part_name = "body"
        else:
            root_part_name = "torso"  # Fallback

        root_path = parts[root_part_name]
        root_anims = anims.get(root_part_name, {})

        self.actor = Actor(root_path, root_anims)
        self.actor.reparentTo(self.render)
        self.actor.setPos(0, 0, 0)
        # self.actor.setHpr(0, 0, 0)
        self.boss_parts[root_part_name] = self.actor
        self.actor.setBlend(frameBlend=True)
        self.actor.setTwoSided(True)

        for part_name, part_path in parts.items():
            if part_name == root_part_name: continue

            part_anims = anims.get(part_name, {})
            if part_anims:
                part_node = Actor(part_path, part_anims)
            else:
                part_node = loader.loadModel(part_path)

            if part_name == "torso" or part_name == "body":
                part_node.reparentTo(self.actor.find("**/joint_pelvis"))

            elif part_name == "head":
                parent = None
                if "torso" in self.boss_parts:
                    parent = self.boss_parts["torso"]
                elif "body" in self.boss_parts:
                    parent = self.boss_parts["body"]
                else:
                    parent = self.actor

                joint = parent.find("**/joint34")
                if joint.isEmpty(): joint = parent.find("**/def_head")
                if joint.isEmpty(): joint = parent.find("**/joint_head")

                if not joint.isEmpty():
                    part_node.reparentTo(joint)
                else:
                    print(f"Warning: Could not find head joint on {parent.getName()}")

                self.head = part_node

            elif part_name == "treads":
                part_node.reparentTo(self.actor.find("**/joint_axle"))

            self.boss_parts[part_name] = part_node

        if "texture" in cog_data:
            tex = loader.loadTexture(cog_data["texture"])
            if "torso" in self.boss_parts:
                self.boss_parts["torso"].find('**/Object').setTexture(tex, 1)
            elif "body" in self.boss_parts:
                self.boss_parts["body"].find('**/Object').setTexture(tex, 1)

        anim_list_key = "torso" if "torso" in anims else "body"
        self.boss_parts["legs"].find('**/mesh_doorFront').reparentTo(self.boss_parts["legs"].find('**/joint_doorFront'))
        self.boss_parts["legs"].find('**/mesh_doorRear').reparentTo(self.boss_parts["legs"].find('**/joint_doorRear'))
        # self.boss_parts["legs"].find('**/joint_doorFront').setHpr(0,0, 80)
        # self.boss_parts["legs"].find('**/joint_doorRear').setHpr(0,0, -80)
        self.boss_parts["legs"].find('**/mesh_doorFront').setPosHprScale(-1.36, 0.00, -6.30, 90.00, 281.31, 0.00, 1.00,
                                                                         1.00, 1.00)
        self.boss_parts["legs"].find('**/mesh_doorRear').setPosHprScale(0.34, 0.00, -6.47, 90.00, 87.00, 0.00, 1.00,
                                                                        1.00, 1.00)

        meter_parent = None
        if "torso" in self.boss_parts:
            meter_parent = self.boss_parts["torso"]
        elif "body" in self.boss_parts:
            meter_parent = self.boss_parts["body"]
        else:
            meter_parent = self.actor

        meter_joint = meter_parent.find('**/joint_lifeMeter')

        medallionColors = {'c': (0.863, 0.776, 0.769, 1.0),
                           's': (0.843, 0.745, 0.745, 1.0),
                           'l': (0.749, 0.776, 0.824, 1.0),
                           'm': (0.749, 0.769, 0.749, 1.0)}
        icon_path = os.path.join(globals.RESOURCES_DIR, "phase_3", "models", "gui", "cog_icons.bam")
        if os.path.exists(icon_path) and not meter_joint.isEmpty():
            dept = cog_data.get('dept', 'c')
            icon_map = {'s': 'SalesIcon', 'm': 'MoneyIcon', 'l': 'LegalIcon', 'c': 'CorpIcon', 'g': 'CorpIcon'}
            node_name = icon_map.get(dept, 'CorpIcon')

            icon_model = loader.loadModel(icon_path)
            icon_node = icon_model.find('**/' + node_name)

            if not icon_node.isEmpty():
                self.boss_icon = icon_node.copyTo(meter_joint)
                if cog_data['name'] in ["CLO"]:
                    self.boss_icon.setPosHprScale(0.00, 0.90, 0.00, 0.00, -20.00, 0.00, 2.00, 2.00, 2.00)
                else:
                    self.boss_icon.setPosHprScale(0.00, -0.15, 0.00, 0.00, -20.00, 0.00, 2.00, 2.00, 2.00)
                self.boss_icon.setColor(medallionColors[dept])

        gui_path = os.path.join(globals.RESOURCES_DIR, "phase_3.5", "models", "gui", "matching_game_gui.bam")
        glow_path = os.path.join(globals.RESOURCES_DIR, "phase_3.5", "models", "props", "glow.bam")

        if os.path.exists(gui_path) and os.path.exists(glow_path) and not meter_joint.isEmpty():
            model = loader.loadModel(gui_path)
            button = model.find('**/minnieCircle')

            if not button.isEmpty():
                self.health_meter = button.copyTo(meter_joint)

                self.health_meter.setScale(6.2)
                self.health_meter.setP(-20)
                if cog_data['name'] in ["CLO"]:
                    self.health_meter.setY(0.90)
                else:
                    self.health_meter.setY(-0.20)
                self.health_meter.setColor(globals.SKELECOG_METER_COLORS[0])

                glow = loader.loadModel(glow_path)
                glow.reparentTo(self.health_meter)
                glow.setScale(0.28)
                glow.setPos(-0.005, 0.01, 0.015)
                glow.setColor(globals.SKELECOG_METER_COLORS[0])

                self.meter_glow = glow
                self.health_meter.hide()
                self.meter_glow.hide()

        anim_list_key = "torso" if "torso" in anims else "body"
        self.available_animations = list(anims.get(anim_list_key, {}).keys())
        self.available_head_animations = list(anims.get("head", {}).keys())
        self.control_panel.update_animation_lists(self.available_animations, self.available_head_animations)

        self.suit_type = "boss"
        self.skele_i = 0

        if self.available_animations:
            first_anim = self.available_animations[20]
            self.actor.pose(first_anim, 0)

            if "torso" in self.boss_parts:
                self.boss_parts["torso"].pose(first_anim, 0)
            elif "body" in self.boss_parts:
                self.boss_parts["body"].pose(first_anim, 0)

            self.actor.update()

        self.control_panel.suit_exec_check.pack_forget()
        self.control_panel.suit_fired_check.pack_forget()
        self.is_costume_active = False
        self.control_panel.is_costume_var.set(False)
        self.control_panel.is_executive_var.set(False)
        self.control_panel.is_fired_var.set(False)
        self.control_panel.is_waiter_var.set(False)

    def toggle_virtualize(self):
        self.store_virtualize = True
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

    def on_tie_select(self, event=None):
        selection = self.control_panel.tie_listbox.curselection()
        if selection:
            selected_tie = self.control_panel.tie_listbox.get(selection[0])
            self.set_necktie(selected_tie)

    def toggle_skele_meter_color(self):
        cog_data = globals.COG_DATA[self.current_cog]
        emblem_hp = self.iconbase.find('**/emblem_hp')
        glow = self.iconbase.find('**/glow')

        self.skele_meter_color = globals.SKELECOG_METER_COLORS[self.skele_i]

        if (self.suit_type in ["as", "bs", "cs"]):
            self.health_meter.setColor(self.skele_meter_color)
            self.meter_glow.setColor(self.skele_meter_color)

        elif (cog_data['name'] in ["VP", "CFO", "CLO"]):

            if self.skele_i < 6:
                if hasattr(self, 'health_meter') and self.health_meter and not self.health_meter.isEmpty():
                    self.health_meter.show()
                    self.health_meter.setColor(self.skele_meter_color)
                if hasattr(self, 'meter_glow') and self.meter_glow and not self.meter_glow.isEmpty():
                    self.meter_glow.show()
                    self.meter_glow.setColor(self.skele_meter_color)
                self.boss_icon.hide()

            # Hide on index 6
            elif self.skele_i == 6:
                if hasattr(self, 'health_meter') and self.health_meter and not self.health_meter.isEmpty():
                    self.health_meter.hide()
                if hasattr(self, 'meter_glow') and self.meter_glow and not self.meter_glow.isEmpty():
                    self.meter_glow.hide()
                self.boss_icon.show()

        elif (cog_data['name'] in ["CEO"]):

            if self.skele_i < 6:
                if hasattr(self, 'health_meter') and self.health_meter and not self.health_meter.isEmpty():
                    self.health_meter.show()
                    self.health_meter.setColor(self.skele_meter_color)
                    self.head.find('**/ceo_sclera').setColor(0, 0, 0, 1.0)
                    self.head.find('**/ceo_eyes').setColor(self.skele_meter_color)
                if hasattr(self, 'meter_glow') and self.meter_glow and not self.meter_glow.isEmpty():
                    self.meter_glow.show()
                    self.meter_glow.setColor(self.skele_meter_color)
                self.boss_icon.hide()

            # Hide on index 6
            elif self.skele_i == 6:
                if hasattr(self, 'health_meter') and self.health_meter and not self.health_meter.isEmpty():
                    self.health_meter.hide()
                    self.head.find('**/ceo_sclera').clearColor()
                    self.head.find('**/ceo_eyes').clearColor()
                if hasattr(self, 'meter_glow') and self.meter_glow and not self.meter_glow.isEmpty():
                    self.meter_glow.hide()
                self.boss_icon.show()

        elif self.skele_i < 6:
            emblem_hp.show()
            glow.show()
            emblem_hp.setColor(self.skele_meter_color)
            glow.setColor(self.skele_meter_color)
            if self.store_emblem not in ["light", "none"]:
                self.iconbase.find(f'**/{self.store_emblem}').hide()

        elif self.skele_i == 6:
            emblem_hp.setColor(self.skele_meter_color)
            glow.setColor(self.skele_meter_color)
            if self.store_emblem is not "light":
                emblem_hp.hide()
                glow.hide()
                self.apply_emblem(self.store_emblem)

        self.skele_i += 1
        self.skele_i %= 7
        self.store_health_meter = True

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

            elif suitToggle == "ms":
                suit_paths = globals.SUIT_TEXTURE_PATH.get(cog_name)
                head_paths = globals.HEAD_TEXTURE_PATH.get(cog_name)
                self.it = (self.it + 1) % len(suit_paths)
                tx_head = loader.loadTexture("phase_9/maps/ttcc_ene_multislacker_static_hw.png")
                self.head.setTexture(tx_head, 1)

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

    def upload_texture(self, part, target):
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askopenfilename(
            title=f"Select {part} Texture",
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

            for node in target:
                node.setTexture(new_tex, 1)

            print(f"Applied new suit texture: {file_path}")

            if part == "Suit":
                if self.suit_type not in ["as", "bs", "cs"]:
                    self.store_suit_texture = panda_path
                else:
                    self.store_skelecog_texture = panda_path
            elif part == "Head":
                self.store_head_texture = panda_path

        except Exception as e:
            print(f"Failed to apply texture: {e}")

    def upload_suit_texture(self):
        suit_part = "Suit"
        if self.cog_data["cog"] in ["VP", "CFO", "CLO", "CEO"]:
            suit_target = [
                self.actor.find('**/Object')
            ]
        elif self.suit_type not in ["as", "bs", "cs"]:
            suit_target = [
                self.actor.find('**/body'),
                self.actor.find('**/necktie-s'),
                self.actor.find('**/necktie-w'),
                self.actor.find('**/bowtie'),
                self.actor.find('**/hands')
            ]
        else:
            suit_target = [
                self.actor.find('**/body'),
                self.actor.find('**/necktie-s'),
                self.actor.find('**/necktie-w'),
                self.actor.find('**/bowtie')
            ]
        self.upload_texture(suit_part, suit_target)

    def upload_head_texture(self):
        cog_data = globals.COG_DATA.get(self.current_cog, None)
        cog_name = cog_data["name"]
        if "ttcc_ene_rainmaker" in cog_name:
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Select Head Texture",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tga"), ("All Files", "*.*")]
            )

            if not file_path:
                print("Upload canceld")
                return
            try:
                panda_path = Filename.fromOsSpecific(file_path)
                panda_path.makeTrueCase()
                new_tex = loader.loadTexture(panda_path)

                if not new_tex:
                    print("faile to load teture")
                    return
                if self.head:
                    geomNode = self.head.find('**/head').node()
                    state1 = geomNode.getGeomState(1)
                    tex_attr1 = state1.getAttrib(TextureAttrib)

                    if tex_attr1:
                        for stage in tex_attr1.getOnStages():
                            if stage.getName() == "rainmaker":
                                new_state = state1.setAttrib(tex_attr1.addOnStage(stage, new_tex))
                                geomNode.setGeomState(1, new_state)
            except Exception as e:
                print("what")
            return

        elif "ttcc_ene_counterfit" in cog_name:
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Select Head Texture",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tga"), ("All Files", "*.*")]
            )

            if not file_path:
                print("Upload canceld")
                return
            try:
                panda_path = Filename.fromOsSpecific(file_path)
                panda_path.makeTrueCase()
                new_tex = loader.loadTexture(panda_path)

                if not new_tex:
                    print("faile to load teture")
                    return
                
                if self.head:
                    gn_path = self.head.find("**/+GeomNode")
                    
                    if not gn_path.isEmpty():
                        geomNode = gn_path.node()
                        
                        for i in range(geomNode.getNumGeoms()):
                            state = geomNode.getGeomState(i)
                            tex_attr = state.getAttrib(TextureAttrib)
                            
                            if tex_attr:
                                for stage in tex_attr.getOnStages():
                                    current_tex = tex_attr.getOnTexture(stage)
                                    if current_tex and "ttcc_ene_counterfit" in current_tex.getFilename().getBasename():
                                        new_state = state.setAttrib(tex_attr.addOnStage(stage, new_tex))
                                        geomNode.setGeomState(i, new_state)

            except Exception as e:
                print("what")
            return
        elif "ttcc_ene_firestarter" in cog_name:
            head_part = "Head"
            head_target = [
                self.head.find('**/Fire_Starter.001')
            ]
        else:
            head_part = "Head"
            head_target = [
                self.head
            ]
        self.upload_texture(head_part, head_target)
    
    def upload_additional_head_texture(self):
        cog_data = globals.COG_DATA.get(self.current_cog, None)
        cog_name = cog_data["name"]
        if "ttcc_ene_rainmaker" in cog_name:
            root = tk.Tk()
            root.withdraw()
            file_path = filedialog.askopenfilename(
                title="Select Hair Texture",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.tga"), ("All Files", "*.*")]
            )

            if not file_path:
                print("Upload canceled.")
                return

            try:
                panda_path = Filename.fromOsSpecific(file_path)
                panda_path.makeTrueCase()
                new_tex = loader.loadTexture(panda_path)
                
                if not new_tex: 
                    print("Failed to load texture.")
                    return

                if self.head:
                    geomNode = self.head.find("**/head").node()
                    
                    state0 = geomNode.getGeomState(0)
                    tex_attr0 = state0.getAttrib(TextureAttrib)
                    
                    if tex_attr0:
                        for stage in tex_attr0.getOnStages():
                            if stage.getName() == "ttcc_ene_rainmaker_hair":
                                new_state = state0.setAttrib(tex_attr0.addOnStage(stage, new_tex))
                                geomNode.setGeomState(0, new_state)
                                print(f"Applied Rainmaker Hair Texture: {file_path}")
            
            except Exception as e:
                print(f"Error applying Rainmaker hair: {e}")
            
            return
        target = []
        if "ttcc_ene_firestarter" in cog_name:
            if self.head:
                fire = self.head.find('**/fire_seq')
                if not fire.isEmpty():
                    target.append(fire)
        
        self.upload_texture("Additional Head", target)

    # Used for Suit Library
    def apply_suit_texture(self, texture_path):
        if self.actor:
            # Storing data for model function
            # if texture_path not in globals.SUIT_TEXTURES["Skelecog"].values():
            if self.suit_type not in ["as", "bs", "cs"]:
                self.store_suit_texture = texture_path
            else:
                self.store_skelecog_texture = texture_path

            texture = loader.loadTexture(texture_path)
            if self.suit_type not in ["erfit", "boss"]:
                suit_nodes = [
                    self.actor.find('**/body'),
                    self.actor.find('**/necktie-s'),
                    self.actor.find('**/necktie-w'),
                    self.actor.find('**/bowtie')
                ]
            else:
                suit_nodes = [self.actor.find('**/body')]
            if texture:
                for node in suit_nodes:
                    node.setTexture(texture, 1)
                # skelecog head
                if self.cog_data["head"] in globals.SKELECOG_HEAD_DICT and self.store_skelecog_texture is not None:
                    amongus = loader.loadTexture(self.store_skelecog_texture)
                    self.head.setTexture(amongus, 1)
                    self.store_head_texture = self.store_skelecog_texture

    def set_stored_vals(self):
        # Store Costume
        self.store_costume = self.is_costume_active
        # Store body animations
        self.store_body_loop = self.control_panel.loop_body_var.get()
        # Store head animations
        self.store_head_frame = self.control_panel.head_frame_slider.get()
        self.store_head_loop = self.control_panel.loop_head_var.get()

    def apply_suit_model(self, suit_model_key):
        if self.actor:
            self.set_stored_vals()
            # Rebuild cog
            self.build_cog(suit_model_key, False)
            self.update_cog_attributes(suit_model_key)

    def reset_stored_vals(self):
        # Reset the stored values
        self.store_suit_texture = None
        self.store_skelecog_texture = None
        self.store_head_texture = None
        self.store_necktie = "(Default)"
        self.it, self.it2, self.it_l, self.it_m, self.it_r = 0, 0, 0, 0, 0
        self.skele_i = 0
        self.skele_color_index = 0
        self.store_virtualize = False
        self.store_health_meter = False
        self.store_emblem = globals.COG_DATA[self.current_cog]["emblem"]
        self.store_head_hpr = globals.HEAD_HPR_DEFAULTS.copy()
        self.control_panel.reset_head_hpr()
        # Stored unique toggles
        self.store_unique_suit_toggle = False
        self.store_cycle_slot_l = False
        self.store_cycle_slot_m = False
        self.store_cycle_slot_r = False
        # Body anim
        self.store_body_anim = None
        self.store_body_frame = 0
        self.store_body_adjusted = False
        self.store_body_playing = False
        # Head anim
        self.store_head_anim = None
        self.store_head_frame = 0
        self.store_head_adjusted = False
        self.store_head_playing = False
        # Scale
        self.control_panel.reset_flatten()
        self.store_flatten_body = {
            "Sx": self.cog_data.get("scale", 1.0),
            "Sy": self.cog_data.get("scale", 1.0),
            "Sz": self.cog_data.get("scale", 1.0),
        }
        self.store_flatten_head = {
            "Sx": self.cog_data.get("headSize", 1.0),
            "Sy": self.cog_data.get("headSize", 1.0),
            "Sz": self.cog_data.get("headSize", 1.0),
        }
        # Stored Colors
        self.store_body_hex_color = None
        self.store_body_color = False
        self.store_head_hex_color = None
        self.store_head_color = False
        self.store_hand_hex_color = None
        self.store_hand_color = False
        # Stored Props
        self.current_prop1 = "zero"
        self.current_prop2 = "zero"
        self.store_prop1 = "zero"
        self.store_prop2 = "zero"
        self.store_prop1_hpr = globals.HEAD_HPR_DEFAULTS.copy()
        self.store_prop2_hpr = globals.HEAD_HPR_DEFAULTS.copy()
        self.store_custom_model = None
        self.store_custom_model_hpr = globals.HEAD_HPR_DEFAULTS.copy()

    def update_cog_attributes(self, suit_model_key=None, costume_check=False):
        autoplay = self.control_panel.is_autoplay_var.get()

        # -- NECKTIE LOGIC -- #
        if self.store_necktie != "(Default)":
            self.set_necktie(self.store_necktie)
            self.control_panel.selected_tie_var.set(self.store_necktie)

        # -- HALLOWEEN COSTUME LOGIC -- #
        if self.store_costume and not costume_check:
            self.toggle_costume(False)
            self.control_panel.is_costume_var.set(True)

        # -- HEAD TEXTURE LOGIC -- #
        if self.store_head_texture is not None:
            head_tex = loader.loadTexture(self.store_head_texture)
            self.head.setTexture(head_tex, 1)

        # -- SUIT TEXTURE LOGIC -- #
        # - Non-Skelecog -#
        if self.cog_data["suit"] not in ("as", "bs", "cs"):
            # skelecog body model #
            if suit_model_key in ("as", "bs", "cs"):
                if self.store_skelecog_texture is not None:  # If skelecog texture already stored
                    self.apply_suit_texture(self.store_skelecog_texture)
                else:  # Else default to normal texture
                    self.apply_suit_texture(globals.DEPT_SKELE_SUIT_TEX_MAP[self.cog_data["dept"]])
            # if suit texture is already stored #
            elif self.store_suit_texture is not None:
                self.apply_suit_texture(self.store_suit_texture)
        # - Skelecog -#
        else:
            # normal model #
            if suit_model_key not in ("as", "bs", "cs"):
                # if suit texture is already stored
                if self.store_suit_texture is not None:
                    self.apply_suit_texture(self.store_suit_texture)
                else:
                    self.apply_suit_texture(globals.DEPT_SUIT_TEX_MAP[self.cog_data["dept"]])
                # Skelecog using suitB closed collar model
                if suit_model_key in ["bc"]:
                    hand_tex = loader.loadTexture(globals.DEPT_SUIT_TEX_MAP[self.cog_data["dept"]])
                    self.actor.find('**/hands').setTexture(hand_tex, 1)
            # skelecog model #
            elif self.store_skelecog_texture is not None:
                self.apply_suit_texture(self.store_skelecog_texture)

        # -- VIRTUALIZED LOGIC -- #
        if self.store_virtualize:
            self.skele_color_index = (self.skele_color_index - 1) % len(globals.SKELECOG_METER_COLORS)
            self.toggle_virtualize()

        # -- EMBLEM LOGIC -- #
        if self.store_emblem is not None:
            self.apply_emblem(self.store_emblem)

        # -- HEALTH METER LOGIC -- #
        if self.store_health_meter:
            self.skele_i -= 1
            self.skele_i %= 7
            self.toggle_skele_meter_color()

        # -- BODY ANIMATION LOGIC -- #
        if self.store_body_anim is not None:
            self.set_animation(self.store_body_anim)
            self.control_panel.loop_body_var.set(self.store_body_loop)
            self.control_panel.body_frame_slider.set(self.store_body_frame)
            # Pose the cog to frame
            self.actor.pose(self.store_body_anim, self.store_body_frame)

            if not self.store_body_adjusted:
                # Bugfix: if autoplay is off and you last pressed the play button, the animation will play
                if not autoplay and self.store_body_playing:
                    self.play_body_animation()
                else:
                    self.check_body_autoplay()

        # -- HEAD ANIMATION LOGIC -- #
        if self.store_head_anim is not None:
            self.set_head_animation(self.store_head_anim)
            self.control_panel.loop_head_var.set(self.store_head_loop)
            self.control_panel.head_frame_slider.set(self.store_head_frame)
            # Pose the head to frame
            self.head.pose(self.store_head_anim, self.store_head_frame)

            if not self.store_head_adjusted:
                # Bugfix: if autoplay is off and you last pressed the play button, the animation will play
                if not autoplay and self.store_head_playing:
                    self.play_head_animation()
                else:
                    self.check_head_autoplay()

        # -- HEAD HPR LOGIC -- #
        for axis, value in self.store_head_hpr.items():
            self.update_head_hpr(axis, value)
        self.control_panel.update_head_hpr_sliders()

        # -- SET SCALE LOGIC -- #
        for axis, value in self.store_flatten_body.items():
            self.update_flatten_body(axis, value)
        for axis, value in self.store_flatten_head.items():
            self.update_flatten_head(axis, value)

        # -- SET COLOR LOGIC -- #
        if self.store_body_color:
            self.apply_body_colorscale(self.store_body_hex_color)
        if self.store_head_color:
            self.apply_head_color(self.store_head_hex_color)
        if self.store_hand_color:
            self.apply_hand_color(self.store_hand_hex_color)

        # -- UNIQUE SUIT TOGGLE LOGIC -- #
        if self.store_unique_suit_toggle:
            self.toggle_unique_suit(False)

        # -- DUCK SHUFFLER SLOT TOGGLE LOGIC -- #
        if self.current_cog == "Duck Shuffler":
            if self.store_cycle_slot_l:
                self.cycle_slot_l(False)
            if self.store_cycle_slot_m:
                self.cycle_slot_m(False)
            if self.store_cycle_slot_r:
                self.cycle_slot_r(False)

        # -- UPLOAD ACCESSORY LOGIC -- #
        if self.store_custom_model is not None:
            self.custom_model = loader.loadModel(self.store_custom_model)
            self.load_custom_model()

        for axis, value in self.store_custom_model_hpr.items():
            self.update_custom_model_hpr(axis, value)

        # -- PROP LOGIC -- #
        self.load_stored_props()

    def load_stored_props(self):
        # Prop 1
        if self.store_prop1 != "zero":                        # Load prop 1
            self.set_prop(self.store_prop1, False)

        for axis, value in self.store_prop1_hpr.items():        # Update HPR
            self.update_prop_hpr(axis, value)

        # Prop 2
        if self.store_prop2 != "zero":                        # Load prop 2
            self.set_prop2(self.store_prop2, False)

        for axis, value in self.store_prop2_hpr.items():        # Update HPR
            self.update_prop2_hpr(axis, value)

    def apply_emblem(self, emblem_name):
        if self.actor:
            self.store_emblem = emblem_name
            emblem_map = globals.EMBLEM_MAP
            self.iconbase.show()

            # Hide all the emblems
            for emblem in list(emblem_map)[:-2]:
                current_emblem = globals.EMBLEM_MAP.get(emblem)
                self.iconbase.find(f'**/{current_emblem}').hide()
                if self.actor.find('**/emblem_healthmeter'):
                    self.actor.find('**/emblem_healthmeter').show()
                    self.actor.find('**/glow').show()

            # Department Emblems
            if emblem_name not in ["light", "none"]:
                # Hide hp glow if it's active
                self.iconbase.find('**/emblem_hp').hide()
                self.iconbase.find('**/glow').hide()
                # Show the picked emblem
                self.iconbase.find(f'**/{emblem_name}').show()

            # Light
            elif emblem_name is "light":
                self.iconbase.find('**/emblem_hp').show()
                self.iconbase.find('**/glow').show()
                if self.skele_i > 0:
                    self.skele_i -= 1
                    self.skele_i %= 6
                    self.toggle_skele_meter_color()

            # None
            else:
                self.iconbase.find('**/emblem_hp').hide()
                self.iconbase.find('**/glow').hide()
                if self.actor.find('**/emblem_healthmeter'):
                    self.actor.find('**/emblem_healthmeter').hide()
                    self.actor.find('**/glow').hide()
                self.iconbase.hide()

    def update_custom_model_hpr(self, axis, value):
        """Callback for the custom model's HPR/XYZ/Scale sliders."""
        if self.custom_model and not self.custom_model.isEmpty():
            self.set_POSHPR(self.custom_model, axis, value)
            self.store_custom_model_hpr[axis] = value

    def upload_custom_model(self):
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
                self.store_custom_model = None

            self.custom_model = loader.loadModel(panda_path)
            self.store_custom_model = panda_path
            if not self.custom_model:
                print(f"Error: Failed to load model {panda_path}")
                return

            self.load_custom_model()
            self.control_panel.reset_prop_sliders(self.control_panel.custom_model_vars)
            for axis, value in globals.HEAD_HPR_DEFAULTS.items():
                self.update_custom_model_hpr(axis, value)

            print(f"Loaded custom model: {file_path}")

        except Exception as e:
            print(f"Failed to load custom model: {e}")

    def load_custom_model(self):
        head_joint = self.actor.find('**/joint_head')
        if not head_joint.isEmpty():
            self.custom_model.reparentTo(head_joint)
        else:
            self.custom_model.reparentTo(self.actor)  # Fallback

        self.control_panel.show_custom_model_tab(True)

    def update_frame(self, task):
        if not self.actor or self.current_animation == "zero":
            print("Cannot take screenshot frames: No actor or animation selected.")
            if self.bool:
                self.setBackgroundColor(0, 0, 0)
            else:
                self.setBackgroundColor(self.background_color)
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
                self.setBackgroundColor(self.background_color)

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
        if self.current_animation != "zero":
            frame = int(round(float(frame_value)))
            if frame != 0:
                self.store_body_frame = frame
                self.store_body_adjusted = True
                self.store_body_playing = False

            # Boss Cog Behavior
            if self.cog_data.get("cog_type") == "boss" and hasattr(self, "boss_parts"):
                for part_name, part_actor in self.boss_parts.items():
                    if part_name == "head": continue
                    if isinstance(part_actor, Actor):
                        part_actor.pose(self.current_animation, frame)

            # Standard Cog Behavior
            elif self.actor:
                self.actor.pose(self.current_animation, frame)

    def update_head_pose(self, frame_value):
        if self.current_head_animation != "zero" and self.head:
            frame = int(round(float(frame_value)))
            if frame != 0:
                self.store_head_frame = frame
                self.store_head_adjusted = True
                self.store_head_playing = False
            self.head.pose(self.current_head_animation, frame)

    def get_head_hpr_default_values(self):
        defaults = {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "h": 0.0,
            "p": 0.0,
            "r": 0.0,
            "scale": 1.0
        }
        cog = globals.COG_DATA.get(self.current_cog, {})

        head_pos_map = {
            "headPos": "z",
            "headPosY": "y",
            "headPosH": "h",
            "headPosP": "p",
            "headSize": "scale"
        }
        for pos_key, pos_type in head_pos_map.items():
            value = cog.get(pos_key)
            if value is not None:
                defaults[pos_type] = value

        globals.HEAD_HPR_DEFAULTS = defaults.copy()

        return defaults


app = CogViewer()
app.render.setAntialias(AntialiasAttrib.MMultisample)
app.run()
