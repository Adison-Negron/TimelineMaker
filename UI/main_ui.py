import queue
import threading
import time
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, scrolledtext, ttk
import tkinterweb as tkweb
from StyleDialog import StyleDialog


class Application(tk.Tk):

    def __init__(self):
        super().__init__()

        # Setup
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        bottom_margin = 20
        color_palette = {
            "background": "#35414d",
            "light_foreground": "#ffffff",
            "dark_foreground": "#000000",
            "button_bg": "#4a5a6a",
            "textbox_bg": "#EBEBEB",
        }

        # Data Stores
        self.TIMELINE = {}
        self.table_order_to_item_id = {}
        self._temp_style_data = None  # Temporary storage before clicking "Add Entry"

        self.title("Timeline Maker")
        self.geometry(f"{screen_width}x{screen_height}")

        # UI Layout Calculations
        left_frame_width = screen_width // 2
        right_frame_width = screen_width // 2

        table_view_height = int(screen_height * 0.35)
        content_editor_height = int(screen_height * 0.65)

        content_editor_left_frame_width = int(left_frame_width * 0.70)
        content_editor_right_frame_width = int(left_frame_width * 0.30)

        # 1. Left Frame (50% Screen Width)
        self.left_frame = tk.Frame(
            self, width=left_frame_width, height=screen_height
        )
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.left_frame.pack_propagate(False)

        # 2. Right Frame (50% Screen Width)
        self.right_frame = tk.Frame(
            self, width=right_frame_width, height=screen_height
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.right_frame.pack_propagate(False)

        # 3. Preview HTML
        self.preview_html = tkweb.HtmlFrame(
            self.right_frame, horizontal_scrollbar="auto"
        )
        self.preview_html.pack(fill=tk.BOTH, expand=True)
        preview_html_content = (
            f"<html><body><p>Start Adding Content to see changes</p>"
            f"<h1>Screen Width: {screen_width}</h1>"
            f"<h1>Screen Height: {screen_height}</h1></body></html>"
        )
        self.preview_html.load_html(preview_html_content)

        # --- Left Frame Sub-Components ---

        # Top Menu
        self.top_menu = tk.Menu(self)
        self.config(menu=self.top_menu)

        # File Menu
        self.file_menu = tk.Menu(self.top_menu, tearoff=0)
        self.file_menu.add_command(label="New")
        self.file_menu.add_command(label="Open")
        self.file_menu.add_command(label="Save")
        self.file_menu.add_command(label="Save As")
        self.top_menu.add_cascade(label="File", menu=self.file_menu)

        # Edit Menu
        self.edit_menu = tk.Menu(self.top_menu, tearoff=0)
        self.edit_menu.add_command(label="Preferences")
        self.top_menu.add_cascade(label="Edit", menu=self.edit_menu)

        # Table View Frame (Top)
        self.table_view_frame = tk.Frame(
            self.left_frame, width=left_frame_width, height=table_view_height
        )
        self.table_view_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)
        self.table_view_frame.pack_propagate(False)

        # Treeview Widget Setup
        tree_columns = ("order", "headline", "text_body", "start_date", "end_date")
        self.table_view_tree = ttk.Treeview(
            self.table_view_frame, columns=tree_columns, show="headings"
        )

        self.table_view_tree.bind("<<TreeviewSelect>>", self.load_data_from_table)
        self.table_view_tree.bind("<Double-1>", self.delete_entry)

        self.table_view_tree.heading("order", text="Order", command=lambda: self.sort_by_column("order", False))
        self.table_view_tree.column("order", width=60, anchor="center")

        self.table_view_tree.heading("headline", text="Headline")
        self.table_view_tree.column("headline", width=160, anchor="w")

        self.table_view_tree.heading("text_body", text="Text Body")
        self.table_view_tree.column("text_body", width=300, anchor="w")

        self.table_view_tree.heading("start_date", text="Start Date")
        self.table_view_tree.column("start_date", width=100, anchor="center")

        self.table_view_tree.heading("end_date", text="End Date")
        self.table_view_tree.column("end_date", width=100, anchor="center")

        # Scrollbars for Treeview
        v_scroll = ttk.Scrollbar(
            self.table_view_frame,
            orient="vertical",
            command=self.table_view_tree.yview,
        )
        h_scroll = ttk.Scrollbar(
            self.table_view_frame,
            orient="horizontal",
            command=self.table_view_tree.xview,
        )
        self.table_view_tree.configure(
            yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set
        )

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.table_view_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Content Editor Frame (Bottom)
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

        # Editor Left Column (Inputs)
        self.content_editor_left_frame = tk.Frame(
            self.content_editor_frame,
            width=content_editor_left_frame_width,
            bg=color_palette["background"],
        )
        self.content_editor_left_frame.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True
        )

        # Editor Right Column (Buttons)
        self.content_editor_right_frame = tk.Frame(
            self.content_editor_frame,
            width=content_editor_right_frame_width,
            bg=color_palette["background"],
        )
        self.content_editor_right_frame.pack(
            side=tk.RIGHT, fill=tk.Y, expand=False
        )

        # --- Left Column Inputs ---

        # Order
        self.order_lbl = tk.Label(
            self.content_editor_left_frame,
            text="Order:",
            anchor="w",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.order_lbl.pack(side=tk.TOP, anchor="w")
        self.order_number = tk.Spinbox(
            self.content_editor_left_frame, from_=0, to=100, increment=1
        )
        self.order_number.pack(side=tk.TOP, anchor="w", pady=(0, bottom_margin))

        # Headline
        self.headline_lbl = tk.Label(
            self.content_editor_left_frame,
            text="Headline:",
            anchor="w",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.headline_lbl.pack(side=tk.TOP, anchor="w")

        self.headline_txtbox = scrolledtext.ScrolledText(
            self.content_editor_left_frame,
            height=2,
            width=70,
            wrap=tk.WORD,
            bg=color_palette["textbox_bg"],
            fg=color_palette["dark_foreground"],
        )
        self.headline_txtbox.pack(
            side=tk.TOP, anchor="w", pady=(0, bottom_margin)
        )

        # Text Body
        self.text_body_lbl = tk.Label(
            self.content_editor_left_frame,
            text="Text Body:",
            anchor="w",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.text_body_lbl.pack(side=tk.TOP, anchor="w")

        self.text_body_txtbox = scrolledtext.ScrolledText(
            self.content_editor_left_frame,
            height=10,
            width=70,
            wrap=tk.WORD,
            bg=color_palette["textbox_bg"],
            fg=color_palette["dark_foreground"],
        )
        self.text_body_txtbox.pack(
            side=tk.TOP, anchor="w", pady=(0, bottom_margin)
        )

        # Date Frame
        self.date_frame = tk.Frame(
            self.content_editor_left_frame, bg=color_palette["background"]
        )
        self.date_frame.pack(side=tk.TOP, anchor="w", fill=tk.X)

        self.date_lbl = tk.Label(
            self.date_frame,
            text="Date:",
            anchor="w",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.date_lbl.pack(side=tk.TOP, anchor="w", pady=(0, 5))

        self.start_date_lbl = tk.Label(
            self.date_frame,
            text="Start Date:",
            anchor="w",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.start_date_lbl.pack(side=tk.LEFT, anchor="w", padx=(0, 5))
        self.start_date_txtbox = tk.Text(
            self.date_frame,
            height=2,
            width=14,
            wrap=tk.WORD,
            bg=color_palette["textbox_bg"],
            fg=color_palette["dark_foreground"],
        )
        self.start_date_txtbox.pack(
            side=tk.LEFT, anchor="w", pady=(0, bottom_margin)
        )

        self.end_date_lbl = tk.Label(
            self.date_frame,
            text="End Date:",
            anchor="w",
            bg=color_palette["background"],
            fg=color_palette["light_foreground"],
        )
        self.end_date_lbl.pack(side=tk.LEFT, anchor="w", padx=(10, 5))
        self.end_date_txtbox = tk.Text(
            self.date_frame,
            height=2,
            width=14,
            wrap=tk.WORD,
            bg=color_palette["textbox_bg"],
            fg=color_palette["dark_foreground"],
        )
        self.end_date_txtbox.pack(
            side=tk.LEFT, anchor="w", pady=(0, bottom_margin)
        )

        # --- Right Column Buttons ---
        self.style_btn = tk.Button(
            self.content_editor_right_frame,
            text="Style",
            width=40,
            height=2,
            bg=color_palette["button_bg"],
            fg=color_palette["light_foreground"],
            command=self.open_style_window,
        )
        self.style_btn.pack(side=tk.TOP, padx=10, pady=(15, bottom_margin))

        self.advanced_config_btn = tk.Button(
            self.content_editor_right_frame,
            text="Advanced Config",
            width=40,
            height=2,
            bg=color_palette["button_bg"],
            fg=color_palette["light_foreground"],
        )
        self.advanced_config_btn.pack(
            side=tk.TOP, padx=10, pady=(0, bottom_margin + 100)
        )

        self.add_entry_btn = tk.Button(
            self.content_editor_right_frame,
            text="Add Entry",
            width=40,
            height=2,
            bg=color_palette["button_bg"],
            fg=color_palette["light_foreground"],
            command=self.add_entry,
        )
        self.add_entry_btn.pack(side=tk.TOP, padx=10, pady=(0, 15))

        # Threading Infrastructure
        self.data_queue = queue.Queue()
        self.is_running = True

        # Handle window close cleanly
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Start non-blocking queue consumer loop on main thread
        self.check_queue()

    def get_default_style(self):
        """Returns baseline style schema for entries created without opening StyleDialog."""
        return {
            "bg_type": "color",
            "bg_color": "#ffffff",
            "bg_image_path": "",
            "media_image_path": "",
            "caption": "",
            "source": "",
            "heading_font": "Arial",
            "heading_size": 18,
            "heading_color": "#000000",
            "body_font": "Arial",
            "body_size": 12,
            "body_color": "#333333",
        }

    def add_entry(self):
        headline = self.headline_txtbox.get("1.0", tk.END).strip()
        text_body = self.text_body_txtbox.get("1.0", tk.END).strip()
        start_date = self.start_date_txtbox.get("1.0", tk.END).strip()
        end_date = self.end_date_txtbox.get("1.0", tk.END).strip()

        try:
            order = int(self.order_number.get())
        except ValueError:
            messagebox.showwarning(
                "Input Error", "Order number must be a valid integer."
            )
            return

        if not headline or not text_body or not start_date or not end_date:
            messagebox.showwarning(
                "Input Error", "All fields must be filled out."
            )
            return

        # Check date format validation
        try:
            start_date_obj = time.strptime(start_date, "%Y-%m-%d")
            end_date_obj = time.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showwarning(
                "Input Error", "Invalid date format. Please use YYYY-MM-DD."
            )
            return

        start_date_tuple = (
            start_date_obj.tm_year,
            start_date_obj.tm_mon,
            start_date_obj.tm_mday,
        )
        end_date_tuple = (
            end_date_obj.tm_year,
            end_date_obj.tm_mon,
            end_date_obj.tm_mday,
        )

        # Retrieve temp style if configured prior to clicking Add Entry, else generate defaults
        style_data = (
            self._temp_style_data
            if self._temp_style_data
            else self.get_default_style()
        )

        self.create_data_entry(
            order, headline, text_body, start_date_tuple, end_date_tuple, style_data
        )

        # Reset temp style & fields
        self.clear_content()
        self.sort_by_column("order",False)
        return 1
    

    def create_data_entry(
        self, order, headline, text_body, start_date, end_date, style_data=None
    ):
        if style_data is None:
            style_data = self.get_default_style()

        data = (headline, text_body, start_date, end_date, style_data)
        self.TIMELINE[order] = data
        print(f"Debug: Stored TIMELINE[{order}]: {self.TIMELINE[order]}")

        # Update UI table view
        self.update_table_view(order)
        return 1

    def clear_content(self):
        self.headline_txtbox.delete("1.0", tk.END)
        self.text_body_txtbox.delete("1.0", tk.END)
        self.start_date_txtbox.delete("1.0", tk.END)
        self.end_date_txtbox.delete("1.0", tk.END)

        # Set spinbox to the next available order number
        next_order = max(self.TIMELINE.keys(), default=-1) + 1
        self.order_number.delete(0, tk.END)
        self.order_number.insert(0, str(next_order))

        # Clear temporary style
        self._temp_style_data = None

    def update_table_view(self, order):
        print(f"Debug: Updating table view for order {order}")
        entry = self.TIMELINE[order]

        # Format dates into clean string formats: YYYY-MM-DD
        start_str = f"{entry[2][0]}-{entry[2][1]:02d}-{entry[2][2]:02d}"
        end_str = f"{entry[3][0]}-{entry[3][1]:02d}-{entry[3][2]:02d}"

        values = (order, entry[0], entry[1], start_str, end_str)

        # Check if order already exists in Treeview
        if order in self.table_order_to_item_id:
            item_id = self.table_order_to_item_id[order]
            self.table_view_tree.item(item_id, values=values)
            print(f"Debug: Updated existing Treeview item ID {item_id}")
        else:
            # Insert new row into Treeview
            item_id = self.table_view_tree.insert("", tk.END, values=values)
            self.table_order_to_item_id[order] = item_id
            print(f"Debug: Inserted new Treeview item ID {item_id}")

        return 1

    def load_data_from_table(self, event):
        selected_item = self.table_view_tree.selection()
        if not selected_item:
            return 0

        item_values = self.table_view_tree.item(selected_item[0], "values")
        order = int(item_values[0])

        return self.load_content_fields(order)

    def load_content_fields(self, order):
        original_data = self.TIMELINE.get(order)
        if not original_data:
            return 0

        self.order_number.delete(0, tk.END)
        self.headline_txtbox.delete("1.0", tk.END)
        self.text_body_txtbox.delete("1.0", tk.END)
        self.start_date_txtbox.delete("1.0", tk.END)
        self.end_date_txtbox.delete("1.0", tk.END)

        # Parse dates
        startdate = original_data[2]
        enddate = original_data[3]

        start_str = f"{startdate[0]}-{startdate[1]:02d}-{startdate[2]:02d}"
        end_str = f"{enddate[0]}-{enddate[1]:02d}-{enddate[2]:02d}"

        self.order_number.insert(0, order)
        self.headline_txtbox.insert("1.0", original_data[0])
        self.text_body_txtbox.insert("1.0", original_data[1])
        self.start_date_txtbox.insert("1.0", start_str)
        self.end_date_txtbox.insert("1.0", end_str)

        # Populate temporary style with target entry's style configuration
        if len(original_data) > 4 and original_data[4]:
            self._temp_style_data = original_data[4].copy()
        else:
            self._temp_style_data = self.get_default_style()

        print(
            f"Debug: Loaded Order {order} and attached style_data."
        )

        return 1

    def delete_entry(self,event):
        selected_item = self.table_view_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select an item to delete.")
            return 0
        item_values = self.table_view_tree.item(selected_item[0], "values")
        order = int(item_values[0])
        headline = item_values[1]

        confirm = messagebox.askyesno(
        title="Confirm Deletion",
        message=f"Are you sure you want to delete Order {order} ('{headline}')?\nThis action cannot be undone.",
        icon="warning",  # Displays the warning icon on Windows/macOS/Linux
        )

        if confirm:
            # Remove from dictionary
            if order in self.TIMELINE:
                del self.TIMELINE[order]

            # Remove from ID mapping
            if order in self.table_order_to_item_id:
                del self.table_order_to_item_id[order]

            # Remove row from Treeview widget
            self.table_view_tree.delete(selected_item[0])

            # Reset editor fields
            self.clear_content()

        print(f"Debug: Successfully deleted Order {order}")
        self.sort_by_column("order",False)
        return 1




    def open_style_window(self):
        try:
            current_order = int(self.order_number.get())
        except ValueError:
            current_order = 0

        # If it's a new entry, ensure _temp_style_data is set to fresh defaults
        if current_order not in self.TIMELINE and self._temp_style_data is None:
            self._temp_style_data = self.get_default_style()

        dialog = StyleDialog(self, current_order=current_order)
        self.wait_window(dialog)

        print(f"Debug: Finished editing style for Order {current_order}")



    def sort_by_column(self, col, reverse):
        """Sort treeview content when a column header is clicked."""
        # Fetch list of tuples: [(col_value, item_id), ...]
        data = []
        for item_id in self.table_view_tree.get_children(""):
            value = self.table_view_tree.set(item_id, col)

            # Convert to integer if sorting by 'order' so numeric sorting works correctly
            if col == "order":
                try:
                    value = int(value)
                except ValueError:
                    pass

            data.append((value, item_id))

        # Sort the list based on column value
        data.sort(reverse=reverse)

        # Reorder items in the Treeview
        for index, (val, item_id) in enumerate(data):
            self.table_view_tree.move(item_id, "", index)

        # Rebind header click to reverse direction on next click
        self.table_view_tree.heading(
            col, command=lambda: self.sort_by_column(col, not reverse)
        )




    def start_task(self):
        worker = threading.Thread(target=self.background_worker, daemon=True)
        worker.start()

    def background_worker(self):
        time.sleep(3)
        result = "Task Complete!"
        self.data_queue.put(result)

    def check_queue(self):
        try:
            while True:
                message = self.data_queue.get_nowait()
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