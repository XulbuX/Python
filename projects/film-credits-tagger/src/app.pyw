# pyright: basic
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional
from PIL import Image
import customtkinter as ctk
import subprocess
import webbrowser
import threading
import tempfile
import ctypes
import shutil
import json
import sys
import io
import re

# PREVENT A CONSOLE WINDOW FROM FLASHING WHEN CALLING EXTERNAL PROCESSES
_POPEN_FLAGS: dict = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}

from consts import COVER_ART_FILE_TYPES, VIDEO_FILE_TYPES, APP_ICON_PNG, COLORS, FIELDS, FIELDS_FLAT, FieldEntry, FieldType, ValueType  # type: ignore[missing-import]
from helpers import resolve_mono_font, get_system_theme, normalize_multi, validate_field, parse_date, exiftool_date_to_display, setup_window_icon  # type: ignore[missing-import]
from widgets import MultilineEntry, SpinnerButton, ToolTip, bind_clean_paste, render_svg_icon  # type: ignore[missing-import]


class MetadataTaggerApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        self.title("Film Credits Tagger")
        self.resizable(False, False)

        # CENTERED FIXED-SIZE WINDOW
        ww, wh = 820, 520
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{ww}x{wh}+{(sw - ww) // 2}+{(sh - wh) // 2}")

        # SET WINDOW/TASKBAR ICON
        self._temp_ico_path: Optional[Path] = setup_window_icon(self, APP_ICON_PNG)

        # CHECK FOR EXIFTOOL
        self.exiftool_path: Optional[str] = shutil.which("exiftool")

        self.selected_files: list[str] = []

        self.cover_art_path: Optional[str] = None
        self.cover_art_embed_path: Optional[str] = None  # TEMP FILE WITH RESIZED VERSION
        self.cover_preview_image: Optional[ctk.CTkImage] = None
        self._cover_video_source: Optional[str] = None  # SET WHEN COVER CAME FROM A VIDEO (NOT AN IMAGE FILE)

        self._current_theme: str = get_system_theme()

        ################################################## UI LAYOUT ##################################################
        PAD: int = 16

        #################### TWO-COLUMN ROOT FRAME ####################
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)

        self.left_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent", width=340)
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
        self.btn_select_files.grid(row=1, column=0, pady=(0, 6), sticky="w")

        self.lbl_files = ctk.CTkLabel(self.sec1, text="0 files selected")
        self.lbl_files.grid(row=1, column=1, padx=(10, 0), pady=(0, 6), sticky="w")

        self.btn_select_cover = ctk.CTkButton(
            self.sec1, text="Select Cover Art", command=self.select_cover_art, border_width=1
        )
        self.btn_select_cover.grid(row=2, column=0, pady=6, sticky="nw")

        self.btn_remove_cover = ctk.CTkButton(
            self.sec1, text="", width=28, height=28, corner_radius=6, border_width=0, command=self._remove_cover
        )
        self.btn_remove_cover.grid(row=2, column=1, padx=(4, 0), pady=6, sticky="w")
        self.btn_remove_cover.grid_remove()  # HIDDEN UNTIL A COVER IS SELECTED
        ToolTip(self.btn_remove_cover, "Remove cover art")

        self.frame_cover_preview = ctk.CTkFrame(self.sec1, fg_color="transparent")
        self.frame_cover_preview.grid(row=3, column=0, columnspan=2, pady=(6, 0), sticky="w")

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

        self.btn_load_template = SpinnerButton(self.sec2, text="Load JSON Template", command=self.load_template)
        self.btn_load_template.pack(fill="x", pady=(0, 6))

        self.btn_save_template = ctk.CTkButton(self.sec2, text="Save JSON Template", command=self.save_template)
        self.btn_save_template.pack(fill="x", pady=(0, 6))

        self.btn_load_from_video = SpinnerButton(
            self.sec2,
            text="Load from Video",
            command=self.load_from_video,
            state="disabled",  # ENABLED AFTER _verify_exiftool CONFIRMS
            border_width=1
        )
        self.btn_load_from_video.pack(fill="x", pady=(6, 0))

        #################### APPLY BUTTON –OR– EXIFTOOL NOT FOUND BANNER ####################
        if self.exiftool_path:
            self._apply_bottom = ctk.CTkFrame(self.left_panel, fg_color="transparent")
            self._apply_bottom.pack(fill="x", side="bottom")
            self._apply_bottom.grid_columnconfigure(0, weight=1)
            self.btn_apply = SpinnerButton(self._apply_bottom, text="Apply Metadata", command=self.apply_metadata, height=40)
            self.btn_apply.grid(row=1, column=0, padx=PAD, pady=(0, PAD), sticky="ew")
            self.progress_bar = ctk.CTkProgressBar(self._apply_bottom, height=4, corner_radius=4)
            self.progress_bar.grid(row=0, column=0, padx=PAD, pady=(PAD // 2, 10), sticky="ew")
            self.progress_bar.set(0)
            self.progress_bar.grid_remove()
            self._progress_anim_id: Optional[str] = None
            self._progress_anim_current: float = 0.0
        else:
            self.btn_apply = None
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
            lbl_cmd.bind("<Button-1>", lambda _: webbrowser.open("https://exiftool.org"))
            self._banner_labels.append((lbl_cmd, "link"))

        #################### METADATA FIELDS SECTION ####################
        self.sec3_header = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.sec3_header.pack(fill="x", padx=PAD, pady=(PAD - 6, 0))
        self.sw_clear_empty = ctk.CTkCheckBox(
            self.sec3_header,
            text="Clear empty fields",
            width=0,
            command=self._on_clear_toggle,
            checkbox_width=18,
            checkbox_height=18,
            border_width=1,
            corner_radius=5
        )
        self.sw_clear_empty.pack(side="right", anchor="e", pady=(0, 6))
        ToolTip(
            self.sw_clear_empty,
            "ON – Empty fields and no cover art will delete those tags from the file when applying.\n"
            "OFF – Only filled-in fields are written; existing tags in the file are left untouched.",
        )
        self.btn_reset_all = ctk.CTkButton(
            self.sec3_header, text="", width=28, height=28, corner_radius=6, border_width=0, command=self.reset_all
        )
        self.btn_reset_all.pack(side="right", padx=(0, 12), pady=(0, 6))
        ToolTip(self.btn_reset_all, "Reset all fields")
        self.lbl_section3 = ctk.CTkLabel(self.sec3_header, text="Metadata", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_section3.pack(side="left", anchor="w", pady=(0, 6))

        self.sec3 = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent", corner_radius=0)
        self.sec3.pack(fill="both", expand=True)  # PADDING WILL BE ADDED DEPENDING ON SCROLLBAR VISIBILITY
        self.sec3.grid_columnconfigure(1, weight=1)
        self.sec3._scrollbar.configure(width=14)

        # AUTO-HIDE SCROLLBAR WHEN CONTENT FITS
        _orig_set = self.sec3._scrollbar.set

        def _on_yscroll(first: float, last: float) -> None:
            _orig_set(first, last)
            if float(first) <= 0.0 and float(last) >= 1.0:
                self.sec3._scrollbar.grid_remove()
                self.sec3._parent_frame.pack(padx=PAD)
            else:
                self.sec3._scrollbar.grid()
                self.sec3._parent_frame.pack(padx=(PAD, PAD - 14))

        self.sec3._parent_canvas.configure(yscrollcommand=_on_yscroll)

        # SPEED UP MOUSEWHEEL SCROLLING (3 UNITS PER NOTCH INSTEAD OF DEFAULT 1)
        _sec3_canvas = self.sec3._parent_canvas

        def _on_sec3_fast_scroll(event: object) -> None:
            _sec3_canvas.yview_scroll(int(-48 * (event.delta / 120)), "units")  # type: ignore[attr-defined]

        _sec3_canvas.bind("<Enter>", lambda _: _sec3_canvas.bind_all("<MouseWheel>", _on_sec3_fast_scroll), add=True)

        self.entries: dict[str, FieldEntry] = {}
        self._field_labels: list[ctk.CTkLabel] = []
        self._section_labels: list[ctk.CTkLabel] = []
        self._section_seps: list[ctk.CTkFrame] = []

        row_idx: int = 0
        for section_idx, (section_title, section_fields) in enumerate(FIELDS.items()):
            if section_idx > 0:
                sep = ctk.CTkFrame(self.sec3, height=1)
                sep.grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=(8, 0))
                self._section_seps.append(sep)
                row_idx += 1

            section_lbl = ctk.CTkLabel(self.sec3, text=section_title, font=ctk.CTkFont(size=12, weight="bold"))
            section_lbl.grid(row=row_idx, column=0, columnspan=2, sticky="w", pady=(6, 2))
            self._section_labels.append(section_lbl)
            row_idx += 1

            for label_text, field_def in section_fields.items():
                lbl = ctk.CTkLabel(self.sec3, text=label_text)
                lbl.grid(row=row_idx, column=0, pady=(4, 4), sticky="nw")
                self._field_labels.append(lbl)

                if field_def["field_type"] == FieldType.EXPANDING:
                    entry_widget: ctk.CTkEntry = MultilineEntry(self.sec3, border_width=1, wrap="word", placeholder_text=field_def.get("placeholder", ""))  # type: ignore[assignment]
                elif field_def["field_type"] == FieldType.MULTILINE:
                    entry_widget = MultilineEntry(  # type: ignore[assignment]
                        self.sec3, allow_newlines=True, always_expanded=True, border_width=1, wrap="word"
                    )
                else:
                    entry_widget = ctk.CTkEntry(self.sec3, border_width=1)
                    bind_clean_paste(entry_widget._entry)
                    if ph := field_def.get("placeholder"):
                        entry_widget.configure(placeholder_text=ph)
                entry_widget.grid(row=row_idx, column=1, padx=(PAD, 0), pady=(4, 4), sticky="ew")
                self.entries[label_text] = {"tags": field_def["tags"], "widget": entry_widget}
                row_idx += 1

        # SPACER SO THE LAST FIELD HAS BREATHING ROOM WHEN SCROLLED TO THE BOTTOM
        spacer = ctk.CTkFrame(self.sec3, fg_color="transparent", height=PAD)
        spacer.grid(row=row_idx, column=0, columnspan=2, sticky="ew")

        self._apply_theme()
        self.after(2000, self._poll_theme)

        self._applying: bool = False

        # VERIFY EXIFTOOL IN THE BACKGROUND SO THE UI IS FULLY RENDERED FIRST
        if self.exiftool_path and self.btn_apply:
            self.btn_apply.start(COLORS[self._current_theme]["primary_foreground"])
            threading.Thread(target=self._verify_exiftool, daemon=True).start()

    def select_files(self) -> None:
        if filenames := filedialog.askopenfilenames(title="Select Video File(s)", filetypes=VIDEO_FILE_TYPES):
            self.selected_files = list(filenames)
            self.lbl_files.configure(
                text=f"{len(self.selected_files)} file{'' if len(self.selected_files) == 1 else's'} selected",
                text_color=COLORS[self._current_theme]["foreground"]
            )

    def select_cover_art(self) -> None:
        if not (filename := filedialog.askopenfilename(title="Select Cover Art", filetypes=COVER_ART_FILE_TYPES)):
            return

        try:
            img = Image.open(filename).convert("RGB")
        except Exception as err:
            messagebox.showerror("Invalid Image", f"Could not open image file:\n{err}")
            return

        self.cover_art_path = filename
        self._set_cover_from_image(img)

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
        embed_img: Image.Image = img.resize((embed_w, embed_h), Image.LANCZOS)  # type: ignore[attr-defined]

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
        thumb_img: Image.Image = embed_img.resize((fit_w, fit_h), Image.LANCZOS)  # type: ignore[attr-defined]

        self.cover_preview_image = ctk.CTkImage(light_image=thumb_img, dark_image=thumb_img, size=(fit_w, fit_h))
        self.lbl_cover_thumb.configure(image=self.cover_preview_image, text="")
        self.lbl_cover_info.configure(
            text=f"image/jpeg\n{embed_w}\u00d7{embed_h}\n{embed_kb} KB\nFront Cover",
            text_color=COLORS[self._current_theme]["foreground"]
        )
        self.btn_remove_cover.grid()  # SHOW THE REMOVE BUTTON NOW THAT A COVER IS LOADED

    def _remove_cover(self) -> None:
        """Clear the selected cover art and reset the cover preview."""
        if self.cover_art_path is None and self.cover_preview_image is None and self._cover_video_source is None:
            self.btn_remove_cover.grid_remove()
            return  # NOTHING TO CLEAR; ALSO PREVENTS stale-PhotoImage TclError ON REPEAT CALLS

        self.cover_art_path = None
        self._cover_video_source = None
        if self.cover_art_embed_path and Path(self.cover_art_embed_path).exists():
            Path(self.cover_art_embed_path).unlink()

        self.cover_art_embed_path = None
        c = COLORS[self._current_theme]

        # NULL OUT BOTH CTkLabel'S _image AND THE UNDERLYING tk.Label's image OPTION SO THAT
        # NO STALE PhotoImage REFERENCE CAUSES TclError WHEN TKINTER VALIDATES OPTIONS ON REDRAW.
        self.lbl_cover_thumb._image = None  # type: ignore[attr-defined]

        try:
            self.lbl_cover_thumb._label.configure(image="")  # type: ignore[attr-defined]
        except Exception:
            pass

        self.lbl_cover_thumb.configure(text="No cover\nart selected", text_color=c["placeholder_foreground"])
        self.lbl_cover_info.configure(text="", text_color=c["placeholder_foreground"])
        self.cover_preview_image = None
        self.btn_remove_cover.grid_remove()

    def reset_all(self) -> None:
        """Clear all metadata fields and remove the cover art."""
        for data in self.entries.values():
            widget = data["widget"]

            if isinstance(widget, MultilineEntry):
                widget.delete(0, "end")
            elif not getattr(widget, "_placeholder_text_active", False):
                # FIELD HAS REAL CONTENT: CLEAR IT, THEN IMMEDIATELY RESTORE THE PLACEHOLDER
                # (WITHOUT THIS, PLACEHOLDER ONLY REAPPEARS ON THE NEXT FOCUS-OUT EVENT)
                widget.delete(0, "end")
                if hasattr(widget, "_activate_placeholder"):
                    widget._activate_placeholder()

        self._remove_cover()

    def _apply_theme(self) -> None:
        self._current_theme = get_system_theme()
        c: dict[str, str] = dict(COLORS[self._current_theme])

        ctk.set_appearance_mode(self._current_theme)
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

        for lbl in self._section_labels:
            lbl.configure(text_color=c["foreground"])
        for sep in self._section_seps:
            sep.configure(fg_color=c["border"])
        for lbl in self._field_labels:
            lbl.configure(text_color=c["muted_foreground"])

        self._on_clear_toggle()
        self.sw_clear_empty.configure(
            fg_color=c["background"],
            hover_color=c["secondary_hover"],
            border_color=c["secondary_border"],
            checkmark_color=c["destructive_label"],
        )

        self.btn_select_files.configure(fg_color=c["card"], hover_color=c["card_hover"], text_color=c["card_foreground"])
        self.btn_select_cover.configure(
            fg_color=c["secondary"],
            hover_color=c["secondary_hover"],
            border_color=c["secondary_border"],
            text_color=c["secondary_foreground"]
        )
        self.btn_remove_cover.configure(
            width=28,
            height=28,
            image=render_svg_icon("x", 16, c["muted_foreground"]),
            fg_color="transparent",
            hover_color=c["secondary_hover"],
        )
        self.btn_load_template.configure(fg_color=c["card"], hover_color=c["card_hover"], text_color=c["card_foreground"])
        self.btn_save_template.configure(fg_color=c["card"], hover_color=c["card_hover"], text_color=c["card_foreground"])
        self.btn_load_from_video.configure(
            fg_color=c["secondary"],
            hover_color=c["secondary_hover"],
            border_color=c["secondary_border"],
            text_color=c["secondary_foreground"]
        )
        self.btn_reset_all.configure(
            width=28,
            height=28,
            image=render_svg_icon("refresh-ccw", 16, c["muted_foreground"]),
            fg_color="transparent",
            hover_color=c["secondary_hover"],
        )

        if self.btn_apply:
            self.btn_apply.configure(fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["primary_foreground"])
        if hasattr(self, "progress_bar"):
            self.progress_bar.configure(fg_color=c["secondary_hover"], progress_color=c["placeholder_foreground"])

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
                    placeholder_text_color=c["placeholder_foreground"],
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
        self.sw_clear_empty.configure(
            text_color=c["destructive_label"] if bool(self.sw_clear_empty.get()) else c["muted_foreground"],
        )

    def _verify_exiftool(self) -> None:
        """Verify ExifTool runs; called in a background thread."""
        ok = False
        if self.exiftool_path:
            try:
                subprocess.run([self.exiftool_path, "-ver"], capture_output=True, timeout=5, check=True, **_POPEN_FLAGS)
                ok = True
            except Exception:
                ok = False

        def _done() -> None:
            if not ok:
                self.exiftool_path = None
            if self.btn_apply:
                self.btn_apply.stop(state="normal" if ok else "disabled")
            self.btn_load_from_video.configure(state="normal" if ok else "disabled")

        self.after(0, _done)

    def _poll_theme(self) -> None:
        if get_system_theme() != self._current_theme:
            self._apply_theme()
        self.after(2000, self._poll_theme)

    def _animate_progress_to(self, target: float) -> None:
        """Ease-out animate the progress bar toward `target` at ~60 fps.<br>
        Each frame closes 25% of the remaining distance, giving natural deceleration."""
        if not hasattr(self, "progress_bar"):
            return
        if self._progress_anim_id:
            self.after_cancel(self._progress_anim_id)
            self._progress_anim_id = None

        _STEP_MS: int = 16
        _EASE: float = 0.25
        _SNAP: float = 0.005

        def _step() -> None:
            if abs(remaining := target - self._progress_anim_current) < _SNAP:
                self.progress_bar.set(target)
                self._progress_anim_current = target
                self._progress_anim_id = None
                return

            self._progress_anim_current += remaining * _EASE
            self.progress_bar.set(self._progress_anim_current)
            self._progress_anim_id = self.after(_STEP_MS, _step)

        _step()

    def save_template(self) -> None:
        # EXTRACT CURRENT VALUES FROM UI
        template_data: dict[str, str] = {}

        for label, data in self.entries.items():
            if val := data["widget"].get().strip():
                if FIELDS_FLAT[label].get("value_type") == ValueType.Date:
                    try:
                        val = exiftool_date_to_display(parse_date(val)) or val
                    except ValueError:
                        pass  # SAVE AS-IS; apply_metadata WILL CATCH THE ERROR LATER

                template_data[label] = val

        cover_src: Optional[str] = self._cover_video_source or self.cover_art_path

        if not template_data and not cover_src:
            messagebox.showinfo("Empty", "No fields filled out to save.")
            return

        if filepath := filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")],
                                                    title="Save Metadata Template"):
            if cover_src:
                try:
                    rel = Path(cover_src).relative_to(Path(filepath).parent, walk_up=True)
                    template_data["__cover_art__"] = rel.as_posix()
                except ValueError:  # DIFFERENT DRIVES ON WINDOWS – FALL BACK TO ABSOLUTE
                    template_data["__cover_art__"] = cover_src
            try:
                with open(filepath, "w", encoding="utf-8") as file:
                    json.dump(template_data, file, indent=4)
                messagebox.showinfo("Saved", "Template saved successfully!")
            except Exception as err:
                messagebox.showerror("Error", f"Failed to save template:\n{err}")

    def _extract_cover_bytes_from_video(self, video_path: str) -> bytes:
        """Run ExifTool to extract embedded cover art bytes from a video file.<br>
        Tries ItemList then QuickTime atom locations. Returns `b""` if none found."""
        if not self.exiftool_path:
            return b""

        for cover_tag in ("-ItemList:CoverArt", "-QuickTime:CoverArt"):
            res = subprocess.run([self.exiftool_path, "-b", cover_tag, video_path], capture_output=True, **_POPEN_FLAGS)
            if res.stdout:
                return res.stdout

        return b""

    def _apply_cover_from_video_bytes(self, cover_bytes: bytes, video_source: str) -> None:
        """Load cover art from raw bytes (extracted from `video_source`) and update the UI."""
        try:
            self._cover_video_source = video_source
            self._set_cover_from_image(Image.open(io.BytesIO(cover_bytes)).convert("RGB"))
        except Exception:
            pass  # MALFORMED COVER DATA; SILENTLY IGNORE

    def load_from_video(self) -> None:
        if not (filepath := filedialog.askopenfilename(title="Load Metadata from Video", filetypes=VIDEO_FILE_TYPES)):
            return

        assert self.exiftool_path is not None

        c = COLORS[self._current_theme]
        self.btn_load_from_video.start(c["secondary_foreground"])

        exiftool = self.exiftool_path

        # REQUEST ALL TAGS FOR EVERY FIELD (PRIMARY AND SECONDARY) SO FALLBACK IS POSSIBLE
        seen: set[str] = set()
        tag_args: list[str] = []

        for fd in FIELDS_FLAT.values():
            for tag in fd["tags"]:
                if (key := tag.lstrip("-")) not in seen:
                    seen.add(key)
                    tag_args.append(key)

        command: list[str] = [exiftool, "-json", "-charset", "utf8"] + [f"-{t}" for t in tag_args] + [filepath]

        def _worker() -> None:
            try:
                result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=True, **_POPEN_FLAGS)
                records: list[dict[str, object]] = json.loads(result.stdout)

            except subprocess.CalledProcessError as err:
                self.after(
                    0,
                    lambda m=f"Failed to read metadata:\n{err.stderr}":
                    (self.btn_load_from_video.stop(state="normal"), messagebox.showerror("ExifTool Error", m))
                )
                return

            except (json.JSONDecodeError, KeyError) as err:
                self.after(
                    0,
                    lambda m=f"Could not parse ExifTool output:\n{err}":
                    (self.btn_load_from_video.stop(state="normal"), messagebox.showerror("Parse Error", m))
                )
                return

            if not records:
                self.after(
                    0, lambda: (
                        self.btn_load_from_video.stop(state="normal"),
                        messagebox.showinfo("No Data", "ExifTool returned no metadata for this file.")
                    )
                )
                return

            meta: dict[str, object] = records[0]
            cover_bytes: bytes = self._extract_cover_bytes_from_video(filepath)
            self.after(0, lambda: self._on_load_from_video_done(meta, cover_bytes, filepath))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_load_from_video_done(self, meta: dict[str, object], cover_bytes: bytes, filepath: str) -> None:
        self.btn_load_from_video.stop(state="normal")

        # BUILD A MAP FROM SHORT TAG NAME → LABEL FOR ALL TAGS (PRIMARY AND SECONDARY),
        # AND TRACK WHICH LABELS HAVE ALREADY BEEN POPULATED (PRIMARY WINS)
        tag_key_to_label: dict[str, str] = {}

        for label, fd in FIELDS_FLAT.items():
            for tag in fd["tags"]:
                # FIRST OCCURRENCE = HIGHEST PRIORITY
                if (short := tag.split(":", 1)[-1].lstrip("-")) not in tag_key_to_label:
                    tag_key_to_label[short] = label

        populated: set[str] = set()

        for key, value in meta.items():
            if key in tag_key_to_label and value:
                if (label := tag_key_to_label[key]) in populated:
                    continue  # ALREADY SET BY A HIGHER-PRIORITY TAG

                populated.add(label)
                widget = self.entries[label]["widget"]
                widget.delete(0, "end")

                if FIELDS_FLAT[label].get("value_type") == ValueType.Date:
                    display_val = exiftool_date_to_display(str(value)) or str(value)
                else:
                    display_val = re.sub(r"\s*[/;,]\s*", ", ", str(value))  # NORMALIZE SEPARATORS FOR DISPLAY

                widget.insert(0, display_val)

        # EXTRACT EMBEDDED COVER ART, IF ANY
        if cover_bytes:
            self._apply_cover_from_video_bytes(cover_bytes, filepath)

    def load_template(self) -> None:
        if not (filepath := filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Load Metadata Template")):
            return

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                template_data: dict[str, str] = json.load(file)
        except Exception as err:
            messagebox.showerror("Error", f"Failed to load template:\n{err}")
            return

        # CLEAR EXISTING ENTRIES AND INSERT NEW ONES
        for label, data in self.entries.items():
            data["widget"].delete(0, "end")
            if label in template_data:
                data["widget"].insert(0, template_data[label])

        cover_path_raw = template_data.get("__cover_art__")
        if not cover_path_raw:
            return
        # RESOLVE RELATIVE TO THE TEMPLATE FILE'S FOLDER; ALSO HANDLES LEGACY ABSOLUTE PATHS
        # (JOINING AN ABSOLUTE PATH DISCARDS THE BASE, SO BOTH FORMATS WORK TRANSPARENTLY)
        cover_path = str((Path(filepath).parent / cover_path_raw).resolve())
        if not Path(cover_path).is_file():
            messagebox.showwarning(
                "Cover Art Not Found", f"The cover image saved in this template could not be found:\n{cover_path}\n\n"
                "The rest of the template was loaded successfully."
            )
            return

        # FAST PATH: PLAIN IMAGE FILE (RUNS ON MAIN THREAD – NO SPINNER NEEDED)
        try:
            self.cover_art_path = cover_path
            self._set_cover_from_image(Image.open(cover_path).convert("RGB"))
            return
        except Exception:
            self.cover_art_path = None

        # SLOW PATH: EMBEDDED COVER IN A VIDEO – RUN EXIFTOOL IN A BACKGROUND THREAD
        c = COLORS[self._current_theme]
        self.btn_load_template.start(c["card_foreground"])

        def _worker() -> None:
            video_cover = self._extract_cover_bytes_from_video(cover_path)

            def _done() -> None:
                self.btn_load_template.stop(state="normal")
                if video_cover:
                    self._apply_cover_from_video_bytes(video_cover, cover_path)
                else:
                    messagebox.showwarning(
                        "Cover Art Failed to Load",
                        f"The cover image saved in this template could not be loaded:\n{cover_path}\n\n"
                        "The rest of the template was loaded successfully."
                    )

            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    def apply_metadata(self) -> None:
        if not self.exiftool_path:
            return
        if not self.selected_files:
            messagebox.showwarning("No Files", "Please select at least one video file.")
            return
        if self._applying:
            return

        files: list[str] = list(self.selected_files)
        n_files: int = len(files)
        exiftool: str = self.exiftool_path

        if clear_mode := bool(self.sw_clear_empty.get()):
            if not messagebox.askokcancel(
                    "Clear Empty Fields",
                    '"Clear empty fields" is enabled.\n\n'
                    f"Fields left blank will actively delete the corresponding tags from the file{'' if n_files == 1 else 's'}. "
                    "This cannot be undone – consider backing up your files first.\n\n"
                    "Continue?",
                    icon="warning",
            ):
                return

        tag_lines: list[str] = []
        val_tempfiles: list[Path] = []  # PER-VALUE TEMP FILES FOR MULTILINE CONTENT
        tags_added: int = 0

        def _tag_line(tag: str, val: str) -> str:
            """Return an argfile line for `tag=val`, using a temp file if val contains newlines."""
            if "\n" in val:
                vf = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False, newline="\n")
                vf.write(val)
                vf.close()
                val_tempfiles.append(Path(vf.name))
                return f"{tag}<={vf.name}"
            return f"{tag}={val}"

        # [1] COLLECT TEXT TAG ASSIGNMENTS
        for label, data in self.entries.items():
            field_type = FIELDS_FLAT[label]["field_type"]

            if val := data["widget"].get().strip():
                if field_type == FieldType.EXPANDING:
                    val = normalize_multi(val)

                elif vt := FIELDS_FLAT[label].get("value_type"):
                    if err := validate_field(val, vt):
                        messagebox.showerror("Invalid Value", err)
                        return
                    if vt == ValueType.Date:
                        val = parse_date(val)

                for tag in data["tags"]:
                    tag_lines.append(_tag_line(tag, val))

                tags_added += 1

            elif clear_mode:
                for tag in data["tags"]:
                    tag_lines.append(f"{tag}=")  # EMPTY ASSIGNMENT DELETES THE TAG

                tags_added += 1

        # [2] COVER ART TAG
        if self.cover_art_embed_path:
            tag_lines.append(f"-ItemList:CoverArt<={self.cover_art_embed_path}")
            tags_added += 1
        elif clear_mode:
            tag_lines.append("-ItemList:CoverArt=")  # REMOVE EXISTING COVER ART
            tags_added += 1

        if tags_added == 0:
            messagebox.showinfo("No Input", "No metadata or cover art provided.")
            return

        # WRITE TAG ASSIGNMENTS TO A UTF-8 ARGFILE SO UNICODE VALUES ARE PASSED
        # CORRECTLY ON WINDOWS (BYPASSES SYSTEM CODEPAGE FOR COMMAND-LINE ARGS)
        argfile = tempfile.NamedTemporaryFile(mode="w", suffix=".args", encoding="utf-8", delete=False, newline="\n")
        argfile.write("\n".join(tag_lines))
        argfile.close()

        self._applying = True

        if self.btn_apply:
            self.btn_apply.start(COLORS[self._current_theme]["primary_foreground"])

        if hasattr(self, "progress_bar"):
            if self._progress_anim_id:
                self.after_cancel(self._progress_anim_id)
            self._progress_anim_id = None
            self._progress_anim_current = 0.0
            self.progress_bar.set(0)
            self.progress_bar.grid()

        errors: list[str] = []
        warnings: list[str] = []

        def _on_done() -> None:
            self._applying = False
            Path(argfile.name).unlink(missing_ok=True)

            for vf in val_tempfiles:
                vf.unlink(missing_ok=True)

            if self.btn_apply:
                self.btn_apply.stop(state="normal")

            if hasattr(self, "progress_bar"):
                if self._progress_anim_id:
                    self.after_cancel(self._progress_anim_id)
                    self._progress_anim_id = None
                self.progress_bar.grid_remove()

            if errors:
                err_text = "\n\n".join(errors)
                messagebox.showerror("ExifTool Error", f"Errors occurred:\n{err_text}")
            elif warnings:
                warn_text = "\n\n".join(warnings)
                messagebox.showwarning(
                    "Completed with Warnings",
                    f"Updated {n_files} file{'' if n_files == 1 else 's'}, but ExifTool reported minor warnings:\n{warn_text}"
                )
            else:
                messagebox.showinfo("Success", f"Successfully updated {n_files} file{'' if n_files == 1 else 's'}!")

        def _worker() -> None:
            for i, filepath in enumerate(files):
                self.after(0, lambda p=(i + 0.3) / n_files: self._animate_progress_to(p))
                cmd: list[str] = [exiftool, "-overwrite_original", "-@", argfile.name, filepath]

                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, **_POPEN_FLAGS)

                    if result.returncode == 0:
                        pass  # CLEAN SUCCESS
                    elif result.returncode == 1:
                        # EXIT CODE 1 = MINOR WARNING (E.G. SPEC VIOLATION); NOT A REAL ERROR
                        if result.stderr.strip():
                            warnings.append(result.stderr.strip())
                    else:
                        errors.append(result.stderr or f"ExifTool exited with code {result.returncode}")

                except Exception as err:
                    errors.append(str(err))

                self.after(0, lambda p=(i + 1) / n_files: self._animate_progress_to(p))

            self.after(0, _on_done)

        threading.Thread(target=_worker, daemon=True).start()


if __name__ == "__main__":
    ctk.set_appearance_mode(get_system_theme())
    ctk.set_default_color_theme("blue")

    # ON WINDOWS, SET THE APP USER MODEL ID BEFORE CREATING THE WINDOW SO THE
    # TASKBAR GROUPS THE APP UNDER ITS OWN ICON RATHER THAN THE PYTHON INTERPRETER
    if sys.platform == "win32":
        try:
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
    if app._temp_ico_path and app._temp_ico_path.exists():
        app._temp_ico_path.unlink()
