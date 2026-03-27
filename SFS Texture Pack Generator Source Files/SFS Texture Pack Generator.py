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

# --- App ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Texture Pack Generator")

        self.files = []
        self.thumbnails = []

        self.page = 0
        self.per_page = 25

        # Drag & Drop
        self.drop_area = tk.Label(root, text="Drag & Drop Images Here", bg="gray", width=60, height=3)
        self.drop_area.pack(pady=5)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.drop)

        # Scrollable canvas
        self.canvas = tk.Canvas(root, width=450, height=450)
        self.scrollbar = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack()
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Pagination controls
        nav = tk.Frame(root)
        nav.pack()

        tk.Button(nav, text="<< Prev", command=self.prev_page).pack(side="left")
        self.page_label = tk.Label(nav, text="Page 1")
        self.page_label.pack(side="left", padx=10)
        tk.Button(nav, text="Next >>", command=self.next_page).pack(side="left")

        # Inputs
        self.pack_name = tk.Entry(root)
        self.pack_name.insert(0, "Pack Name")
        self.pack_name.pack()

        self.version = tk.Entry(root)
        self.version.insert(0, "Version")
        self.version.pack()

        self.description = tk.Entry(root)
        self.description.insert(0, "Description")
        self.description.pack()

        self.author = tk.Entry(root)
        self.author.insert(0, "Author")
        self.author.pack()

        # Progress bar
        self.progress = ttk.Progressbar(root, length=300, mode='determinate')
        self.progress.pack(pady=5)

        #Dark mode
        self.dark_mode = True
        self.theme_btn = tk.Button(root, text="Dark Mode: ON", command=self.toggle_theme)
        self.theme_btn.pack(pady=5)
        self.toggle_theme()

        tk.Button(root, text="Generate Pack", command=self.generate).pack(pady=5)

    def drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                if f not in self.files:
                    self.files.append(f)
        self.update_preview()

    def update_preview(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        self.thumbnails.clear()

        cols = 5
        start = self.page * self.per_page
        end = start + self.per_page
        visible_files = self.files[start:end]

        for i, file in enumerate(visible_files):
            try:
                img = Image.open(file)
                img.thumbnail((80, 80))
                tk_img = ImageTk.PhotoImage(img)
                self.thumbnails.append(tk_img)

                label = tk.Label(self.scroll_frame, image=tk_img, bd=2, relief="solid")
                label.grid(row=i // cols, column=i % cols, padx=5, pady=5)

                # Click to remove
                label.bind("<Button-1>", lambda e, f=file: self.remove_file(f))

            except:
                pass

        total_pages = max(1, (len(self.files) - 1) // self.per_page + 1)
        self.page_label.config(text=f"Page {self.page + 1} / {total_pages}")

    def toggle_theme(self):
    self.dark_mode = not self.dark_mode

    if self.dark_mode:
        bg = "#1e1e1e"
        fg = "#ffffff"
        entry_bg = "#2a2a2a"
        btn_bg = "#333333"
        self.theme_btn.config(text="Dark Mode: ON")
    else:
        bg = "#f0f0f0"
        fg = "#000000"
        entry_bg = "#ffffff"
        btn_bg = "#e0e0e0"
        self.theme_btn.config(text="Dark Mode: OFF")

    # Root
    self.root.configure(bg=bg)

    # Apply to all widgets
    for widget in self.root.winfo_children():
        self.apply_theme(widget, bg, fg, entry_bg, btn_bg)

    def remove_file(self, file):
        if file in self.files:
            self.files.remove(file)
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

    def apply_theme(self, widget, bg, fg, entry_bg, btn_bg):
         try:
            if isinstance(widget, tk.Frame) or isinstance(widget, tk.Label):
                widget.config(bg=bg, fg=fg)
            elif isinstance(widget, tk.Button):
                widget.config(bg=btn_bg, fg=fg)
            elif isinstance(widget, tk.Entry):
                widget.config(bg=entry_bg, fg=fg, insertbackground=fg)
            elif isinstance(widget, tk.Canvas):
                widget.config(bg=bg)

            for child in widget.winfo_children():
                self.apply_theme(child, bg, fg, entry_bg, btn_bg)
            except:
                pass

    def generate(self):
        if not self.files:
            messagebox.showerror("Error", "No images added.")
            return

        pack_name = self.pack_name.get()
        version = self.version.get()
        description = self.description.get()
        author = self.author.get()

        documents = os.path.join(os.path.expanduser("~"), "Documents")
        base_path = os.path.join(documents, pack_name)

        os.makedirs(os.path.join(base_path, "Color Textures"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "Textures"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "Shadow Textures"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "Shape Textures"), exist_ok=True)

        with open(os.path.join(base_path, "pack_info.txt"), "w") as f:
            f.write(PACK_TEMPLATE % (pack_name, version, description, author))

        self.progress["maximum"] = len(self.files)

        for i, file in enumerate(self.files):
            name = os.path.splitext(os.path.basename(file))[0]
            dest_img = os.path.join(base_path, "Textures", name + ".png")

            try:
                img = Image.open(file).convert("RGBA")
                img.save(dest_img, "PNG")
            except:
                continue

            txt_path = os.path.join(base_path, "Color Textures", name + ".txt")
            with open(txt_path, "w") as f:
                f.write(COLOR_TEMPLATE % (name, name))

            self.progress["value"] = i + 1
            self.root.update_idletasks()

        messagebox.showinfo("Done", "Pack created successfully!")

# --- Run ---
root = TkinterDnD.Tk()
app = App(root)
root.mainloop()