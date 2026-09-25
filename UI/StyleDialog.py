import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, scrolledtext, ttk


class StyleDialog(tk.Toplevel):

    def __init__(self, parent, current_order=0):
        super().__init__(parent)
        self.order = current_order
        self.title("Style & Media Customization")
        self.geometry("520x620")
        self.resizable(False, False)

        # Make window modal
        self.transient(parent)
        self.grab_set()

        # Load style data from TIMELINE, temp storage, or defaults
        self.style_data = self._get_initial_style()

        # Available Fonts & Sizes
        self.font_families = [
            "Arial",
            "Courier New",
            "Georgia",
            "Helvetica",
            "Times New Roman",
            "Verdana",
        ]
        self.font_sizes = [str(size) for size in range(8, 37, 2)]

        # Main Layout Structure
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create Tabs
        self.media_tab = ttk.Frame(self.notebook)
        self.typography_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.media_tab, text=" Background & Media ")
        self.notebook.add(self.typography_tab, text=" Typography & Colors ")

        # Build Tab Contents
        self._build_media_tab()
        self._build_typography_tab()

        # Bottom Action Bar
        self._build_action_bar()

    def _get_initial_style(self):
        # 1. If entry exists in TIMELINE, use its style
        if self.order in self.master.TIMELINE:
            entry = self.master.TIMELINE[self.order]
            if len(entry) > 4 and entry[4]:
                return entry[4].copy()

        # 2. If it's a new entry and temp style exists, use it
        if hasattr(self.master, "_temp_style_data") and self.master._temp_style_data is not None:
            return self.master._temp_style_data.copy()

        # 3. Fallback to default schema
        return self.master.get_default_style()

    # --- TAB 1: MEDIA & BACKGROUND ---
    def _build_media_tab(self):
        bg_frame = ttk.LabelFrame(self.media_tab, text=" Background ", padding=10)
        bg_frame.pack(fill=tk.X, padx=10, pady=10)

        self.bg_type_var = tk.StringVar(value=self.style_data["bg_type"])

        color_radio = ttk.Radiobutton(
            bg_frame,
            text="Solid Color",
            value="color",
            variable=self.bg_type_var,
            command=self._toggle_bg_inputs,
        )
        color_radio.grid(row=0, column=0, sticky="w", pady=2)

        self.bg_color_btn = ttk.Button(
            bg_frame, text="Pick Color", command=self._pick_bg_color
        )
        self.bg_color_btn.grid(row=0, column=1, padx=10, pady=2)

        self.bg_color_preview = tk.Label(
            bg_frame,
            bg=self.style_data["bg_color"],
            width=6,
            relief="solid",
            bd=1,
        )
        self.bg_color_preview.grid(row=0, column=2, pady=2)

        image_radio = ttk.Radiobutton(
            bg_frame,
            text="Image",
            value="image",
            variable=self.bg_type_var,
            command=self._toggle_bg_inputs,
        )
        image_radio.grid(row=1, column=0, sticky="w", pady=(10, 2))

        self.bg_image_entry = ttk.Entry(bg_frame, width=30)
        self.bg_image_entry.insert(0, self.style_data["bg_image_path"])
        self.bg_image_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=(10, 2))

        self.bg_image_btn = ttk.Button(
            bg_frame, text="Browse...", command=self._browse_bg_image
        )
        self.bg_image_btn.grid(row=2, column=1, sticky="w", padx=10, pady=2)

        media_frame = ttk.LabelFrame(
            self.media_tab, text=" Timeline Entry Image ", padding=10
        )
        media_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(media_frame, text="Image File:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self.media_path_entry = ttk.Entry(media_frame, width=30)
        self.media_path_entry.insert(0, self.style_data["media_image_path"])
        self.media_path_entry.grid(row=0, column=1, padx=5, pady=5)

        media_browse_btn = ttk.Button(
            media_frame, text="Browse...", command=self._browse_media_image
        )
        media_browse_btn.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(media_frame, text="Caption:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self.caption_entry = ttk.Entry(media_frame, width=42)
        self.caption_entry.insert(0, self.style_data["caption"])
        self.caption_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5)

        ttk.Label(media_frame, text="Source/Credit:").grid(
            row=2, column=0, sticky="w", pady=5
        )
        self.source_entry = ttk.Entry(media_frame, width=42)
        self.source_entry.insert(0, self.style_data["source"])
        self.source_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

        self._toggle_bg_inputs()

    # --- TAB 2: TYPOGRAPHY & COLORS ---
    def _build_typography_tab(self):
        h_frame = ttk.LabelFrame(self.typography_tab, text=" Heading ", padding=10)
        h_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(h_frame, text="Font:").grid(row=0, column=0, sticky="w", pady=5)
        self.h_font_combo = ttk.Combobox(
            h_frame, values=self.font_families, state="readonly", width=18
        )
        self.h_font_combo.set(self.style_data["heading_font"])
        self.h_font_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(h_frame, text="Size:").grid(row=0, column=2, sticky="w", pady=5)
        self.h_size_combo = ttk.Combobox(
            h_frame, values=self.font_sizes, state="readonly", width=5
        )
        self.h_size_combo.set(str(self.style_data["heading_size"]))
        self.h_size_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(h_frame, text="Color:").grid(row=1, column=0, sticky="w", pady=5)
        self.h_color_btn = ttk.Button(
            h_frame, text="Choose Color", command=self._pick_h_color
        )
        self.h_color_btn.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.h_color_preview = tk.Label(
            h_frame,
            bg=self.style_data["heading_color"],
            width=6,
            relief="solid",
            bd=1,
        )
        self.h_color_preview.grid(row=1, column=2, pady=5)

        b_frame = ttk.LabelFrame(
            self.typography_tab, text=" Paragraph / Body ", padding=10
        )
        b_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(b_frame, text="Font:").grid(row=0, column=0, sticky="w", pady=5)
        self.b_font_combo = ttk.Combobox(
            b_frame, values=self.font_families, state="readonly", width=18
        )
        self.b_font_combo.set(self.style_data["body_font"])
        self.b_font_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(b_frame, text="Size:").grid(row=0, column=2, sticky="w", pady=5)
        self.b_size_combo = ttk.Combobox(
            b_frame, values=self.font_sizes, state="readonly", width=5
        )
        self.b_size_combo.set(str(self.style_data["body_size"]))
        self.b_size_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(b_frame, text="Color:").grid(row=1, column=0, sticky="w", pady=5)
        self.b_color_btn = ttk.Button(
            b_frame, text="Choose Color", command=self._pick_b_color
        )
        self.b_color_btn.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        self.b_color_preview = tk.Label(
            b_frame,
            bg=self.style_data["body_color"],
            width=6,
            relief="solid",
            bd=1,
        )
        self.b_color_preview.grid(row=1, column=2, pady=5)

    # --- BOTTOM ACTIONS ---
    def _build_action_bar(self):
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        save_btn = ttk.Button(
            btn_frame, text="Apply & Save", command=self._save_and_close
        )
        save_btn.pack(side=tk.RIGHT, padx=5)

        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    # --- EVENT HANDLERS ---
    def _toggle_bg_inputs(self):
        selection = self.bg_type_var.get()
        if selection == "color":
            self.bg_color_btn.config(state="normal")
            self.bg_image_entry.config(state="disabled")
            self.bg_image_btn.config(state="disabled")
        else:
            self.bg_color_btn.config(state="disabled")
            self.bg_image_entry.config(state="normal")
            self.bg_image_btn.config(state="normal")

    def _pick_bg_color(self):
        color = colorchooser.askcolor(title="Select Background Color")[1]
        if color:
            self.style_data["bg_color"] = color
            self.bg_color_preview.config(bg=color)

    def _pick_h_color(self):
        color = colorchooser.askcolor(title="Select Heading Font Color")[1]
        if color:
            self.style_data["heading_color"] = color
            self.h_color_preview.config(bg=color)

    def _pick_b_color(self):
        color = colorchooser.askcolor(title="Select Body Font Color")[1]
        if color:
            self.style_data["body_color"] = color
            self.b_color_preview.config(bg=color)

    def _browse_bg_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            self.bg_image_entry.config(state="normal")
            self.bg_image_entry.delete(0, tk.END)
            self.bg_image_entry.insert(0, file_path)

    def _browse_media_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            self.media_path_entry.delete(0, tk.END)
            self.media_path_entry.insert(0, file_path)

    def reset_fields_to_defaults(self):
        """Resets all widget inputs and preview labels in StyleDialog to standard baseline defaults."""
        defaults = self.master.get_default_style()
        self.style_data = defaults.copy()

        # 1. Reset Media & Background Tab
        self.bg_type_var.set(defaults["bg_type"])

        self.bg_color_preview.config(bg=defaults["bg_color"])

        self.bg_image_entry.config(state="normal")
        self.bg_image_entry.delete(0, tk.END)
        self.bg_image_entry.insert(0, defaults["bg_image_path"])

        self.media_path_entry.delete(0, tk.END)
        self.media_path_entry.insert(0, defaults["media_image_path"])

        self.caption_entry.delete(0, tk.END)
        self.caption_entry.insert(0, defaults["caption"])

        self.source_entry.delete(0, tk.END)
        self.source_entry.insert(0, defaults["source"])

        self._toggle_bg_inputs()

        # 2. Reset Typography Tab
        self.h_font_combo.set(defaults["heading_font"])
        self.h_size_combo.set(str(defaults["heading_size"]))
        self.h_color_preview.config(bg=defaults["heading_color"])

        self.b_font_combo.set(defaults["body_font"])
        self.b_size_combo.set(str(defaults["body_size"]))
        self.b_color_preview.config(bg=defaults["body_color"])

    def _save_and_close(self):
        # Collect configuration values
        self.style_data["bg_type"] = self.bg_type_var.get()
        self.style_data["bg_image_path"] = self.bg_image_entry.get().strip()
        self.style_data["media_image_path"] = self.media_path_entry.get().strip()
        self.style_data["caption"] = self.caption_entry.get().strip()
        self.style_data["source"] = self.source_entry.get().strip()

        self.style_data["heading_font"] = self.h_font_combo.get()
        self.style_data["heading_size"] = int(self.h_size_combo.get())

        self.style_data["body_font"] = self.b_font_combo.get()
        self.style_data["body_size"] = int(self.b_size_combo.get())

        # Update parent TIMELINE directly if row already exists
        if self.order in self.master.TIMELINE:
            entry = self.master.TIMELINE[self.order]
            self.master.TIMELINE[self.order] = (
                entry[0],
                entry[1],
                entry[2],
                entry[3],
                self.style_data,
            )

        # Retain in temp variable for clicking "Add Entry"
        self.master._temp_style_data = self.style_data

        self.destroy()