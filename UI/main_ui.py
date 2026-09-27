import copy
import json
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, scrolledtext, simpledialog, ttk
import webbrowser

from tkcalendar import DateEntry

from Dataloader import load_json
from website_maker import build_website_content


class Application(tk.Tk):

    def __init__(self):
        super().__init__()

        # Threading and Queue Setup
        self.data_queue = queue.Queue()
        self.is_running = True

        # Setup & Colors
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        bottom_margin = 20
        color_palette = {
            "background": "#35414d",
            "light_foreground": "#ffffff",
            "dark_foreground": "#000000",
            "button_bg": "#4a5a6a",
            "textbox_bg": "#EBEBEB",
            "panel_bg": "#2b353e",
        }
        self.color_palette = color_palette

        # Data Stores
        self.TIMELINE = []
        self.current_file_path = None
        self.selected_index = None  # Tracks which row is currently selected/editing
        self._is_loading_data = False  # Prevent loop updates during UI population

        self.title("Timeline Maker")
        self.geometry(f"{screen_width}x{screen_height}")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # UI Layout Calculations
        left_frame_width = screen_width // 2
        right_frame_width = screen_width // 2
        table_view_height = int(screen_height * 0.35)
        content_editor_height = int(screen_height * 0.65)

        # Menu
        self.menubar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label="New", command=self.file_new)
        self.file_menu.add_command(label="Open", command=self.load_data)
        self.file_menu.add_command(label="Save", command=self.file_save)
        self.file_menu.add_command(label="Save as", command=self.file_save_as)

        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.config(menu=self.menubar)

        # Main Split Frames
        self.left_frame = tk.Frame(self, width=left_frame_width, height=screen_height)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.left_frame.pack_propagate(False)

        self.right_frame = tk.Frame(
            self, width=right_frame_width, height=screen_height, bg=color_palette["panel_bg"]
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.right_frame.pack_propagate(False)

        # --- Table View Frame (Top Left) ---
        self.table_view_frame = tk.Frame(
            self.left_frame, width=left_frame_width, height=table_view_height
        )
        self.table_view_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        self.table_view_frame.pack_propagate(False)

        tree_columns = ("row_num", "headline", "text_body", "start_date", "end_date", "is_title")
        self.table_view_tree = ttk.Treeview(
            self.table_view_frame, columns=tree_columns, show="headings"
        )

        self.table_view_tree.heading("row_num", text="#")
        self.table_view_tree.column("row_num", width=35, anchor="center")

        self.table_view_tree.heading("headline", text="Headline")
        self.table_view_tree.column("headline", width=140, anchor="w")

        self.table_view_tree.heading("text_body", text="Text Body")
        self.table_view_tree.column("text_body", width=220, anchor="w")

        self.table_view_tree.heading("start_date", text="Start Date")
        self.table_view_tree.column("start_date", width=90, anchor="center")

        self.table_view_tree.heading("end_date", text="End Date")
        self.table_view_tree.column("end_date", width=90, anchor="center")

        self.table_view_tree.heading("is_title", text="Title?")
        self.table_view_tree.column("is_title", width=50, anchor="center")

        self.table_view_tree.bind("<<TreeviewSelect>>", self.on_table_row_select)
        self.table_view_tree.bind("<Delete>", self.delete_selected)
        self.table_view_tree.bind("<BackSpace>", self.delete_selected)
        self.table_view_tree.bind("<Alt-Up>", self.move_selected_up)
        self.table_view_tree.bind("<Alt-Down>", self.move_selected_down)

        v_scroll = ttk.Scrollbar(
            self.table_view_frame, orient="vertical", command=self.table_view_tree.yview
        )
        h_scroll = ttk.Scrollbar(
            self.table_view_frame, orient="horizontal", command=self.table_view_tree.xview
        )
        self.table_view_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.table_view_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Content Editor Frame (Bottom Left) ---
        self.content_editor_frame = tk.Frame(
            self.left_frame,
            width=left_frame_width,
            height=content_editor_height,
            padx=15,
            pady=15,
            bg=color_palette["background"],
        )
        self.content_editor_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.content_editor_frame.pack_propagate(False)

        self.content_editor_left_frame = tk.Frame(
            self.content_editor_frame, bg=color_palette["background"]
        )
        self.content_editor_left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.content_editor_right_frame = tk.Frame(
            self.content_editor_frame, bg=color_palette["background"]
        )
        self.content_editor_right_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=False)

        self.status_lbl = tk.Label(
            self.content_editor_left_frame,
            text="Select a row from the list above to edit its content",
            font=("Arial", 11, "bold"),
            bg=color_palette["background"],
            fg="#ffffff",
        )
        self.status_lbl.pack(side=tk.TOP, anchor="w", pady=(0, 10))

        # Title Event Checkbox
        self.is_title_var = tk.BooleanVar(value=False)
        self.title_chk = tk.Checkbutton(
            self.content_editor_left_frame,
            text="Set as Timeline Title Event (Forces event to show first)",
            variable=self.is_title_var,
            onvalue=True,
            offvalue=False,
            bg=color_palette["background"],
            fg="#ffffff",
            selectcolor=color_palette["button_bg"],
            activebackground=color_palette["background"],
            activeforeground="#ffffff",
            command=self.on_input_change,
            takefocus=False,
        )
        self.title_chk.pack(side=tk.TOP, anchor="w", pady=(0, 10))

        # Headline
        self.headline_lbl = tk.Label(
            self.content_editor_left_frame,
            text="Headline:",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.headline_lbl.pack(side=tk.TOP, anchor="w")
        self.headline_txtbox = scrolledtext.ScrolledText(
            self.content_editor_left_frame,
            height=2,
            width=50,
            wrap=tk.WORD,
            bg=color_palette["textbox_bg"],
            fg=color_palette["dark_foreground"],
            undo=True,
        )
        self.headline_txtbox.pack(side=tk.TOP, anchor="w", pady=(0, bottom_margin))
        self.headline_txtbox.bind("<KeyRelease>", self.on_input_change)

        # Text Body
        self.text_body_lbl = tk.Label(
            self.content_editor_left_frame,
            text="Text Body:",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.text_body_lbl.pack(side=tk.TOP, anchor="w")
        self.text_body_txtbox = scrolledtext.ScrolledText(
            self.content_editor_left_frame,
            height=8,
            width=50,
            wrap=tk.WORD,
            bg=color_palette["textbox_bg"],
            fg=color_palette["dark_foreground"],
            undo=True,
        )
        self.text_body_txtbox.pack(side=tk.TOP, anchor="w", pady=(0, bottom_margin))
        self.text_body_txtbox.bind("<KeyRelease>", self.on_input_change)

        # Dates
        self.date_frame = tk.Frame(self.content_editor_left_frame, bg=color_palette["background"])
        self.date_frame.pack(side=tk.TOP, anchor="w", fill=tk.X)

        self.start_date_lbl = tk.Label(
            self.date_frame,
            text="Start Date:",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.start_date_lbl.pack(side=tk.LEFT, anchor="w", padx=(0, 5))

        self.start_date_picker = DateEntry(
            self.date_frame,
            width=12,
            background=color_palette["button_bg"],
            foreground="white",
            bordercolor=color_palette["background"],
            headersbackground=color_palette["button_bg"],
            headersforeground="white",
            date_pattern="yyyy-mm-dd",
        )
        self.start_date_picker.pack(side=tk.LEFT, anchor="w", pady=(0, bottom_margin))
        self.start_date_picker.bind("<KeyRelease>", self.on_input_change)
        self.start_date_picker.bind("<<DateEntrySelected>>", self.on_input_change)

        self.end_date_lbl = tk.Label(
            self.date_frame,
            text="End Date:",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.end_date_lbl.pack(side=tk.LEFT, anchor="w", padx=(20, 5))

        self.end_date_picker = DateEntry(
            self.date_frame,
            width=12,
            background=color_palette["button_bg"],
            foreground="white",
            bordercolor=color_palette["background"],
            headersbackground=color_palette["button_bg"],
            headersforeground="white",
            date_pattern="yyyy-mm-dd",
        )
        self.end_date_picker.pack(side=tk.LEFT, anchor="w", pady=(0, bottom_margin))
        self.end_date_picker.bind("<KeyRelease>", self.on_input_change)
        self.end_date_picker.bind("<<DateEntrySelected>>", self.on_input_change)

        # Action Buttons
        self.add_rows_btn = tk.Button(
            self.content_editor_right_frame,
            text="➕ Add Rows...",
            width=25,
            height=2,
            bg=color_palette["button_bg"],
            fg=color_palette["light_foreground"],
            command=self.add_empty_rows,
            takefocus=False,
        )
        self.add_rows_btn.pack(side=tk.TOP, padx=10, pady=(15, 10))

        self.move_up_btn = tk.Button(
            self.content_editor_right_frame,
            text="⬆️ Move Up",
            width=25,
            height=2,
            bg=color_palette["button_bg"],
            fg=color_palette["light_foreground"],
            command=self.move_selected_up,
            takefocus=False,
        )
        self.move_up_btn.pack(side=tk.TOP, padx=10, pady=(0, 10))

        self.move_down_btn = tk.Button(
            self.content_editor_right_frame,
            text="⬇️ Move Down",
            width=25,
            height=2,
            bg=color_palette["button_bg"],
            fg=color_palette["light_foreground"],
            command=self.move_selected_down,
            takefocus=False,
        )
        self.move_down_btn.pack(side=tk.TOP, padx=10, pady=(0, 10))

        self.delete_btn = tk.Button(
            self.content_editor_right_frame,
            text="❌ Delete Selected Row",
            width=25,
            height=2,
            bg="#8b0000",
            fg=color_palette["light_foreground"],
            command=self.delete_selected,
            takefocus=False,
        )
        self.delete_btn.pack(side=tk.TOP, padx=10, pady=(0, 10))

        self.clear_selection_btn = tk.Button(
            self.content_editor_right_frame,
            text="Deselect / Clear",
            width=25,
            height=2,
            bg=color_palette["button_bg"],
            fg=color_palette["light_foreground"],
            command=self.deselect_and_clear,
            takefocus=False,
        )
        self.clear_selection_btn.pack(side=tk.TOP, padx=10, pady=(0, 15))

        self.buildwebsite_btn = tk.Button(
            self.content_editor_right_frame,
            text="Build Website & Open Browser",
            width=25,
            height=2,
            bg=color_palette["button_bg"],
            fg=color_palette["light_foreground"],
            command=self.build_website,
            takefocus=False,
        )
        self.buildwebsite_btn.pack(side=tk.TOP, padx=10, pady=(0, 15))

        # --- Build Right Frame Style Panel ---
        self._build_style_panel()

        # Initial Setup
        self.add_empty_rows(10)
        self.toggle_editor_state(enabled=False)
        self.check_queue()

    def _build_style_panel(self):
        """Creates embedded style controls in the right panel."""
        style_frame = tk.Frame(self.right_frame, bg=self.color_palette["panel_bg"], padx=20, pady=20)
        style_frame.pack(fill=tk.BOTH, expand=True)

        header = tk.Label(
            style_frame,
            text="Row Style & Media Settings",
            font=("Arial", 14, "bold"),
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
        )
        header.pack(anchor="w", pady=(0, 15))

        # --- Background Settings ---
        bg_group = tk.LabelFrame(
            style_frame,
            text="Background & Block Colors",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
            padx=10,
            pady=10,
        )
        bg_group.pack(fill=tk.X, pady=(0, 15))

        self.bg_type_var = tk.StringVar(value="color")

        rb_color = tk.Radiobutton(
            bg_group,
            text="Solid Outer BG Color",
            variable=self.bg_type_var,
            value="color",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
            selectcolor=self.color_palette["button_bg"],
            command=self.on_style_input_change,
            takefocus=False,
        )
        rb_color.pack(anchor="w")

        color_sub_frame = tk.Frame(bg_group, bg=self.color_palette["panel_bg"])
        color_sub_frame.pack(fill=tk.X, padx=20, pady=5)

        self.bg_color_btn = tk.Button(
            color_sub_frame,
            text="Pick Outer BG Color",
            command=self.pick_bg_color,
            bg=self.color_palette["button_bg"],
            fg=self.color_palette["light_foreground"],
            takefocus=False,
        )
        self.bg_color_btn.pack(side=tk.LEFT)

        self.bg_color_preview = tk.Label(
            color_sub_frame, text="      ", bg="#ffffff", relief="sunken"
        )
        self.bg_color_preview.pack(side=tk.LEFT, padx=10)

        # Block Background Color Picker (Text container)
        block_sub_frame = tk.Frame(bg_group, bg=self.color_palette["panel_bg"])
        block_sub_frame.pack(fill=tk.X, padx=20, pady=5)

        self.block_color_btn = tk.Button(
            block_sub_frame,
            text="Pick Text Block BG Color",
            command=self.pick_block_color,
            bg=self.color_palette["button_bg"],
            fg=self.color_palette["light_foreground"],
            takefocus=False,
        )
        self.block_color_btn.pack(side=tk.LEFT)

        self.block_color_preview = tk.Label(
            block_sub_frame, text="      ", bg="#ffffff", relief="sunken"
        )
        self.block_color_preview.pack(side=tk.LEFT, padx=10)

        self.opacity_label = tk.Label(
            block_sub_frame,
            text="Block Opacity: 80%",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
        )
        self.opacity_label.pack(side="top", anchor="w", padx=5, pady=2)

        self.opacity_slider = tk.Scale(
            block_sub_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            resolution=1,
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
            command=self.on_opacity_slider_change,
        )
        self.opacity_slider.set(80)
        self.opacity_slider.pack(fill="x", expand=True, padx=5, pady=5)

        rb_image = tk.Radiobutton(
            bg_group,
            text="Background Image",
            variable=self.bg_type_var,
            value="image",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
            selectcolor=self.color_palette["button_bg"],
            command=self.on_style_input_change,
            takefocus=False,
        )
        rb_image.pack(anchor="w", pady=(10, 0))

        img_sub_frame = tk.Frame(bg_group, bg=self.color_palette["panel_bg"])
        img_sub_frame.pack(fill=tk.X, padx=20, pady=5)

        self.bg_image_entry = tk.Entry(img_sub_frame, width=30)
        self.bg_image_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.bg_image_entry.bind("<KeyRelease>", self.on_style_input_change)

        btn_browse_bg = tk.Button(
            img_sub_frame,
            text="Browse...",
            command=self.browse_bg_image,
            bg=self.color_palette["button_bg"],
            fg=self.color_palette["light_foreground"],
            takefocus=False,
        )
        btn_browse_bg.pack(side=tk.LEFT, padx=(5, 0))

        # --- BG Image Overlay Darkness Slider ---
        bg_overlay_frame = tk.Frame(bg_group, bg=self.color_palette["panel_bg"])
        bg_overlay_frame.pack(fill=tk.X, padx=20, pady=5)

        self.bg_overlay_label = tk.Label(
            bg_overlay_frame,
            text="BG Image Darkness Overlay: 40%",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
        )
        self.bg_overlay_label.pack(side="top", anchor="w", padx=5, pady=2)

        self.bg_overlay_slider = tk.Scale(
            bg_overlay_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            resolution=1,
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
            command=self.on_bg_overlay_slider_change,
        )
        self.bg_overlay_slider.set(40)
        self.bg_overlay_slider.pack(fill="x", expand=True, padx=5, pady=5)

        # --- Media & Captions ---
        media_group = tk.LabelFrame(
            style_frame,
            text="Media & Attribution",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
            padx=10,
            pady=10,
        )
        media_group.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            media_group,
            text="Media File (Image/Video):",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
        ).pack(anchor="w")

        media_sub_frame = tk.Frame(media_group, bg=self.color_palette["panel_bg"])
        media_sub_frame.pack(fill=tk.X, pady=(0, 10))

        self.media_path_entry = tk.Entry(media_sub_frame, width=30)
        self.media_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.media_path_entry.bind("<KeyRelease>", self.on_style_input_change)

        btn_browse_media = tk.Button(
            media_sub_frame,
            text="Browse...",
            command=self.browse_media_image,
            bg=self.color_palette["button_bg"],
            fg=self.color_palette["light_foreground"],
            takefocus=False,
        )
        btn_browse_media.pack(side=tk.LEFT, padx=(5, 0))

        tk.Label(
            media_group,
            text="Caption:",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
        ).pack(anchor="w")
        self.caption_entry = tk.Entry(media_group, width=40)
        self.caption_entry.pack(fill=tk.X, pady=(0, 10))
        self.caption_entry.bind("<KeyRelease>", self.on_style_input_change)

        tk.Label(
            media_group,
            text="Source / Credit:",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
        ).pack(anchor="w")
        self.source_entry = tk.Entry(media_group, width=40)
        self.source_entry.pack(fill=tk.X)
        self.source_entry.bind("<KeyRelease>", self.on_style_input_change)

        # --- Font Options ---
        font_group = tk.LabelFrame(
            style_frame,
            text="Typography",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
            padx=10,
            pady=10,
        )
        font_group.pack(fill=tk.X)

        fonts = ["Arial", "Courier New", "Georgia", "Times New Roman", "Trebuchet MS", "Verdana"]

        # Heading Font
        h_frame = tk.Frame(font_group, bg=self.color_palette["panel_bg"])
        h_frame.pack(fill=tk.X, pady=2)
        tk.Label(
            h_frame,
            text="Heading:",
            width=10,
            anchor="w",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
        ).pack(side=tk.LEFT)
        self.h_font_cb = ttk.Combobox(h_frame, values=fonts, width=12, state="readonly")
        self.h_font_cb.pack(side=tk.LEFT, padx=2)
        self.h_font_cb.bind("<<ComboboxSelected>>", self.on_style_input_change)

        self.h_size_sp = tk.Spinbox(h_frame, from_=8, to=72, width=4, command=self.on_style_input_change)
        self.h_size_sp.pack(side=tk.LEFT, padx=2)
        self.h_size_sp.bind("<KeyRelease>", self.on_style_input_change)

        self.h_color_btn = tk.Button(
            h_frame,
            text="Color",
            command=self.pick_h_color,
            bg=self.color_palette["button_bg"],
            fg=self.color_palette["light_foreground"],
            takefocus=False,
        )
        self.h_color_btn.pack(side=tk.LEFT, padx=2)
        self.h_color_preview = tk.Label(h_frame, text="  ", bg="#ffffff", relief="sunken")
        self.h_color_preview.pack(side=tk.LEFT, padx=2)

        # Body Font
        b_frame = tk.Frame(font_group, bg=self.color_palette["panel_bg"])
        b_frame.pack(fill=tk.X, pady=2)
        tk.Label(
            b_frame,
            text="Body:",
            width=10,
            anchor="w",
            bg=self.color_palette["panel_bg"],
            fg=self.color_palette["light_foreground"],
        ).pack(side=tk.LEFT)
        self.b_font_cb = ttk.Combobox(b_frame, values=fonts, width=12, state="readonly")
        self.b_font_cb.pack(side=tk.LEFT, padx=2)
        self.b_font_cb.bind("<<ComboboxSelected>>", self.on_style_input_change)

        self.b_size_sp = tk.Spinbox(b_frame, from_=8, to=72, width=4, command=self.on_style_input_change)
        self.b_size_sp.pack(side=tk.LEFT, padx=2)
        self.b_size_sp.bind("<KeyRelease>", self.on_style_input_change)

        self.b_color_btn = tk.Button(
            b_frame,
            text="Color",
            command=self.pick_b_color,
            bg=self.color_palette["button_bg"],
            fg=self.color_palette["light_foreground"],
            takefocus=False,
        )
        self.b_color_btn.pack(side=tk.LEFT, padx=2)
        self.b_color_preview = tk.Label(b_frame, text="  ", bg="#cccccc", relief="sunken")
        self.b_color_preview.pack(side=tk.LEFT, padx=2)

    # --- Style Event Callbacks & Pickers ---
    def pick_bg_color(self):
        color = colorchooser.askcolor(title="Choose Background Color")
        if color[1]:
            self.bg_color_preview.config(bg=color[1])
            self.on_style_input_change()

    def pick_block_color(self):
        color = colorchooser.askcolor(title="Choose Content Block Background Color")
        if color[1]:
            self.block_color_preview.config(bg=color[1])
            self.on_style_input_change()

    def pick_h_color(self):
        color = colorchooser.askcolor(title="Choose Heading Color")
        if color[1]:
            self.h_color_preview.config(bg=color[1])
            self.on_style_input_change()

    def pick_b_color(self):
        color = colorchooser.askcolor(title="Choose Body Color")
        if color[1]:
            self.b_color_preview.config(bg=color[1])
            self.on_style_input_change()

    def browse_bg_image(self):
        filename = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")],
        )
        if filename:
            self.bg_image_entry.delete(0, tk.END)
            self.bg_image_entry.insert(0, filename)
            self.on_style_input_change()

    def browse_media_image(self):
        filename = filedialog.askopenfilename(
            title="Select Media File",
            filetypes=[("Media Files", "*.png *.jpg *.jpeg *.gif *.mp4")],
        )
        if filename:
            self.media_path_entry.delete(0, tk.END)
            self.media_path_entry.insert(0, filename)
            self.on_style_input_change()

    def get_default_style_data(self):
        """Return default styling dictionary for slides/items."""
        return {
            "bg_type": "color",
            "bg_color": "#1a1a1a",
            "bg_image_path": "",
            "bg_image_overlay": 0.40,
            "media_image_path": "",
            "caption": "",
            "source": "",
            "block_color": "#000000",
            "block_opacity": 0.80,
            "heading_font": "Arial",
            "heading_size": 24,
            "heading_color": "#ffffff",
            "body_font": "Arial",
            "body_size": 14,
            "body_color": "#cccccc",
        }

    # Alias helper for backward compatibility
    def get_default_style(self):
        return self.get_default_style_data()

    def on_opacity_slider_change(self, val):
        """Callback triggered whenever the content block transparency slider moves."""
        try:
            val_int = int(float(val))
        except (ValueError, TypeError):
            val_int = 80

        opacity_float = round(val_int / 100.0, 2)

        if hasattr(self, "opacity_label") and self.opacity_label:
            self.opacity_label.config(text=f"Block Opacity: {val_int}%")

        if self.selected_index is not None and 0 <= self.selected_index < len(self.TIMELINE):
            selected_slide = self.TIMELINE[self.selected_index]
            if "style_data" not in selected_slide:
                selected_slide["style_data"] = self.get_default_style_data()

            selected_slide["style_data"]["block_opacity"] = opacity_float
            selected_slide["style_data"]["block_color"] = self.block_color_preview.cget("bg")

    def on_bg_overlay_slider_change(self, val):
        """Callback triggered whenever the background image overlay slider moves."""
        try:
            val_int = int(float(val))
        except (ValueError, TypeError):
            val_int = 40

        overlay_float = round(val_int / 100.0, 2)

        if hasattr(self, "bg_overlay_label") and self.bg_overlay_label:
            self.bg_overlay_label.config(text=f"BG Image Darkness Overlay: {val_int}%")

        if self.selected_index is not None and 0 <= self.selected_index < len(self.TIMELINE):
            selected_slide = self.TIMELINE[self.selected_index]
            if "style_data" not in selected_slide:
                selected_slide["style_data"] = self.get_default_style_data()

            selected_slide["style_data"]["bg_image_overlay"] = overlay_float

    def add_empty_rows(self, count=None):
        if count is None:
            count = simpledialog.askinteger(
                "Add Rows",
                "How many rows would you like to add?",
                parent=self,
                initialvalue=5,
                minvalue=1,
                maxvalue=100,
            )
            if count is None:
                return

        start_num = len(self.TIMELINE)
        for i in range(count):
            row_idx = start_num + i
            empty_entry = {
                "headline": "",
                "text_body": "",
                "start_date": "",
                "end_date": "",
                "is_title": False,
                "style_data": self.get_default_style_data(),
            }
            self.TIMELINE.append(empty_entry)

            values = (f"#{row_idx + 1}", "", "", "", "", "")
            self.table_view_tree.insert("", tk.END, iid=str(row_idx), values=values)

    def update_preview(self, index_path):
        """Opens the generated website in the default web browser."""
        file_url = f"file:///{os.path.abspath(index_path).replace('\\', '/')}"
        webbrowser.open(file_url)

    def on_table_row_select(self, event):
        selected = self.table_view_tree.selection()
        if not selected:
            return

        self._is_loading_data = True
        idx = int(selected[0])
        self.selected_index = idx
        entry = self.TIMELINE[idx]

        self.status_lbl.config(text=f"Editing Row #{idx + 1}", fg="#90ee90")
        self.toggle_editor_state(enabled=True)

        self.is_title_var.set(entry.get("is_title", False))
        self.headline_txtbox.delete("1.0", tk.END)
        self.headline_txtbox.insert("1.0", entry.get("headline", ""))

        self.text_body_txtbox.delete("1.0", tk.END)
        self.text_body_txtbox.insert("1.0", entry.get("text_body", ""))

        if entry.get("start_date"):
            try:
                self.start_date_picker.set_date(entry["start_date"])
            except Exception:
                pass

        if entry.get("end_date"):
            try:
                self.end_date_picker.set_date(entry["end_date"])
            except Exception:
                pass

        # Load style fields into right panel
        style = entry.get("style_data", self.get_default_style_data())
        self.bg_type_var.set(style.get("bg_type", "color"))
        self.bg_color_preview.config(bg=style.get("bg_color", "#1a1a1a"))
        self.block_color_preview.config(bg=style.get("block_color", "#000000"))

        opacity_val = style.get("block_opacity", 0.80)
        self.opacity_slider.set(int(opacity_val * 100))
        self.opacity_label.config(text=f"Block Opacity: {int(opacity_val * 100)}%")

        bg_overlay_val = style.get("bg_image_overlay", 0.40)
        self.bg_overlay_slider.set(int(bg_overlay_val * 100))
        self.bg_overlay_label.config(text=f"BG Image Darkness Overlay: {int(bg_overlay_val * 100)}%")

        self.bg_image_entry.delete(0, tk.END)
        self.bg_image_entry.insert(0, style.get("bg_image_path", ""))

        self.media_path_entry.delete(0, tk.END)
        self.media_path_entry.insert(0, style.get("media_image_path", ""))

        self.caption_entry.delete(0, tk.END)
        self.caption_entry.insert(0, style.get("caption", ""))

        self.source_entry.delete(0, tk.END)
        self.source_entry.insert(0, style.get("source", ""))

        self.h_font_cb.set(style.get("heading_font", "Arial"))
        self.h_size_sp.delete(0, tk.END)
        self.h_size_sp.insert(0, str(style.get("heading_size", 24)))
        self.h_color_preview.config(bg=style.get("heading_color", "#ffffff"))

        self.b_font_cb.set(style.get("body_font", "Arial"))
        self.b_size_sp.delete(0, tk.END)
        self.b_size_sp.insert(0, str(style.get("body_size", 14)))
        self.b_color_preview.config(bg=style.get("body_color", "#cccccc"))

        self._is_loading_data = False

    def on_input_change(self, *args):
        if self._is_loading_data or self.selected_index is None:
            return

        idx = self.selected_index
        is_title = self.is_title_var.get()

        if is_title:
            for i, item in enumerate(self.TIMELINE):
                if i != idx:
                    item["is_title"] = False

        headline = self.headline_txtbox.get("1.0", "end-1c")
        text_body = self.text_body_txtbox.get("1.0", "end-1c")
        start_date = self.start_date_picker.get()
        end_date = self.end_date_picker.get()

        self.TIMELINE[idx]["is_title"] = is_title
        self.TIMELINE[idx]["headline"] = headline
        self.TIMELINE[idx]["text_body"] = text_body
        self.TIMELINE[idx]["start_date"] = start_date
        self.TIMELINE[idx]["end_date"] = end_date

        self.refresh_treeview()
        self.table_view_tree.selection_set(str(idx))

    def on_style_input_change(self, *args):
        if self._is_loading_data or self.selected_index is None:
            return

        idx = self.selected_index
        style_data = {
            "bg_type": self.bg_type_var.get(),
            "bg_color": self.bg_color_preview.cget("bg"),
            "block_color": self.block_color_preview.cget("bg"),
            "block_opacity": round(self.opacity_slider.get() / 100.0, 2),
            "bg_image_path": self.bg_image_entry.get(),
            "bg_image_overlay": round(self.bg_overlay_slider.get() / 100.0, 2),
            "media_image_path": self.media_path_entry.get(),
            "caption": self.caption_entry.get(),
            "source": self.source_entry.get(),
            "heading_font": self.h_font_cb.get(),
            "heading_size": int(self.h_size_sp.get() or 24),
            "heading_color": self.h_color_preview.cget("bg"),
            "body_font": self.b_font_cb.get(),
            "body_size": int(self.b_size_sp.get() or 14),
            "body_color": self.b_color_preview.cget("bg"),
        }

        self.TIMELINE[idx]["style_data"] = style_data

    def delete_selected(self, event=None):
        if self.selected_index is None:
            return "break"

        idx_to_delete = self.selected_index
        if 0 <= idx_to_delete < len(self.TIMELINE):
            del self.TIMELINE[idx_to_delete]

        self.deselect_and_clear()
        self.refresh_treeview()
        return "break"

    def move_selected_up(self, event=None):
        if self.selected_index is None or self.selected_index <= 0:
            return "break"

        idx = self.selected_index
        self.TIMELINE[idx], self.TIMELINE[idx - 1] = (
            self.TIMELINE[idx - 1],
            self.TIMELINE[idx],
        )

        self.refresh_treeview()
        new_idx = idx - 1
        self.table_view_tree.selection_set(str(new_idx))
        return "break"

    def move_selected_down(self, event=None):
        if self.selected_index is None or self.selected_index >= len(self.TIMELINE) - 1:
            return "break"

        idx = self.selected_index
        self.TIMELINE[idx], self.TIMELINE[idx + 1] = (
            self.TIMELINE[idx + 1],
            self.TIMELINE[idx],
        )

        self.refresh_treeview()
        new_idx = idx + 1
        self.table_view_tree.selection_set(str(new_idx))
        return "break"

    def deselect_and_clear(self):
        self.selected_index = None
        self.table_view_tree.selection_remove(self.table_view_tree.selection())
        self.status_lbl.config(text="Select a row from the list above to edit its content", fg="#ffffff")
        self.toggle_editor_state(enabled=False)

    def toggle_editor_state(self, enabled=True):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.title_chk.config(state=state)
        self.headline_txtbox.config(state=state)
        self.text_body_txtbox.config(state=state)

    def refresh_treeview(self):
        for item in self.table_view_tree.get_children():
            self.table_view_tree.delete(item)

        for i, row in enumerate(self.TIMELINE):
            is_title_str = "Yes" if row.get("is_title") else "No"
            values = (
                f"#{i + 1}",
                row.get("headline", ""),
                row.get("text_body", ""),
                row.get("start_date", ""),
                row.get("end_date", ""),
                is_title_str,
            )
            self.table_view_tree.insert("", tk.END, iid=str(i), values=values)

    def file_new(self):
        self.TIMELINE.clear()
        self.current_file_path = None
        self.deselect_and_clear()
        self.add_empty_rows(10)

    def load_data(self):
        file_path = filedialog.askopenfilename(
            title="Open Timeline JSON",
            filetypes=[("JSON Files", "*.json")],
        )
        if not file_path:
            return

        try:
            data = load_json(file_path)
            if isinstance(data, list):
                self.TIMELINE = data
                self.current_file_path = file_path
                self.deselect_and_clear()
                self.refresh_treeview()
            else:
                messagebox.showerror("Error", "Invalid JSON data structure.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def file_save(self):
        if self.current_file_path:
            self._save_to_path(self.current_file_path)
        else:
            self.file_save_as()

    def file_save_as(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Timeline JSON",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
        )
        if file_path:
            self.current_file_path = file_path
            self._save_to_path(file_path)

    def _save_to_path(self, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.TIMELINE, f, indent=4)
            messagebox.showinfo("Saved", f"Successfully saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def build_website(self):
        output_dir = filedialog.askdirectory(title="Select Output Directory for Website")
        if not output_dir:
            return

        def run_build():
            try:
                build_website_content(self.TIMELINE, output_dir)
                index_path = os.path.join(output_dir, "index.html")
                self.data_queue.put(("SUCCESS", index_path))
            except Exception as e:
                self.data_queue.put(("ERROR", str(e)))

        threading.Thread(target=run_build, daemon=True).start()

    def check_queue(self):
        try:
            while True:
                msg_type, payload = self.data_queue.get_nowait()
                if msg_type == "SUCCESS":
                    self.update_preview(payload)
                elif msg_type == "ERROR":
                    messagebox.showerror("Build Error", f"Failed to build website: {payload}")
        except queue.Empty:
            pass

        if self.is_running:
            self.after(100, self.check_queue)

    def on_close(self):
        self.is_running = False
        self.destroy()


if __name__ == "__main__":
    app = Application()
    app.mainloop()