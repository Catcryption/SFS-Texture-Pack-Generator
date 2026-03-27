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
    "border_Bottom": {
      "uvSize": 0.0,
      "sizeMode": 0,
      "size": 0.5
    },
    "border_Top": {
      "uvSize": 0.0,
      "sizeMode": 0,
      "size": 0.5
    },
    "center": {
      "mode": 0,
      "sizeMode": 0,
      "size": 0.5,
      "logoHeightPercent": 0.5,
      "scaleLogoToFit": false
    },
    "fixedWidth": false,
    "fixedWidthValue": 1.0,
    "flipToLight_X": false,
    "flipToLight_Y": false,
    "metalTexture": false,
    "icon": null
  },
  "tags": [
    "tank",
    "cone",
    "fairing"
  ],
  "pack_Redstone_Atlas": false,
  "multiple": false,
  "segments": [],
  "name": "%s",
  "hideFlags": 0
}'''

PACK_TEMPLATE = '''{
  "DisplayName": "%s",
  "Version": "1.0",
  "Description": "%s",
  "Author": "%s",
  "ShowIcon": false,
  "Icon": null,
  "name": "",
  "hideFlags": 0
}'''

# --- App ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Texture Pack Generator")

        self.files = []
        self.thumbnails = []

        # Drag & Drop
        self.drop_area = tk.Label(root, text="Drag & Drop Images Here", bg="gray", width=60, height=5)
        self.drop_area.pack(pady=10)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.drop)

        # Preview grid
        self.preview_frame = tk.Frame(root)
        self.preview_frame.pack()

        # Inputs
        self.folder_name = tk.Entry(root)
        self.folder_name.insert(0, "Folder Name")
        self.folder_name.pack()

        self.display_name = tk.Entry(root)
        self.display_name.insert(0, "Display Name")
        self.display_name.pack()

        self.description = tk.Entry(root)
        self.description.insert(0, "Description")
        self.description.pack()

        self.author = tk.Entry(root)
        self.author.insert(0, "Author")
        self.author.pack()

        # Progress bar
        self.progress = ttk.Progressbar(root, length=300, mode='determinate')
        self.progress.pack(pady=10)

        tk.Button(root, text="Generate Pack", command=self.generate).pack(pady=5)

    def drop(self, event):
        files = self.root.tk.splitlist(event.data)
        for f in files:
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                if f not in self.files:
                    self.files.append(f)
        self.update_preview()

    def update_preview(self):
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        self.thumbnails.clear()

        cols = 5
        for i, file in enumerate(self.files):
            try:
                img = Image.open(file)
                img.thumbnail((80, 80))
                tk_img = ImageTk.PhotoImage(img)
                self.thumbnails.append(tk_img)

                label = tk.Label(self.preview_frame, image=tk_img)
                label.grid(row=i // cols, column=i % cols, padx=5, pady=5)
            except:
                pass

    def generate(self):
        if not self.files:
            messagebox.showerror("Error", "No images added.")
            return

        folder_name = self.folder_name.get()
        display_name = self.display_name.get()
        description = self.description.get()
        author = self.author.get()

        documents = os.path.join(os.path.expanduser("~"), "Documents")
        base_path = os.path.join(documents, folder_name)

        os.makedirs(os.path.join(base_path, "Color Textures"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "Textures"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "Shadow Textures"), exist_ok=True)
        os.makedirs(os.path.join(base_path, "Shape Textures"), exist_ok=True)

        # pack_info.txt
        with open(os.path.join(base_path, "pack_info.txt"), "w") as f:
            f.write(PACK_TEMPLATE % (display_name, description, author))

        total = len(self.files)
        self.progress["maximum"] = total

        for i, file in enumerate(self.files):
            name = os.path.splitext(os.path.basename(file))[0]
            dest_img = os.path.join(base_path, "Textures", name + ".png")

            try:
                img = Image.open(file).convert("RGBA")
                img.save(dest_img, "PNG")
            except Exception as e:
                print(f"Error: {e}")
                continue

            txt_path = os.path.join(base_path, "Color Textures", name + ".txt")
            with open(txt_path, "w") as f:
                f.write(COLOR_TEMPLATE % (name, name))

            # Update progress bar
            self.progress["value"] = i + 1
            self.root.update_idletasks()

        messagebox.showinfo("Done", "Pack created successfully!")

# --- Run ---
root = TkinterDnD.Tk()
app = App(root)
root.mainloop()