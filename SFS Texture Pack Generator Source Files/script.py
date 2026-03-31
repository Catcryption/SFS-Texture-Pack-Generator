import os
import tkinter as tk
from tkinter import messagebox, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk

# --- Templates ---
COLOR_TEMPLATE = '''{
  "colorTex": {
    "textures": [
      {
        "texture": "%s.png",
        "ideal": 0.0
      }
    ],
    "center": {
      "mode": 0,
      "sizeMode": 0,
      "size": 0.5
    }
  },
  "name": "%s"
}'''

PACK_TEMPLATE = '''{
  "DisplayName": "%s",
  "Version": "%s",
  "Description": "%s",
  "Author": "%s"
}'''

# --- Tooltip helper ---
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 40
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="#ffffe0", relief="solid",
                         borderwidth=1, font=("Segoe UI", 8))
        label.pack()

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# --- Placeholder Entry ---
class PlaceholderEntry(tk.Entry):
    def __init__(self, master, placeholder="", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self._fg_real    = self.cget("fg")      # real text colour (set by theme later)
        self._showing_placeholder = False

        self.bind("<FocusIn>",  self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        self._show_placeholder()

    def _show_placeholder(self):
        self.delete(0, tk.END)
        self.insert(0, self.placeholder)
        self.config(fg="#888888")
        self._showing_placeholder = True

    def _on_focus_in(self, _=None):
        if self._showing_placeholder:
            self.delete(0, tk.END)
            self.config(fg=self._fg_real)
            self._showing_placeholder = False

    def _on_focus_out(self, _=None):
        if not self.get():
            self._show_placeholder()

    def get(self):
        if self._showing_placeholder:
            return ""
        return super().get()

    def set_fg(self, colour):
        """Called by the theme engine so real-text colour stays in sync."""
        self._fg_real = colour
        if not self._showing_placeholder:
            self.config(fg=colour)


# --- App ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("SFS Texture Pack Generator")
        self.root.resizable(False, False)

        self.files = []
        self.thumbnails = []

        self.page = 0
        self.per_page = 15  # 5 columns x 3 rows

        self.dark_mode = True

        # ── Outer wrapper so we can theme the root edge ──
        self.outer = tk.Frame(root)
        self.outer.pack(padx=12, pady=12)

        # ── Main content row ──
        content = tk.Frame(self.outer)
        content.grid(row=0, column=0, sticky="nsew")

        # --- Canvas / thumbnail area ---
        thumb_size = 80
        padding = 5
        rows_visible = 3
        cols_visible = 5

        canvas_width  = cols_visible * (thumb_size + padding * 2)
        canvas_height = rows_visible * (thumb_size + padding * 2)

        self.canvas = tk.Canvas(content, width=canvas_width, height=canvas_height,
                                highlightthickness=2)
        self.scrollbar = tk.Scrollbar(content, orient="vertical",
                                      command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Register canvas and scroll_frame as drop targets
        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.drop)
        self.scroll_frame.drop_target_register(DND_FILES)
        self.scroll_frame.dnd_bind('<<Drop>>', self.drop)

        # Image count label
        self.count_label = tk.Label(content, text="0 images loaded",
                                    font=("Segoe UI", 8))
        self.count_label.grid(row=1, column=0, columnspan=2, pady=(4, 0), sticky="w")

        # Pagination controls
        nav = tk.Frame(content)
        nav.grid(row=2, column=0, columnspan=2, pady=6)

        self.prev_btn = tk.Button(nav, text="◀ Prev", width=8,
                                  command=self.prev_page,
                                  relief="flat", bd=0, pady=4,
                                  cursor="hand2")
        self.prev_btn.pack(side="left")

        self.page_label = tk.Label(nav, text="Page 1 / 1",
                                   font=("Segoe UI", 9), width=12)
        self.page_label.pack(side="left", padx=8)

        self.next_btn = tk.Button(nav, text="Next ▶", width=8,
                                  command=self.next_page,
                                  relief="flat", bd=0, pady=4,
                                  cursor="hand2")
        self.next_btn.pack(side="left")

        # --- Vertical separator ---
        sep = ttk.Separator(content, orient="vertical")
        sep.grid(row=0, column=2, rowspan=3, sticky="ns", padx=10)

        # --- Pack settings panel (right) ---
        settings_frame = tk.Frame(content)
        settings_frame.grid(row=0, column=3, rowspan=3, sticky="n", padx=(0, 4))

        def labeled_entry(parent, label_text, placeholder, row):
            lbl = tk.Label(parent, text=label_text, font=("Segoe UI", 9),
                           anchor="w")
            lbl.grid(row=row * 2,     column=0, sticky="w", pady=(8, 0))
            entry = PlaceholderEntry(parent, placeholder=placeholder,
                                     width=22, font=("Segoe UI", 9))
            entry.grid(row=row * 2 + 1, column=0, sticky="ew", ipady=3)
            return lbl, entry

        self.lbl_name,    self.pack_name   = labeled_entry(settings_frame, "Pack Name",   "My Pack",        0)
        self.lbl_ver,     self.version     = labeled_entry(settings_frame, "Version",     "1.0",            1)
        self.lbl_desc,    self.description = labeled_entry(settings_frame, "Description", "A texture pack", 2)
        self.lbl_author,  self.author      = labeled_entry(settings_frame, "Author",      "Author",         3)

        # Dark mode toggle
        self.theme_btn = tk.Button(settings_frame, text="Dark Mode",
                                   width=20, font=("Segoe UI", 9),
                                   command=self.toggle_theme,
                                   relief="flat", bd=0, pady=6,
                                   cursor="hand2")
        self.theme_btn.grid(row=9, column=0, pady=(16, 4), sticky="ew")

        # Generate button
        self.gen_btn = tk.Button(settings_frame, text="Generate Pack",
                                 width=20, font=("Segoe UI", 9, "bold"),
                                 command=self.generate,
                                 relief="flat", bd=0, pady=6,
                                 cursor="hand2")
        self.gen_btn.grid(row=10, column=0, pady=4, sticky="ew")

        # Apply initial theme
        self.apply_theme_from_state()

    # ── helpers to iterate ALL themeable widgets ──────────────────────────────

    def _all_widgets(self, root_widget=None):
        """Yield every widget in the tree, including scroll_frame subtree.
        Defaults to self.root so nothing is missed."""
        if root_widget is None:
            root_widget = self.root
        yield root_widget
        for child in root_widget.winfo_children():
            yield from self._all_widgets(child)
        # scroll_frame lives inside a Canvas window — not a normal tk child
        if root_widget is self.canvas:
            yield from self._all_widgets(self.scroll_frame)

    # ── Drag & Drop ───────────────────────────────────────────────────────────

    def drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                if f not in self.files:
                    self.files.append(f)
        self.page = 0
        self.update_preview()

    # ── Preview grid ──────────────────────────────────────────────────────────

    def update_preview(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.thumbnails.clear()
        self.canvas.delete("hint")

        if not self.files:
            cx = self.canvas.winfo_reqwidth()  // 2
            cy = self.canvas.winfo_reqheight() // 2
            hint_fg = "#555555" if self.dark_mode else "#aaaaaa"
            self.canvas.create_text(
                cx, cy - 12,
                text="Drag & Drop Images Here",
                fill=hint_fg, font=("Segoe UI", 11, "bold"), tags="hint"
            )
            self.canvas.create_text(
                cx, cy + 12,
                text="(click a thumbnail to remove it)",
                fill=hint_fg, font=("Segoe UI", 8), tags="hint"
            )
            self.page_label.config(text="Page 1 / 1")
            self.count_label.config(text="0 images loaded")
            return

        cols  = 5
        start = self.page * self.per_page
        end   = start + self.per_page
        visible_files = self.files[start:end]

        # Determine current theme colours for new thumbnail labels
        bg      = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        hl      = "#555555" if self.dark_mode else "#aaaaaa"

        for i, file in enumerate(visible_files):
            try:
                img = Image.open(file)
                img.thumbnail((80, 80))
                tk_img = ImageTk.PhotoImage(img)
                self.thumbnails.append(tk_img)

                label = tk.Label(self.scroll_frame, image=tk_img,
                                 bd=2, relief="solid",
                                 bg=bg, highlightbackground=hl)
                label.grid(row=i // cols, column=i % cols, padx=5, pady=5)

                # Tooltip shows filename
                fname = os.path.basename(file)
                Tooltip(label, f"{fname}\n(click to remove)")

                # Click to remove
                label.bind("<Button-1>", lambda e, f=file: self.remove_file(f))
            except Exception:
                pass

        total_pages = max(1, (len(self.files) - 1) // self.per_page + 1)
        self.page_label.config(text=f"Page {self.page + 1} / {total_pages}")
        self.count_label.config(text=f"{len(self.files)} image{'s' if len(self.files) != 1 else ''} loaded")

        # Re-apply theme so new labels inherit correct colours
        self.apply_theme_from_state()

    # ── Theme ─────────────────────────────────────────────────────────────────

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme_from_state()

    def apply_theme_from_state(self):
        if self.dark_mode:
            bg           = "#1e1e1e"
            fg           = "#f0f0f0"
            entry_bg     = "#2d2d2d"
            btn_bg       = "#3a3a3a"
            drop_bg      = "#2a2a2a"
            sep_fg       = "#555555"
            canvas_hl    = "#00cc44"   # green outline in dark mode
            self.theme_btn.config(text="Dark Mode")
        else:
            bg           = "#f2f2f2"
            fg           = "#1a1a1a"
            entry_bg     = "#ffffff"
            btn_bg       = "#dcdcdc"
            drop_bg      = "#e8e8e8"
            sep_fg       = "#bbbbbb"
            canvas_hl    = "#cc2200"   # red outline in light mode
            self.theme_btn.config(text="Light Mode")

        self.root.configure(bg=bg)
        self.canvas.config(highlightbackground=canvas_hl, highlightcolor=canvas_hl)

        for widget in self._all_widgets():
            self._theme_widget(widget, bg, fg, entry_bg, btn_bg, drop_bg)

        # Redraw hint text so its colour matches the new theme
        if not self.files:
            self.canvas.delete("hint")
            cx = self.canvas.winfo_reqwidth()  // 2
            cy = self.canvas.winfo_reqheight() // 2
            hint_fg = "#555555" if self.dark_mode else "#aaaaaa"
            self.canvas.create_text(
                cx, cy - 12,
                text="Drag & Drop Images Here",
                fill=hint_fg, font=("Segoe UI", 11, "bold"), tags="hint"
            )
            self.canvas.create_text(
                cx, cy + 12,
                text="(click a thumbnail to remove it)",
                fill=hint_fg, font=("Segoe UI", 8), tags="hint"
            )

    def _theme_widget(self, widget, bg, fg, entry_bg, btn_bg, drop_bg):
        try:
            if isinstance(widget, tk.Frame):
                widget.config(bg=bg)                      # Frame has no fg
            elif isinstance(widget, tk.Label):
                widget.config(bg=bg, fg=fg)
            elif isinstance(widget, tk.Button):
                widget.config(bg=btn_bg, fg=fg, activebackground=btn_bg,
                              activeforeground=fg, relief="flat", bd=1)
            elif isinstance(widget, PlaceholderEntry):
                widget.config(bg=entry_bg,
                              insertbackground=fg,
                              relief="flat", bd=1,
                              highlightthickness=1,
                              highlightbackground="#555" if self.dark_mode else "#bbb",
                              highlightcolor="#888")
                widget.set_fg(fg)          # keeps placeholder grey, real text themed
            elif isinstance(widget, tk.Entry):
                widget.config(bg=entry_bg, fg=fg,
                              insertbackground=fg,
                              relief="flat", bd=1,
                              highlightthickness=1,
                              highlightbackground="#555" if self.dark_mode else "#bbb",
                              highlightcolor="#888")
            elif isinstance(widget, tk.Canvas):
                widget.config(bg=bg)
            elif isinstance(widget, tk.Scrollbar):
                widget.config(bg=btn_bg, troughcolor=bg)
        except Exception:
            pass

    # ── Pagination ────────────────────────────────────────────────────────────

    def remove_file(self, file):
        if file in self.files:
            self.files.remove(file)
        # Stay on current page unless it no longer exists
        total_pages = max(1, (len(self.files) - 1) // self.per_page + 1)
        if self.page >= total_pages:
            self.page = total_pages - 1
        self.update_preview()

    def next_page(self):
        if (self.page + 1) * self.per_page < len(self.files):
            self.page += 1
            self.update_preview()

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.update_preview()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Generate pack ─────────────────────────────────────────────────────────

    def generate(self):
        if not self.files:
            messagebox.showerror("Error", "No images added.")
            return

        pack_name   = self.pack_name.get().strip()
        version     = self.version.get().strip()
        description = self.description.get().strip()
        author      = self.author.get().strip()

        missing = []
        if not pack_name:   missing.append("Pack Name")
        if not version:     missing.append("Version")
        if not description: missing.append("Description")
        if not author:      missing.append("Author")

        if missing:
            messagebox.showerror(
                "Missing Fields",
                "Please fill in the following fields before generating:\n\n" +
                "\n".join(f"  - {f}" for f in missing)
            )
            return

        try:
            float(version)
        except ValueError:
            messagebox.showerror("Invalid Version", "Version must be a number (e.g. 1, 1.0, 2.5).")
            return

        documents = os.path.join(os.path.expanduser("~"), "Documents")
        base_path = os.path.join(documents, pack_name)

        os.makedirs(os.path.join(base_path, "Color Textures"),  exist_ok=True)
        os.makedirs(os.path.join(base_path, "Textures"),        exist_ok=True)
        os.makedirs(os.path.join(base_path, "Shadow Textures"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "Shape Textures"),  exist_ok=True)

        with open(os.path.join(base_path, "pack_info.txt"), "w") as f:
            f.write(PACK_TEMPLATE % (pack_name, version, description, author))

        errors = []
        for file in self.files:
            name     = os.path.splitext(os.path.basename(file))[0]
            dest_img = os.path.join(base_path, "Textures", name + ".png")

            try:
                img = Image.open(file).convert("RGBA")
                img.save(dest_img, "PNG")
            except Exception as e:
                errors.append(f"{name}: {e}")
                continue

            txt_path = os.path.join(base_path, "Color Textures", name + ".txt")
            with open(txt_path, "w") as f:
                f.write(COLOR_TEMPLATE % (name, name))

        if errors:
            messagebox.showwarning(
                "Done with warnings",
                f"Pack created but {len(errors)} file(s) failed:\n" + "\n".join(errors)
            )
        else:
            messagebox.showinfo("Done", f"Pack '{pack_name}' created at:\n{base_path}")


# --- Run ---
root = TkinterDnD.Tk()
app  = App(root)
root.mainloop()