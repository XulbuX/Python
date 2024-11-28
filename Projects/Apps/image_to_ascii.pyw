# pip install customtkinter pillow

import customtkinter as ctk
from tkinter import font as tkfont
from PIL import Image
import os


INIT_BR_CHARS = " .,:;!vlLFE#$"


class ASCIIArtApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ASCII Art Generator")
        self.geometry("600x700")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.file_path = None
        self.color_mode = ctk.BooleanVar(value=False)

        # FONT SIZE TRACKING
        self.current_font_size = 6
        self.current_font_family = "Consolas"

        self.create_widgets()

        # BIND MOUSE WHEEL WITH CTRL KEY
        self.output_text.bind("<Control-MouseWheel>", self.zoom)

    def create_widgets(self):
        # FILE SELECTION
        self.file_button = ctk.CTkButton(
            self, text="Select Image", command=self.select_file
        )
        self.file_button.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        # SETTINGS FRAME
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        # CONTRAST SLIDER
        self.contrast_label = ctk.CTkLabel(settings_frame, text="Contrast:")
        self.contrast_label.grid(row=0, column=0, padx=10, pady=5)
        self.contrast_slider = ctk.CTkSlider(
            settings_frame,
            from_=0.5,
            to=2.0,
            number_of_steps=30,
            command=self.update_ascii,
        )
        self.contrast_slider.grid(row=0, column=1, padx=10, pady=5)
        self.contrast_slider.set(1.0)

        # ASCII CHARACTERS ENTRY
        self.chars_label = ctk.CTkLabel(settings_frame, text="ASCII Chars:")
        self.chars_label.grid(row=1, column=0, padx=10, pady=5)
        self.chars_entry = ctk.CTkEntry(settings_frame)
        self.chars_entry.grid(row=1, column=1, padx=10, pady=5)
        self.chars_entry.insert(0, INIT_BR_CHARS)
        self.chars_entry.bind("<KeyRelease>", self.update_ascii)

        # FONT SELECTION
        self.font_label = ctk.CTkLabel(settings_frame, text="Font:")
        self.font_label.grid(row=2, column=0, padx=10, pady=5)
        self.font_combobox = ctk.CTkComboBox(
            settings_frame, values=self.get_monospace_fonts(), command=self.update_ascii
        )
        self.font_combobox.grid(row=2, column=1, padx=10, pady=5)
        self.font_combobox.set("Consolas")

        # COLOR TOGGLE
        self.color_label = ctk.CTkLabel(settings_frame, text="Display in Color:")
        self.color_label.grid(row=3, column=0, padx=10, pady=5)
        self.color_switch = ctk.CTkSwitch(
            settings_frame, text="", variable=self.color_mode, command=self.update_ascii
        )
        self.color_switch.grid(row=3, column=1, padx=10, pady=5)

        # OUTPUT TEXT BOX
        self.output_text = ctk.CTkTextbox(self, wrap="none", font=("Consolas", 10))
        self.output_text.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

    def get_monospace_fonts(self):
        monospace_fonts = []
        for font_name in tkfont.families():
            if tkfont.Font(family=font_name, size=10).metrics("fixed"):
                monospace_fonts.append(font_name)
        return monospace_fonts

    def select_file(self):
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if file_path:
            self.file_path = file_path
            self.file_button.configure(text=os.path.basename(file_path))
            self.update_ascii()

    def update_ascii(self, *args):
        if not self.file_path:
            self.output_text.delete("1.0", "end")
            self.output_text.insert("1.0", "Please select an image file first.")
            return

        # LOAD AND PROCESS THE IMAGE
        img = Image.open(self.file_path)
        width, height = img.size
        aspect_ratio = height / width
        new_width = 100
        new_height = int(aspect_ratio * new_width * 0.55)
        img = img.resize((new_width, new_height))
        img = img.convert("RGB")

        # APPLY CONTRAST
        contrast = self.contrast_slider.get()
        img = img.point(lambda p: p * contrast)

        # GET ASCII CHARACTERS
        chars = self.chars_entry.get()
        if not chars:
            chars = INIT_BR_CHARS

        # GENERATE ASCII ART
        self.output_text.delete("1.0", "end")

        # UPDATE FONT BASED ON CURRENT SETTINGS
        self.current_font_family = self.font_combobox.get()
        self.output_text.configure(
            font=(self.current_font_family, self.current_font_size)
        )

        for y in range(new_height):
            for x in range(new_width):
                r, g, b = img.getpixel((x, y))
                brightness = sum((r, g, b)) / 3
                char_index = int((brightness / 255) * (len(chars) - 1))
                char = chars[char_index]

                # CREATE A UNIQUE TAG FOR THIS CHARACTER
                tag = f"char_{y}_{x}"

                # INSERT THE CHARACTER
                self.output_text.insert("end", char)

                # IF COLOR MODE IS ON, APPLY COLOR TO THE CHARACTER
                if self.color_mode.get():
                    # CONVERT TO HEX COLOR
                    hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
                    self.output_text.tag_config(tag, foreground=hex_color)
                    self.output_text.tag_add(tag, f"end-2c", "end-1c")

            # Add newline
            self.output_text.insert("end", "\n")

    def zoom(self, event):
        # CTRL + MOUSE WHEEL FOR ZOOMING
        if event.delta > 0:
            self.increase_font_size()
        else:
            self.decrease_font_size()
        return "break"  # PREVENT DEFAULT SCROLLING

    def increase_font_size(self):
        if self.current_font_size < 30:  # SET A REASONABLE UPPER LIMIT
            self.current_font_size += 1
            self.output_text.configure(
                font=(self.current_font_family, self.current_font_size)
            )

    def decrease_font_size(self):
        if self.current_font_size > 3:  # SET A REASONABLE LOWER LIMIT
            self.current_font_size -= 1
            self.output_text.configure(
                font=(self.current_font_family, self.current_font_size)
            )


if __name__ == "__main__":
    app = ASCIIArtApp()
    app.mainloop()
