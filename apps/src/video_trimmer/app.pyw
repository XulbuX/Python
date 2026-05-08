# pyright: basic
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Optional
from PIL import Image
import customtkinter as ctk
import subprocess
import webbrowser
import threading
import ctypes
import shutil
import json
import sys
import io

# MAKE THE _shared PACKAGE (apps/src/_shared) IMPORTABLE WHEN RUNNING THIS SCRIPT DIRECTLY
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# SHARED – ABSOLUTE IMPORTS DURING RUNTIME, RELATIVE ONES DURING DEVELOPMENT SO THE TYPES ARE LINKED CORRECTLY IN THE IDE
from _shared.consts import COLORS, POPEN_FLAGS as _POPEN_FLAGS  # type: ignore[missing-import]
from _shared.helpers import resolve_mono_font, get_system_theme, setup_window_icon  # type: ignore[missing-import]
from _shared.widgets import SegmentedButton, SpinnerButton, ToolTip, bind_clean_paste, render_svg_icon  # type: ignore[missing-import]
if TYPE_CHECKING:
    from .._shared.consts import COLORS, POPEN_FLAGS as _POPEN_FLAGS
    from .._shared.helpers import resolve_mono_font, get_system_theme, setup_window_icon
    from .._shared.widgets import SegmentedButton, SpinnerButton, ToolTip, bind_clean_paste, render_svg_icon

from consts import VIDEO_FILE_TYPES, APP_ICON_PNG
from helpers import parse_time, format_time, frame_to_time, time_to_frame
from widgets import TrimTimeline

_THUMB_W: int = 260
_THUMB_H: int = 146  # 16:9 ASPECT RATIO
_PREVIEW_DEBOUNCE_MS: int = 350
_DEFAULT_FPS: float = 25.0


class VideoTrimmerApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        self.title("Video Trimmer")
        self.resizable(False, False)

        # CENTERED FIXED-SIZE WINDOW
        ww, wh = 580, 635
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{ww}x{wh}+{(sw - ww) // 2}+{(sh - wh) // 2}")

        # SET WINDOW/TASKBAR ICON
        self._temp_ico_path: Optional[Path] = setup_window_icon(self, APP_ICON_PNG)

        # CHECK FOR FFMPEG / FFPROBE
        self.ffmpeg_path: Optional[str] = shutil.which("ffmpeg")
        self.ffprobe_path: Optional[str] = shutil.which("ffprobe")

        self.selected_file: Optional[str] = None
        self.duration: Optional[float] = None  # IN SECONDS
        self.fps: Optional[float] = None
        self.output_path: Optional[str] = None

        self._start_sec: float = 0.0  # INTERNAL START POINT (ALWAYS IN SECONDS)
        self._end_sec: Optional[float] = None  # INTERNAL END POINT; None = END OF FILE

        self._input_mode: str = "time"  # "time" OR "frame"
        self._current_theme: str = get_system_theme()
        self._trimming: bool = False

        self._preview_start_job: Optional[str] = None
        self._preview_end_job: Optional[str] = None
        self._start_preview_image: Optional[ctk.CTkImage] = None
        self._end_preview_image: Optional[ctk.CTkImage] = None
        self._preview_generation: int = 0

        ################################################## UI LAYOUT ##################################################
        PAD: int = 16

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        #################### SELECT FILE SECTION ####################
        self.sec_file = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.sec_file.pack(fill="x")
        self.sec_file.grid_columnconfigure(1, weight=1)

        self.lbl_section_file = ctk.CTkLabel(self.sec_file, text="Select Video", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_section_file.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.btn_reset_all = ctk.CTkButton(
            self.sec_file, text="", width=28, height=28, corner_radius=6, border_width=0, command=self.reset_all
        )
        self.btn_reset_all.grid(row=0, column=2, sticky="e", pady=(0, 8))
        ToolTip(self.btn_reset_all, "Reset all fields")

        self.btn_select_file = SpinnerButton(self.sec_file, text="Select Video File", command=self.select_file)
        self.btn_select_file.grid(row=1, column=0, sticky="w")

        self.lbl_file = ctk.CTkLabel(self.sec_file, text="No file selected", anchor="w")
        self.lbl_file.grid(row=1, column=1, padx=(10, 0), sticky="ew")

        #################### TRIM RANGE SECTION ####################
        self.sec_trim = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.sec_trim.pack(fill="x", pady=(PAD, 0))

        # -- SECTION HEADER: TITLE + TIME / FRAME MODE TOGGLE --
        self.trim_header = ctk.CTkFrame(self.sec_trim, fg_color="transparent")
        self.trim_header.pack(fill="x", pady=(0, 8))

        self.lbl_section_trim = ctk.CTkLabel(
            self.trim_header, text="Trim Range", font=ctk.CTkFont(size=16, weight="bold")
        )
        self.lbl_section_trim.pack(side="left")

        self.mode_toggle = SegmentedButton(
            self.trim_header,
            values=["Time", "Frame"],
            command=self._on_mode_change,
            width=120,
            height=24,
            font=ctk.CTkFont(size=12),
            tooltip="Switch between time (HH:MM:SS) and frame-number input mode",
        )
        self.mode_toggle.set("Time")
        self.mode_toggle.pack(side="right")

        # -- PREVIEW THUMBNAILS: START ON LEFT, END ON RIGHT --
        self.sec_preview = ctk.CTkFrame(self.sec_trim, fg_color="transparent")
        self.sec_preview.pack(fill="x", pady=(0, 6))

        self.frame_start_thumb = ctk.CTkFrame(
            self.sec_preview, width=_THUMB_W + 2, height=_THUMB_H + 2, corner_radius=0, border_width=1
        )
        self.frame_start_thumb.pack(side="left")
        self.frame_start_thumb.pack_propagate(False)
        self.lbl_start_thumb = ctk.CTkLabel(
            self.frame_start_thumb, text="Start\nframe", font=ctk.CTkFont(size=11)
        )
        self.lbl_start_thumb.place(relx=0.5, rely=0.5, anchor="center")

        self.frame_end_thumb = ctk.CTkFrame(
            self.sec_preview, width=_THUMB_W + 2, height=_THUMB_H + 2, corner_radius=0, border_width=1
        )
        self.frame_end_thumb.pack(side="right")
        self.frame_end_thumb.pack_propagate(False)
        self.lbl_end_thumb = ctk.CTkLabel(
            self.frame_end_thumb, text="End\nframe", font=ctk.CTkFont(size=11)
        )
        self.lbl_end_thumb.place(relx=0.5, rely=0.5, anchor="center")

        # -- TIMELINE BAR --
        self.trim_timeline = TrimTimeline(self.sec_trim, height=36)
        self.trim_timeline.pack(fill="x", pady=(16, 32))
        self.trim_timeline.on_change = self._on_timeline_change
        self.trim_timeline.on_commit = self._on_timeline_commit
        self.trim_timeline.set_enabled(False)  # DISABLED UNTIL A FILE IS LOADED

        # -- INPUT ROW: START / END ENTRIES WITH STEPPERS --
        self.sec_inputs = ctk.CTkFrame(self.sec_trim, fg_color="transparent")
        self.sec_inputs.pack(fill="x")
        self.sec_inputs.grid_columnconfigure(2, weight=1)
        self.sec_inputs.grid_columnconfigure(6, weight=1)

        # START
        self.lbl_start = ctk.CTkLabel(self.sec_inputs, text="Start")
        self.lbl_start.grid(row=0, column=0, sticky="w", padx=(0, 6))

        self.btn_start_left = ctk.CTkButton(
            self.sec_inputs, text="", width=28, height=28, corner_radius=6,
            border_width=1,
            command=lambda: self._step_time("start", -1),
        )
        self.btn_start_left.grid(row=0, column=1, padx=(0, 2))

        self.entry_start = ctk.CTkEntry(self.sec_inputs, border_width=1, placeholder_text="00:00")
        self.entry_start.grid(row=0, column=2, sticky="ew")
        bind_clean_paste(self.entry_start._entry)

        self.btn_start_right = ctk.CTkButton(
            self.sec_inputs, text="", width=28, height=28, corner_radius=6,
            border_width=1,
            command=lambda: self._step_time("start", +1),
        )
        self.btn_start_right.grid(row=0, column=3, padx=(2, 0))

        # END
        self.lbl_end = ctk.CTkLabel(self.sec_inputs, text="End")
        self.lbl_end.grid(row=0, column=4, sticky="w", padx=(PAD, 6))

        self.btn_end_left = ctk.CTkButton(
            self.sec_inputs, text="", width=28, height=28, corner_radius=6,
            border_width=1,
            command=lambda: self._step_time("end", -1),
        )
        self.btn_end_left.grid(row=0, column=5, padx=(0, 2))

        self.entry_end = ctk.CTkEntry(self.sec_inputs, border_width=1, placeholder_text="end of file")
        self.entry_end.grid(row=0, column=6, sticky="ew")
        bind_clean_paste(self.entry_end._entry)

        self.btn_end_right = ctk.CTkButton(
            self.sec_inputs, text="", width=28, height=28, corner_radius=6,
            border_width=1,
            command=lambda: self._step_time("end", +1),
        )
        self.btn_end_right.grid(row=0, column=7, padx=(2, 0))

        # -- HINT TEXT --
        self.lbl_hint = ctk.CTkLabel(
            self.sec_trim,
            text="Format: SS, MM:SS or HH:MM:SS  (decimals allowed, e.g. 1:23.5)",
            font=ctk.CTkFont(size=11),
        )
        self.lbl_hint.pack(anchor="w", pady=(6, 0))

        #################### OUTPUT SECTION ####################
        self.sec_out = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.sec_out.pack(fill="x", pady=(PAD, 0))
        self.sec_out.grid_columnconfigure(1, weight=1)

        self.lbl_section_out = ctk.CTkLabel(self.sec_out, text="Output", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_section_out.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.btn_select_out = ctk.CTkButton(
            self.sec_out, text="Choose Output\u2026", command=self.select_output, border_width=1
        )
        self.btn_select_out.grid(row=1, column=0, sticky="w")

        self.lbl_out = ctk.CTkLabel(self.sec_out, text="(auto: same folder, suffix \"_trimmed\")", anchor="w")
        self.lbl_out.grid(row=1, column=1, padx=(10, 0), sticky="ew")

        #################### APPLY BUTTON –OR– FFMPEG NOT FOUND BANNER ####################
        if self.ffmpeg_path and self.ffprobe_path:
            self._apply_bottom = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            self._apply_bottom.pack(fill="x", side="bottom", pady=(PAD, 0))
            self._apply_bottom.grid_columnconfigure(0, weight=1)
            self.btn_apply = SpinnerButton(self._apply_bottom, text="Trim Video", command=self.apply_trim, height=40)
            self.btn_apply.grid(row=1, column=0, sticky="ew")
            self.progress_bar = ctk.CTkProgressBar(self._apply_bottom, height=4, corner_radius=4)
            self.progress_bar.grid(row=0, column=0, pady=(0, 10), sticky="ew")
            self.progress_bar.set(0)
            self.progress_bar.grid_remove()
            self._progress_anim_id: Optional[str] = None
            self._progress_anim_current: float = 0.0
        else:
            self.btn_apply = None
            self._banner_labels: list[tuple[ctk.CTkLabel, str]] = []  # (widget, color_key)
            self._banner = ctk.CTkFrame(self.main_frame, border_width=1, corner_radius=8)
            self._banner.pack(fill="x", side="bottom", pady=(PAD, 0))
            lbl_title = ctk.CTkLabel(
                self._banner,
                text="FFmpeg is not installed or not in PATH",
                font=ctk.CTkFont(size=13, weight="bold"),
                wraplength=ww - 2 * PAD - 20,
                justify="left"
            )
            lbl_title.pack(anchor="w", padx=10, pady=(2, 0))
            self._banner_labels.append((lbl_title, "destructive_foreground"))
            lbl_desc = ctk.CTkLabel(
                self._banner,
                text="FFmpeg (and FFprobe) are required to trim video files. Please install them and restart the app.",
                wraplength=ww - 2 * PAD - 20,
                justify="left"
            )
            lbl_desc.pack(anchor="w", padx=10, pady=(4, 0))
            self._banner_labels.append((lbl_desc, "destructive_muted"))
            lbl_cmd = ctk.CTkLabel(self._banner, text="ffmpeg.org", font=resolve_mono_font(12), cursor="hand2")
            lbl_cmd.pack(anchor="w", padx=10, pady=(4, 8))
            lbl_cmd.bind("<Button-1>", lambda _: webbrowser.open("https://ffmpeg.org"))
            self._banner_labels.append((lbl_cmd, "link"))

        # BIND ENTRY COMMIT EVENTS
        for entry, which in ((self.entry_start, "start"), (self.entry_end, "end")):
            entry._entry.bind("<FocusOut>", lambda e, w=which: self._on_entry_commit(w))
            entry._entry.bind("<Return>", lambda e, w=which: self._on_entry_commit(w))
            entry._entry.bind("<KP_Enter>", lambda e, w=which: self._on_entry_commit(w))

        self._apply_theme()
        self.after(2000, self._poll_theme)

        # VERIFY FFMPEG IN THE BACKGROUND SO THE UI IS FULLY RENDERED FIRST
        if self.ffmpeg_path and self.ffprobe_path and self.btn_apply:
            self.btn_apply.start(COLORS[self._current_theme]["primary_foreground"])
            threading.Thread(target=self._verify_ffmpeg, daemon=True).start()

    ########################################################## FILE SELECTION ##########################################################

    def select_file(self) -> None:
        if not (filename := filedialog.askopenfilename(title="Select Video File", filetypes=VIDEO_FILE_TYPES)):
            return

        self.selected_file = filename
        self.duration = None
        self.fps = None
        self._start_sec = 0.0
        self._end_sec = None
        self._preview_generation += 1

        c = COLORS[self._current_theme]
        self.lbl_file.configure(text=Path(filename).name, text_color=c["foreground"])
        self.btn_select_file.start(COLORS[self._current_theme]["card_foreground"])

        # RESET PREVIEWS AND TIMELINE
        self._cancel_preview_jobs()
        self._set_preview("start", None)
        self._set_preview("end", None)
        self.trim_timeline.set_range(0.0, 1.0)
        self.trim_timeline.set_enabled(False)

        threading.Thread(target=self._probe_duration, args=(filename,), daemon=True).start()

    def _probe_duration(self, filename: str) -> None:
        """Probe the file's duration and FPS via FFprobe; called in a background thread."""
        if not self.ffprobe_path:
            return

        cmd = [self.ffprobe_path, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", filename]
        duration: Optional[float] = None
        fps: Optional[float] = None

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, **_POPEN_FLAGS)
            data = json.loads(res.stdout or "{}")

            if d := data.get("format", {}).get("duration"):
                duration = float(d)

            for st in data.get("streams", []):
                if st.get("codec_type") == "video":
                    if duration is None:
                        if d := st.get("duration"):
                            duration = float(d)
                    # PARSE r_frame_rate OR avg_frame_rate (FORMAT: "num/den")
                    for key in ("r_frame_rate", "avg_frame_rate"):
                        if (fr := st.get(key)) and "/" in fr:
                            try:
                                num, den = fr.split("/", 1)
                                candidate = float(num) / float(den)
                                if 1.0 < candidate < 500.0:
                                    fps = candidate
                                    break
                            except (ValueError, ZeroDivisionError):
                                pass
                    break

        except Exception:
            duration = None

        def _done() -> None:
            self.duration = duration
            self.fps = fps
            c = COLORS[self._current_theme]

            if duration is not None:
                self._start_sec = 0.0
                self._end_sec = None
                self.trim_timeline.set_range(0.0, 1.0)
                self.trim_timeline.set_enabled(True)
                self._sync_entries()
                self._update_hint()
                self._schedule_preview("start", 0.0)
                self._schedule_preview("end", duration)
            else:
                self.lbl_file.configure(text_color=c["destructive_label"])
            self.btn_select_file.stop(state="normal")

        self.after(0, _done)

    ########################################################## FRAME PREVIEWS ##########################################################

    def _cancel_preview_jobs(self) -> None:
        for attr in ("_preview_start_job", "_preview_end_job"):
            if job := getattr(self, attr):
                self.after_cancel(job)
                setattr(self, attr, None)

    def _schedule_preview(self, which: str, sec: float) -> None:
        """Debounce and then extract the frame at `sec` seconds for `which` thumbnail."""
        if not self.selected_file or not self.ffmpeg_path:
            return

        # CAP TO JUST BEFORE EOF; FFmpeg RETURNS NOTHING IF SEEK POSITION >= DURATION
        if self.duration is not None:
            sec = min(sec, max(0.0, self.duration - 1.0 / (self.fps or _DEFAULT_FPS)))


        if old := getattr(self, (job_attr := f"_preview_{which}_job")):
            self.after_cancel(old)

        video_path = self.selected_file

        setattr(self, job_attr, self.after(
            _PREVIEW_DEBOUNCE_MS,
            lambda: self._load_preview_async(which, sec, video_path),
        ))

    def _load_preview_async(self, which: str, sec: float, video_path: str) -> None:
        setattr(self, f"_preview_{which}_job", None)
        generation = self._preview_generation

        def _worker() -> None:
            img = self._extract_frame(video_path, sec)

            def _apply() -> None:
                if self._preview_generation == generation:
                    self._set_preview(which, img)

            self.after(0, _apply)

        threading.Thread(target=_worker, daemon=True).start()

    def _extract_frame(self, video_path: str, sec: float) -> Optional[Image.Image]:
        """Extract a single video frame at `sec` seconds; returns PIL Image or None."""
        if not self.ffmpeg_path:
            return None
        cmd = [
            self.ffmpeg_path,
            "-ss", f"{max(0.0, sec):.6f}",
            "-i", video_path,
            "-frames:v", "1",
            "-vf", (
                f"scale={_THUMB_W}:{_THUMB_H}:force_original_aspect_ratio=decrease:flags=lanczos,"
                f"pad={_THUMB_W}:{_THUMB_H}:({_THUMB_W}-iw)/2:({_THUMB_H}-ih)/2"
            ),
            "-f", "image2pipe",
            "-vcodec", "mjpeg",
            "pipe:1",
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, timeout=10, **_POPEN_FLAGS)
            if res.returncode == 0 and res.stdout:
                return Image.open(io.BytesIO(res.stdout)).copy()
        except Exception:
            pass
        return None

    def _set_preview(self, which: str, img: Optional[Image.Image]) -> None:
        """Update a thumbnail widget; `which` is 'start' or 'end'."""
        lbl = self.lbl_start_thumb if which == "start" else self.lbl_end_thumb
        c = COLORS[self._current_theme]

        if img is None:
            setattr(self, f"_{which}_preview_image", None)
            # CLEAR THE UNDERLYING tk.Label IMAGE FIRST TO PREVENT TclError FROM STALE PHOTIMAGE REFS
            try:
                lbl._label.configure(image="")
            except Exception:
                pass
            lbl.configure(image=None, text="Start\nframe" if which == "start" else "End\nframe",
                          text_color=c["placeholder_foreground"])
            return

        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
        setattr(self, f"_{'start' if which == 'start' else 'end'}_preview_image", ctk_img)
        lbl.configure(image=ctk_img, text="")
        lbl.place(relx=0.5, rely=0.5, anchor="center")

    ########################################################## TIMELINE INTERACTIONS ##########################################################

    def _on_timeline_change(self, start_frac: float, end_frac: float) -> None:
        """Called continuously while the timeline handle is being dragged."""
        if self.duration is None:
            return

        self._start_sec = start_frac * self.duration
        new_end = end_frac * self.duration
        self._end_sec = new_end if new_end < self.duration - 0.05 else None

        self._sync_entries()

    def _on_timeline_commit(self, start_frac: float, end_frac: float) -> None:
        """Called once when the timeline handle is released."""
        if self.duration is None:
            return

        self._start_sec = start_frac * self.duration
        new_end = end_frac * self.duration
        self._end_sec = new_end if new_end < self.duration - 0.05 else None

        self._sync_entries()
        self._schedule_preview("start", self._start_sec)
        self._schedule_preview("end", self._end_sec if self._end_sec is not None else self.duration)

    ########################################################## ENTRY INTERACTIONS ##########################################################

    def _on_entry_commit(self, which: str) -> None:
        """Parse the entry and update internal state; revert on invalid input."""
        entry = self.entry_start if which == "start" else self.entry_end
        val = entry.get().strip()

        if not val:
            if which == "start":
                self._start_sec = 0.0
            else:
                self._end_sec = None
            self._sync_entries()
            self._sync_timeline()
            return

        sec: Optional[float] = None
        if self._input_mode == "frame":
            fps = self.fps or _DEFAULT_FPS
            try:
                sec = frame_to_time(int(val), fps)
            except ValueError:
                pass
        else:
            sec = parse_time(val)

        if sec is None:
            self._sync_entries()  # REVERT TO LAST VALID VALUE
            return

        sec = max(0.0, sec)
        if self.duration is not None:
            sec = min(sec, self.duration)

        if which == "start":
            self._start_sec = sec
        else:
            self._end_sec = sec if (self.duration is None or sec < self.duration - 0.05) else None

        self._sync_entries()
        self._sync_timeline()
        self._schedule_preview(which, sec)

    def _step_time(self, which: str, direction: int) -> None:
        """Increment or decrement the start or end by exactly one frame."""
        if not self.selected_file:
            return
        fps = self.fps or _DEFAULT_FPS
        step = 1.0 / fps

        if which == "start":
            current = self._start_sec
        else:
            current = self._end_sec if self._end_sec is not None else (self.duration or 0.0)

        new_sec = max(0.0, current + direction * step)
        if self.duration is not None:
            new_sec = min(new_sec, self.duration)

        if which == "start":
            self._start_sec = new_sec
            if self._end_sec is not None and self._start_sec >= self._end_sec:
                self._start_sec = max(0.0, self._end_sec - step)
        else:
            self._end_sec = new_sec if (self.duration is None or new_sec < self.duration - 0.05) else None
            if self._end_sec is not None and self._end_sec <= self._start_sec:
                self._end_sec = self._start_sec + step

        self._sync_entries()
        self._sync_timeline()
        self._schedule_preview(which, new_sec)

    def _on_mode_change(self, value: str) -> None:
        self._input_mode = "frame" if value == "Frame" else "time"
        self._update_hint()
        self._sync_entries()

    ########################################################## STATE SYNC ##########################################################

    def _sync_entries(self) -> None:
        """Repopulate the entry widgets from `_start_sec` / `_end_sec`."""
        if not self.selected_file:
            return

        fps = self.fps or _DEFAULT_FPS
        effective_end = self._end_sec if self._end_sec is not None else self.duration

        if self._input_mode == "frame":
            start_text = str(time_to_frame(self._start_sec, fps)) if self.selected_file else ""
            end_text = str(time_to_frame(effective_end, fps)) if effective_end is not None else ""
        else:
            start_text = format_time(self._start_sec) if self.selected_file else ""
            end_text = format_time(effective_end) if effective_end is not None else ""

        for entry, text in ((self.entry_start, start_text), (self.entry_end, end_text)):
            entry.delete(0, "end")
            if text:
                entry.insert(0, text)

    def _sync_timeline(self) -> None:
        """Update the timeline widget from `_start_sec` / `_end_sec`."""
        if self.duration:
            start_frac = self._start_sec / self.duration
            end_frac = (self._end_sec / self.duration) if self._end_sec is not None else 1.0
            self.trim_timeline.set_range(start_frac, end_frac)

    def _update_hint(self) -> None:
        if self._input_mode == "frame":
            if self.fps:
                hint = f"Frame number  (at {self.fps:.3f} fps)"
            else:
                hint = f"Frame number  (FPS unknown, assuming {_DEFAULT_FPS:.0f})"

            self.entry_start.configure(placeholder_text="0")
            self.entry_end.configure(placeholder_text="last frame")

        else:
            hint = "Format: SS, MM:SS or HH:MM:SS  (decimals allowed, e.g. 1:23.5)"
            self.entry_start.configure(placeholder_text="00:00")
            self.entry_end.configure(placeholder_text="end of file")

        self.lbl_hint.configure(text=hint)

    ########################################################## OUTPUT & RESET ##########################################################

    def select_output(self) -> None:
        initial_dir: Optional[str] = None
        initial_file: Optional[str] = None

        if self.selected_file:
            p = Path(self.selected_file)
            initial_dir = str(p.parent)
            initial_file = f"{p.stem}_trimmed{p.suffix}"

        path = filedialog.asksaveasfilename(
            title="Save Trimmed Video As",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=Path(self.selected_file).suffix if self.selected_file else ".mp4",
            filetypes=VIDEO_FILE_TYPES,
        )
        if not path:
            return

        self.output_path = path
        c = COLORS[self._current_theme]
        self.lbl_out.configure(text=Path(path).name, text_color=c["foreground"])

    def reset_all(self) -> None:
        """Clear all fields and return the UI to its initial state."""
        self._start_sec = 0.0
        self._end_sec = None
        self.selected_file = None
        self.duration = None
        self.fps = None
        self.output_path = None

        self._preview_generation += 1
        self._cancel_preview_jobs()

        self.entry_start.delete(0, "end")
        self.entry_end.delete(0, "end")

        c = COLORS[self._current_theme]
        self.lbl_file.configure(text="No file selected", text_color=c["placeholder_foreground"])
        self.btn_select_file.stop(state="normal")
        self.lbl_out.configure(text="(auto: same folder, suffix \"_trimmed\")", text_color=c["placeholder_foreground"])

        self._set_preview("start", None)
        self._set_preview("end", None)
        self.trim_timeline.set_range(0.0, 1.0)
        self.trim_timeline.set_enabled(False)

    ########################################################## THEMING ##########################################################

    def _apply_theme(self) -> None:
        self._current_theme = get_system_theme()
        c: dict[str, str] = dict(COLORS[self._current_theme])

        ctk.set_appearance_mode(self._current_theme)
        self.configure(fg_color=c["background"])

        self.main_frame.configure(fg_color=c["background"])
        self.sec_file.configure(fg_color=c["background"])
        self.sec_trim.configure(fg_color=c["background"])
        self.trim_header.configure(fg_color=c["background"])
        self.sec_preview.configure(fg_color=c["background"])
        self.sec_inputs.configure(fg_color=c["background"])
        self.sec_out.configure(fg_color=c["background"])

        self.lbl_section_file.configure(text_color=c["foreground"])
        self.lbl_section_trim.configure(text_color=c["foreground"])
        self.lbl_section_out.configure(text_color=c["foreground"])

        self.lbl_start.configure(text_color=c["muted_foreground"])
        self.lbl_end.configure(text_color=c["muted_foreground"])
        self.lbl_hint.configure(text_color=c["muted_foreground"])

        self.lbl_file.configure(text_color=c["foreground"] if self.selected_file else c["placeholder_foreground"])
        self.lbl_out.configure(text_color=c["foreground"] if self.output_path else c["placeholder_foreground"])

        # PREVIEW THUMBNAILS
        for frame in (self.frame_start_thumb, self.frame_end_thumb):
            frame.configure(fg_color=c["background"], border_color=c["border"])
        for lbl in (self.lbl_start_thumb, self.lbl_end_thumb):
            lbl.configure(text_color=c["placeholder_foreground"], fg_color="transparent")

        # MODE TOGGLE
        self.mode_toggle.configure(
            fg_color=c["background"],
            border_color=c["secondary_border"],
            selected_color=c["primary"],
            selected_hover_color=c["primary_hover"],
            unselected_color=c["background"],
            unselected_hover_color=c["secondary_hover"],
            text_color=c["foreground"],
        )

        # TIMELINE
        self.trim_timeline.apply_colors(c)

        # STEPPER BUTTONS
        _chevron_left = render_svg_icon("chevron-left", 14, c["muted_foreground"])
        _chevron_right = render_svg_icon("chevron-right", 14, c["muted_foreground"])
        for btn, icon in (
            (self.btn_start_left, _chevron_left),
            (self.btn_start_right, _chevron_right),
            (self.btn_end_left, _chevron_left),
            (self.btn_end_right, _chevron_right),
        ):
            btn.configure(
                fg_color=c["secondary"],
                hover_color=c["secondary_hover"],
                border_color=c["secondary_border"],
                text_color=c["muted_foreground"],
                image=icon,
            )

        self.btn_select_file.configure(fg_color=c["card"], hover_color=c["card_hover"], text_color=c["card_foreground"])
        self.btn_select_out.configure(
            fg_color=c["secondary"],
            hover_color=c["secondary_hover"],
            border_color=c["secondary_border"],
            text_color=c["secondary_foreground"],
        )
        self.btn_reset_all.configure(
            width=28,
            height=28,
            image=render_svg_icon("refresh-ccw", 16, c["muted_foreground"]),
            fg_color="transparent",
            hover_color=c["secondary_hover"],
        )

        for entry in (self.entry_start, self.entry_end):
            entry.configure(
                fg_color=c["background"],
                border_color=c["secondary_border"],
                text_color=c["foreground"],
                placeholder_text_color=c["placeholder_foreground"],
            )

        if self.btn_apply:
            self.btn_apply.configure(
                fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["primary_foreground"]
            )
        if hasattr(self, "progress_bar"):
            self.progress_bar.configure(
                fg_color=c["secondary_hover"], progress_color=c["placeholder_foreground"]
            )

        if hasattr(self, "_banner"):
            self._banner.configure(fg_color=c["destructive"], border_color=c["destructive_border"])
            for lbl, key in self._banner_labels:
                lbl.configure(text_color=c[key])

    def _verify_ffmpeg(self) -> None:
        """Verify FFmpeg and FFprobe run; called in a background thread."""
        ok = False
        if self.ffmpeg_path and self.ffprobe_path:
            try:
                subprocess.run([self.ffmpeg_path, "-version"], capture_output=True, timeout=5, check=True, **_POPEN_FLAGS)
                subprocess.run([self.ffprobe_path, "-version"], capture_output=True, timeout=5, check=True, **_POPEN_FLAGS)
                ok = True
            except Exception:
                ok = False

        def _done() -> None:
            if not ok:
                self.ffmpeg_path = None
                self.ffprobe_path = None
            if self.btn_apply:
                self.btn_apply.stop(state="normal" if ok else "disabled")

        self.after(0, _done)

    def _poll_theme(self) -> None:
        if get_system_theme() != self._current_theme:
            self._apply_theme()
        self.after(2000, self._poll_theme)

    ########################################################## TRIMMING ##########################################################

    def _animate_progress_to(self, target: float) -> None:
        """Ease-out animate the progress bar toward `target` at ~60 fps."""
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

    def apply_trim(self) -> None:
        if not self.ffmpeg_path:
            return
        if not self.selected_file:
            messagebox.showwarning("No File", "Please select a video file first.")
            return
        if self._trimming:
            return

        # PARSE CURRENT ENTRY VALUES (HANDLES UNCOMMITTED CHANGES)
        start_str = self.entry_start.get().strip()
        end_str = self.entry_end.get().strip()

        start_s: float = 0.0
        if start_str:
            if self._input_mode == "frame":
                fps = self.fps or _DEFAULT_FPS
                try:
                    start_s = frame_to_time(int(start_str), fps)
                except (ValueError, TypeError):
                    messagebox.showerror("Invalid Start", f'Cannot parse start frame: "{start_str}"')
                    return
            else:
                if (parsed := parse_time(start_str)) is None:
                    messagebox.showerror("Invalid Start", f'Cannot parse start time: "{start_str}"')
                    return
                start_s = parsed

        end_s: Optional[float] = None
        if end_str:
            if self._input_mode == "frame":
                fps = self.fps or _DEFAULT_FPS
                try:
                    end_s = frame_to_time(int(end_str), fps)
                except (ValueError, TypeError):
                    messagebox.showerror("Invalid End", f'Cannot parse end frame: "{end_str}"')
                    return
            else:
                if (parsed := parse_time(end_str)) is None:
                    messagebox.showerror("Invalid End", f'Cannot parse end time: "{end_str}"')
                    return
                end_s = parsed

        if end_s is not None and end_s <= start_s:
            messagebox.showerror("Invalid Range", "End time must be greater than start time.")
            return

        if self.duration is not None:
            if start_s >= self.duration:
                messagebox.showerror("Invalid Range", "Start time is past the end of the file.")
                return
            if end_s is not None and end_s > self.duration + 0.5:
                messagebox.showerror("Invalid Range", "End time is past the end of the file.")
                return

        # RESOLVE OUTPUT PATH
        if self.output_path:
            out_path = self.output_path
        else:
            p = Path(self.selected_file)
            out_path = str(p.with_name(f"{p.stem}_trimmed{p.suffix}"))

        if Path(out_path).resolve() == Path(self.selected_file).resolve():
            messagebox.showerror("Invalid Output", "Output path must differ from the input file.")
            return

        if Path(out_path).exists():
            if not messagebox.askokcancel(
                    "Overwrite?",
                    f'"{Path(out_path).name}" already exists.\n\nOverwrite this file?',
                    icon="warning",
            ):
                return

        # BUILD FFMPEG COMMAND – STREAM COPY (FAST, LOSSLESS)
        cmd: list[str] = [self.ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error", "-progress", "pipe:1"]
        cmd += ["-ss", format_time(start_s)]
        if end_s is not None:
            cmd += ["-to", format_time(end_s)]
        cmd += ["-i", self.selected_file, "-c", "copy", "-map", "0", "-avoid_negative_ts", "make_zero", out_path]

        clip_total: Optional[float] = None
        if end_s is not None:
            clip_total = end_s - start_s
        elif self.duration is not None:
            clip_total = self.duration - start_s

        self._trimming = True

        if self.btn_apply:
            self.btn_apply.start(COLORS[self._current_theme]["primary_foreground"])

        if hasattr(self, "progress_bar"):
            if self._progress_anim_id:
                self.after_cancel(self._progress_anim_id)
            self._progress_anim_id = None
            self._progress_anim_current = 0.0
            self.progress_bar.set(0)
            self.progress_bar.grid()

        result_holder: dict[str, object] = {"err": None, "ok": False}

        def _on_done() -> None:
            self._trimming = False

            if self.btn_apply:
                self.btn_apply.stop(state="normal")

            if hasattr(self, "progress_bar"):
                if self._progress_anim_id:
                    self.after_cancel(self._progress_anim_id)
                    self._progress_anim_id = None
                self.progress_bar.grid_remove()

            if result_holder["ok"]:
                messagebox.showinfo("Success", f"Saved trimmed video to:\n{out_path}")
            else:
                err = result_holder["err"] or "Unknown error"
                messagebox.showerror("FFmpeg Error", f"Failed to trim video:\n{err}")

        def _worker() -> None:
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    **_POPEN_FLAGS,
                )
            except Exception as err:
                result_holder["err"] = str(err)
                self.after(0, _on_done)
                return

            assert proc.stdout is not None

            for line in proc.stdout:
                if not (line := line.strip()) or "=" not in line:
                    continue

                key, _, val = line.partition("=")
                if key == "out_time_ms" and clip_total and val.isdigit():
                    elapsed = int(val) / 1_000_000.0
                    frac = max(0.0, min(0.99, elapsed / clip_total))
                    self.after(0, lambda f=frac: self._animate_progress_to(f))
                elif key == "progress" and val == "end":
                    self.after(0, lambda: self._animate_progress_to(1.0))

            stderr_out: str = proc.stderr.read() if proc.stderr is not None else ""
            rc = proc.wait()

            if rc == 0:
                result_holder["ok"] = True
            else:
                result_holder["err"] = stderr_out.strip() or f"FFmpeg exited with code {rc}"

            self.after(0, _on_done)

        threading.Thread(target=_worker, daemon=True).start()


if __name__ == "__main__":
    ctk.set_appearance_mode(get_system_theme())
    ctk.set_default_color_theme("blue")

    # ON WINDOWS, SET THE APP USER MODEL ID BEFORE CREATING THE WINDOW SO THE
    # TASKBAR GROUPS THE APP UNDER ITS OWN ICON RATHER THAN THE PYTHON INTERPRETER
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VideoTrimmer.app")
        except Exception:
            pass

    app = VideoTrimmerApp()

    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.destroy()

    # CLEAN UP TEMP FILES
    if app._temp_ico_path and app._temp_ico_path.exists():
        app._temp_ico_path.unlink()
