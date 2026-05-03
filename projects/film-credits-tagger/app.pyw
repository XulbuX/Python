from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional
from PIL import Image, ImageTk
import customtkinter as ctk  # type: ignore[no-stubs]
import subprocess
import webbrowser
import tempfile
import shutil
import json
import sys
import io

from theme import COLORS, get_system_theme, resolve_mono_font
from widgets import FieldEntry, MultilineEntry, ToolTip


class MetadataTaggerApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        self.title("Film Credits Tagger")
        self.resizable(False, False)
        self.geometry("800x520")

        # SET WINDOW/TASKBAR ICON
        _icon_path: Path = Path(__file__).resolve().parent / "assets" / "img" / "FilmCreditsTagger.png"
        self._icon_ico_path: Optional[Path] = None
        if _icon_path.is_file():
            _pil_icon: Image.Image = Image.open(str(_icon_path))
            if sys.platform == "win32":
                _ico_tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
                _ico_tmp.close()
                _pil_icon.save(_ico_tmp.name, format="ICO", sizes=[(512, 512), (256, 256), (128, 128), (64, 64)])
                self._icon_ico_path = Path(_ico_tmp.name)
                self.after(201, lambda: self.iconbitmap(str(self._icon_ico_path)))
            else:
                self._icon_photo: ImageTk.PhotoImage = ImageTk.PhotoImage(_pil_icon)
                self.after(201, lambda: self.wm_iconphoto(True, self._icon_photo))

        # CHECK FOR EXIFTOOL
        self.exiftool_path: Optional[str] = shutil.which("exiftool")

        self.selected_files: list[str] = []
        self.cover_art_path: Optional[str] = None
        self.cover_art_embed_path: Optional[str] = None  # TEMP FILE WITH RESIZED VERSION
        self.cover_preview_image: Optional[ctk.CTkImage] = None
        self._current_theme: str = get_system_theme()

        ################################################## UI LAYOUT ##################################################
        PAD: int = 16

        #################### TWO-COLUMN ROOT FRAME ####################
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)

        self.left_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent", width=350)
        self.left_panel.pack(side="left", fill="y")
        self.left_panel.pack_propagate(False)

        self.sep_v = ctk.CTkFrame(self.main_frame, width=1)
        self.sep_v.pack(side="left", fill="y")

        self.right_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.right_panel.pack(side="left", fill="both", expand=True)

        #################### SELECT MEDIA SECTION ####################
        self.sec1 = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.sec1.pack(fill="x", padx=PAD, pady=(PAD - 6, PAD))
        self.sec1.grid_columnconfigure(1, weight=1)

        self.lbl_section1 = ctk.CTkLabel(self.sec1, text="Select Media", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_section1.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.btn_select_files = ctk.CTkButton(self.sec1, text="Select Video File(s)", command=self.select_files)
        self.btn_select_files.grid(row=1, column=0, pady=5, sticky="w")

        self.lbl_files = ctk.CTkLabel(self.sec1, text="0 files selected")
        self.lbl_files.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="w")

        self.btn_select_cover = ctk.CTkButton(
            self.sec1, text="Select Cover Art", command=self.select_cover_art, border_width=1
        )
        self.btn_select_cover.grid(row=2, column=0, pady=5, sticky="nw")

        self.frame_cover_preview = ctk.CTkFrame(self.sec1, fg_color="transparent")
        self.frame_cover_preview.grid(row=3, column=0, columnspan=2, pady=(5, 0), sticky="w")

        THUMB_CONTAINER: int = 80
        self.frame_thumb_container = ctk.CTkFrame(
            self.frame_cover_preview, width=THUMB_CONTAINER, height=THUMB_CONTAINER, corner_radius=0, border_width=1
        )
        self.frame_thumb_container.pack(side="left", padx=(0, 10))
        self.frame_thumb_container.pack_propagate(False)

        self.lbl_cover_thumb = ctk.CTkLabel(
            self.frame_thumb_container, text="No cover\nart selected", font=ctk.CTkFont(size=11), fg_color="transparent"
        )
        self.lbl_cover_thumb.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_cover_info = ctk.CTkLabel(self.frame_cover_preview, text="", justify="left")
        self.lbl_cover_info.pack(side="left", anchor="nw")

        # SEPARATOR
        self.sep1 = ctk.CTkFrame(self.left_panel, height=1)
        self.sep1.pack(fill="x")

        #################### LOAD/SAVE DATA SECTION ####################
        self.sec2 = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.sec2.pack(fill="x", padx=PAD, pady=(PAD - 6, PAD))

        self.lbl_section2 = ctk.CTkLabel(self.sec2, text="Load/Save Data", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_section2.pack(anchor="nw", pady=(0, 8))

        self.btn_load_template = ctk.CTkButton(self.sec2, text="Load JSON Template", command=self.load_template)
        self.btn_load_template.pack(fill="x", pady=(0, 6))

        self.btn_save_template = ctk.CTkButton(self.sec2, text="Save JSON Template", command=self.save_template)
        self.btn_save_template.pack(fill="x", pady=(0, 6))

        self.btn_load_from_video = ctk.CTkButton(
            self.sec2,
            text="Load from Video",
            command=self.load_from_video,
            state="normal" if self.exiftool_path else "disabled",
            border_width=1
        )
        self.btn_load_from_video.pack(fill="x")

        #################### APPLY BUTTON –OR– EXIFTOOL NOT FOUND BANNER ####################
        if self.exiftool_path:
            self.btn_apply = ctk.CTkButton(self.left_panel, text="Apply Metadata", command=self.apply_metadata, height=40)
            self.btn_apply.pack(fill="x", padx=PAD, pady=(0, PAD), side="bottom")
        else:
            self.btn_apply = None  # type: ignore[assignment]
            self._banner_labels: list[tuple[ctk.CTkLabel, str]] = []  # (widget, color_key)
            self._banner = ctk.CTkFrame(self.left_panel, border_width=1, corner_radius=8)
            self._banner.pack(fill="x", padx=PAD, pady=(0, PAD), side="bottom")
            lbl_title = ctk.CTkLabel(
                self._banner,
                text="ExifTool is not installed or not in PATH",
                font=ctk.CTkFont(size=13, weight="bold"),
                wraplength=290,
                justify="left"
            )
            lbl_title.pack(anchor="w", padx=10, pady=(2, 0))
            self._banner_labels.append((lbl_title, "destructive_foreground"))
            lbl_desc = ctk.CTkLabel(
                self._banner,
                text="ExifTool is required to write metadata to video files. Please install it and restart the app.",
                wraplength=290,
                justify="left"
            )
            lbl_desc.pack(anchor="w", padx=10, pady=(4, 0))
            self._banner_labels.append((lbl_desc, "destructive_muted"))
            lbl_cmd = ctk.CTkLabel(self._banner, text="exiftool.org", font=resolve_mono_font(12), cursor="hand2")
            lbl_cmd.pack(anchor="w", padx=10, pady=(4, 8))
            lbl_cmd.bind("<Button-1>", lambda _: webbrowser.open("https://exiftool.org"))  # type: ignore[misc]
            self._banner_labels.append((lbl_cmd, "link"))

        #################### METADATA FIELDS SECTION ####################
        self.sec3_header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.sec3_header.pack(fill="x", padx=PAD, pady=(PAD - 6, 0))
        self.sw_clear_empty = ctk.CTkSwitch(
            self.sec3_header, text="Clear empty fields", width=0, command=self._on_clear_toggle
        )
        self.sw_clear_empty.pack(side="right", anchor="e", pady=(0, 5))
        ToolTip(
            self.sw_clear_empty,
            "ON – empty fields and no cover art will delete those tags from the file when applying.\n"
            "OFF – only filled-in fields are written; existing tags in the file are left untouched.",
        )
        self.lbl_section3 = ctk.CTkLabel(self.sec3_header, text="Metadata", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_section3.pack(side="left", anchor="w", pady=(0, 5))

        self.sec3 = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        self.sec3.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))
        self.sec3.grid_columnconfigure(1, weight=1)

        # AUTO-HIDE SCROLLBAR WHEN CONTENT FITS
        _orig_set = self.sec3._scrollbar.set

        def _on_yscroll(first: str, last: str) -> None:
            _orig_set(first, last)
            if float(first) <= 0.0 and float(last) >= 1.0:
                self.sec3._scrollbar.grid_remove()
            else:
                self.sec3._scrollbar.grid()

        self.sec3._parent_canvas.configure(yscrollcommand=_on_yscroll)
        self.after_idle(lambda: _on_yscroll(*self.sec3._parent_canvas.yview()))

        # EACH FIELD LISTS ITS TAGS IN PRIORITY ORDER: CROSS-PLATFORM FIRST, OS-SPECIFIC APPENDED.
        # ItemList TAGS WRITE STANDARD iTunes/QuickTime ATOMS (©dir, ©wrt, ©prd, …) RECOGNIZED BY
        # macOS, VLC, MPV AND LINUX MEDIA PLAYERS. MICROSOFT TAGS COVER WINDOWS EXPLORER / WMP.
        self.fields: dict[str, tuple[str, ...]] = {
            "Title": ("-ItemList:Title", ),
            "Subtitle": ("-ItemList:Description", "-Microsoft:Subtitle"),
            "Subject": ("-Microsoft:Subject", ),
            "Year": ("-ItemList:ContentCreateDate", ),
            "Genre(s)": ("-ItemList:Genre", ),
            "Director(s)": ("-ItemList:Director", "-Microsoft:Director"),
            "Writer(s)": ("-ItemList:Composer", "-Microsoft:Writer"),
            "Producer(s)": ("-ItemList:Producer", "-Microsoft:Producer"),
            "Contributing Artist(s)": ("-ItemList:Artist", ),
            "Comment": ("-ItemList:Comment", ),
        }

        self.entries: dict[str, FieldEntry] = {}
        self._field_labels: list[ctk.CTkLabel] = []

        MULTI_FIELDS: frozenset[str] = frozenset({
            "Genre(s)", "Director(s)", "Writer(s)", "Producer(s)", "Contributing Artist(s)"
        })
        NEWLINE_FIELDS: frozenset[str] = frozenset({"Comment"})

        for row_idx, (label_text, tags) in enumerate(self.fields.items(), start=0):
            lbl = ctk.CTkLabel(self.sec3, text=label_text)
            lbl.grid(row=row_idx, column=0, pady=(4, 4), sticky="nw")
            self._field_labels.append(lbl)

            if label_text in MULTI_FIELDS:
                entry_widget: ctk.CTkEntry = MultilineEntry(self.sec3, border_width=1, wrap="word")  # type: ignore[assignment]
            elif label_text in NEWLINE_FIELDS:
                entry_widget = MultilineEntry(  # type: ignore[assignment]
                    self.sec3, allow_newlines=True, border_width=1, wrap="word"
                )
            else:
                entry_widget = ctk.CTkEntry(self.sec3, border_width=1)
            entry_widget.grid(row=row_idx, column=1, padx=(10, 0), pady=(4, 4), sticky="ew")
            self.entries[label_text] = {"tags": tags, "widget": entry_widget}

        self._apply_theme()
        self.after(2000, self._poll_theme)

    def select_files(self) -> None:
        filenames = filedialog.askopenfilenames(
            title="Select Video File(s)",
            filetypes=[("Video Files", "*.mp4 *.mov *.m4v *.m4a *.3gp *.3g2"), ("All Files", "*.*")]
        )
        if filenames:
            self.selected_files = list(filenames)
            self.lbl_files.configure(
                text=f"{len(self.selected_files)} file{'' if len(self.selected_files) == 1 else's'} selected",
                text_color=COLORS[self._current_theme]["foreground"]
            )

    def select_cover_art(self) -> None:
        filename = filedialog.askopenfilename(title="Select Cover Art", filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if not filename:
            return
        self.cover_art_path = filename
        self._set_cover_from_image(Image.open(filename).convert("RGB"))

    def _set_cover_from_image(self, img: Image.Image) -> None:
        orig_w, orig_h = img.size

        # RESIZE TO MAX 400px (WHAT WILL ACTUALLY BE EMBEDDED)
        MAX_EMBED: int = 400
        if max(orig_w, orig_h) > MAX_EMBED:
            embed_ratio: float = MAX_EMBED / max(orig_w, orig_h)
            embed_w: int = max(1, int(orig_w * embed_ratio))
            embed_h: int = max(1, int(orig_h * embed_ratio))
        else:
            embed_w, embed_h = orig_w, orig_h
        embed_img: Image.Image = img.resize((embed_w, embed_h), Image.LANCZOS)

        # MEASURE JPEG SIZE AFTER COMPRESSION
        buf: io.BytesIO = io.BytesIO()
        embed_img.save(buf, format="JPEG", quality=85)
        embed_kb: int = max(1, round(buf.tell() / 1024))

        # SAVE RESIZED VERSION TO TEMP FILE FOR EXIFTOOL
        if self.cover_art_embed_path and Path(self.cover_art_embed_path).exists():
            Path(self.cover_art_embed_path).unlink()
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(buf.getvalue())
        tmp.close()
        self.cover_art_embed_path = tmp.name

        # SCALE TO FIT WITHIN CONTAINER (MINUS BORDER), PRESERVE ASPECT RATIO
        THUMB: int = int(self.frame_thumb_container.cget("width")) - 3
        fit_scale: float = min(THUMB / embed_w, THUMB / embed_h)
        fit_w: int = max(1, int(embed_w * fit_scale))
        fit_h: int = max(1, int(embed_h * fit_scale))
        thumb_img: Image.Image = embed_img.resize((fit_w, fit_h), Image.LANCZOS)

        self.cover_preview_image = ctk.CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(fit_w, fit_h))
        self.lbl_cover_thumb.configure(image=self.cover_preview_image, text="")
        self.lbl_cover_info.configure(
            text=f"image/jpeg\n{embed_w}\u00d7{embed_h}\n{embed_kb} KB\nFront Cover",
            text_color=COLORS[self._current_theme]["foreground"]
        )

    def _apply_theme(self) -> None:
        theme: str = get_system_theme()
        c: dict[str, str] = dict(COLORS[theme])

        ctk.set_appearance_mode(theme)
        self.configure(fg_color=c["background"])

        self.main_frame.configure(fg_color=c["background"])
        self.left_panel.configure(fg_color=c["background"])
        self.right_panel.configure(fg_color=c["background"])

        self.sec1.configure(fg_color=c["background"])
        self.sec2.configure(fg_color=c["background"])
        self.sec3_header.configure(fg_color=c["background"])
        self.sec3.configure(
            fg_color=c["background"],
            scrollbar_button_color=c["secondary_border"],
            scrollbar_button_hover_color=c["secondary_hover"],
        )

        self.sep1.configure(fg_color=c["border"])
        self.sep_v.configure(fg_color=c["border"])

        self.lbl_section1.configure(text_color=c["foreground"])
        self.lbl_section2.configure(text_color=c["foreground"])
        self.lbl_section3.configure(text_color=c["foreground"])

        if self.cover_art_path:
            self.lbl_cover_info.configure(text_color=c["foreground"])
        self.lbl_cover_thumb.configure(text_color=c["placeholder_foreground"], fg_color=c["background"])
        self.lbl_files.configure(text_color=c["foreground"] if self.selected_files else c["placeholder_foreground"])
        self.frame_thumb_container.configure(fg_color=c["background"], border_color=c["border"])

        for lbl in self._field_labels:
            lbl.configure(text_color=c["muted_foreground"])

        self._current_theme = theme
        self._on_clear_toggle()  # APPLIES SWITCH COLORS BASED ON CURRENT STATE

        self.btn_select_files.configure(fg_color=c["card"], hover_color=c["card_hover"], text_color=c["card_foreground"])
        self.btn_select_cover.configure(
            fg_color=c["secondary"],
            hover_color=c["secondary_hover"],
            border_color=c["secondary_border"],
            text_color=c["secondary_foreground"]
        )
        self.btn_load_template.configure(fg_color=c["card"], hover_color=c["card_hover"], text_color=c["card_foreground"])
        self.btn_save_template.configure(fg_color=c["card"], hover_color=c["card_hover"], text_color=c["card_foreground"])
        self.btn_load_from_video.configure(
            fg_color=c["secondary"],
            hover_color=c["secondary_hover"],
            border_color=c["secondary_border"],
            text_color=c["secondary_foreground"]
        )

        if self.btn_apply:
            self.btn_apply.configure(fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["primary_foreground"])

        if hasattr(self, "_banner"):
            self._banner.configure(fg_color=c["destructive"], border_color=c["destructive_border"])
            for lbl, key in self._banner_labels:
                lbl.configure(text_color=c[key])

        for data in self.entries.values():
            widget = data["widget"]
            if isinstance(widget, MultilineEntry):
                widget.configure(
                    fg_color=c["background"],
                    border_color=c["secondary_border"],
                    text_color=c["foreground"],
                )
            else:
                widget.configure(
                    fg_color=c["background"],
                    border_color=c["secondary_border"],
                    text_color=c["foreground"],
                    placeholder_text_color=c["placeholder_foreground"],
                )

    def _on_clear_toggle(self) -> None:
        c = COLORS[self._current_theme]
        active = bool(self.sw_clear_empty.get())
        btn_color = c["foreground"]
        self.sw_clear_empty.configure(
            fg_color=c["destructive_border"] if active else c["secondary_border"],
            progress_color=c["primary"] if active else c["primary"],
            button_color=btn_color,
            button_hover_color=btn_color,
            text_color=c["destructive_muted"] if active else c["muted_foreground"],
        )

    def _poll_theme(self) -> None:
        if get_system_theme() != self._current_theme:
            self._apply_theme()
        self.after(2000, self._poll_theme)

    def save_template(self) -> None:
        # EXTRACT CURRENT VALUES FROM UI
        template_data: dict[str, str] = {}
        for label, data in self.entries.items():
            val = data["widget"].get().strip()
            if val:
                template_data[label] = val

        if not template_data:
            messagebox.showinfo("Empty", "No fields filled out to save.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON Files", "*.json")], title="Save Metadata Template"
        )

        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(template_data, f, indent=4)
                messagebox.showinfo("Saved", "Template saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save template:\n{e}")

    def load_from_video(self) -> None:
        filepath = filedialog.askopenfilename(
            title="Load Metadata from Video",
            filetypes=[("Video Files", "*.mp4 *.mov *.m4v *.m4a *.3gp *.3g2"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        assert self.exiftool_path is not None

        # BUILD READ COMMAND: REQUEST ONLY THE PRIMARY (CROSS-PLATFORM) TAG PER FIELD
        tag_args: list[str] = [tags[0].lstrip("-") for tags in self.fields.values()]
        command: list[str] = [self.exiftool_path, "-json"] + [f"-{t}" for t in tag_args] + [filepath]

        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=True)
            records: list[dict[str, object]] = json.loads(result.stdout)
            if not records:
                messagebox.showinfo("No Data", "ExifTool returned no metadata for this file.")
                return

            meta: dict[str, object] = records[0]

            # MAP SHORT TAG NAME → LABEL, THEN POPULATE ENTRIES
            short_key_to_label: dict[str, str] = {
                tags[0].split(":", 1)[-1].lstrip("-"): label
                for label, tags in self.fields.items()
            }
            for key, value in meta.items():
                if key in short_key_to_label and value:
                    label = short_key_to_label[key]
                    widget = self.entries[label]["widget"]
                    widget.delete(0, "end")
                    # ADD SPACES AROUND ExifTool's "/" LIST SEPARATOR FOR READABILITY
                    display_val = str(value).replace("/", " / ")
                    widget.insert(0, display_val)

            # EXTRACT EMBEDDED COVER ART, IF ANY
            cover_result = subprocess.run([self.exiftool_path, "-b", "-ItemList:CoverArt", filepath], capture_output=True)
            if cover_result.stdout:
                try:
                    self.cover_art_path = filepath
                    self._set_cover_from_image(Image.open(io.BytesIO(cover_result.stdout)).convert("RGB"))
                except Exception:
                    pass  # MALFORMED COVER DATA; SILENTLY IGNORE

        except subprocess.CalledProcessError as e:
            messagebox.showerror("ExifTool Error", f"Failed to read metadata:\n{e.stderr}")
        except (json.JSONDecodeError, KeyError) as e:
            messagebox.showerror("Parse Error", f"Could not parse ExifTool output:\n{e}")

    def load_template(self) -> None:
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Load Metadata Template")
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    template_data: dict[str, str] = json.load(f)

                # CLEAR EXISTING ENTRIES AND INSERT NEW ONES
                for label, data in self.entries.items():
                    data["widget"].delete(0, "end")
                    if label in template_data:
                        data["widget"].insert(0, template_data[label])

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load template:\n{e}")

    def apply_metadata(self) -> None:
        if not self.exiftool_path:
            return
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select at least one MP4 file.")
            return

        command: list[str] = [self.exiftool_path, "-overwrite_original"]
        tags_added: int = 0

        clear_mode: bool = bool(self.sw_clear_empty.get())

        # [1] ADD TEXT TAGS
        for data in self.entries.values():
            val = data["widget"].get().strip()
            if val:
                for tag in data["tags"]:
                    command.append(f"{tag}={val}")
                tags_added += 1
            elif clear_mode:
                for tag in data["tags"]:
                    command.append(f"{tag}=")  # EMPTY ASSIGNMENT DELETES THE TAG
                tags_added += 1

        # [2] ADD COVER ART TAG
        if self.cover_art_embed_path:
            command.append(f"-ItemList:CoverArt<={self.cover_art_embed_path}")
            tags_added += 1
        elif clear_mode:
            command.append("-ItemList:CoverArt=")  # REMOVE EXISTING COVER ART
            tags_added += 1

        if tags_added == 0:
            messagebox.showinfo("No Input", "No metadata or cover art provided.")
            return

        # [3] APPEND ALL SELECTED FILES TO THE COMMAND
        command.extend(self.selected_files)

        if self.btn_apply:
            self.btn_apply.configure(text="Processing...", state="disabled")
        self.update()

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            messagebox.showinfo("Success", f"Successfully updated {len(self.selected_files)} file(s)!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("ExifTool Error", f"An error occurred:\n{e.stderr}")
        finally:
            if self.btn_apply:
                self.btn_apply.configure(text="Apply Metadata to Batch", state="normal")


if __name__ == "__main__":
    ctk.set_appearance_mode(get_system_theme())
    ctk.set_default_color_theme("blue")

    # ON WINDOWS, SET THE APP USER MODEL ID BEFORE CREATING THE WINDOW SO THE
    # TASKBAR GROUPS THE APP UNDER ITS OWN ICON RATHER THAN THE PYTHON INTERPRETER
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FilmCreditsTagger.app")
        except Exception:
            pass

    app = MetadataTaggerApp()

    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.destroy()

    # CLEAN UP TEMP FILES
    if app.cover_art_embed_path and Path(app.cover_art_embed_path).exists():
        Path(app.cover_art_embed_path).unlink()
    if app._icon_ico_path and app._icon_ico_path.exists():
        app._icon_ico_path.unlink()
