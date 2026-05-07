# pyright: basic
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Optional
import customtkinter as ctk
import subprocess
import webbrowser
import threading
import ctypes
import shutil
import json
import sys

# MAKE THE _shared PACKAGE (apps/src/_shared) IMPORTABLE WHEN RUNNING THIS SCRIPT DIRECTLY
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# USE ABSOLUTE IMPORTS DURING RUNTIME AND RELATIVE ONES DURING DEVELOPMENT SO THE TYPES ARE LINKED CORRECTLY IN THE IDE
from _shared.consts import COLORS, POPEN_FLAGS as _POPEN_FLAGS  # type: ignore[missing-import]
from _shared.helpers import resolve_mono_font, get_system_theme, setup_window_icon  # type: ignore[missing-import]
from _shared.widgets import SpinnerButton, ToolTip, bind_clean_paste, render_svg_icon  # type: ignore[missing-import]
if TYPE_CHECKING:
    from .._shared.consts import COLORS, POPEN_FLAGS as _POPEN_FLAGS
    from .._shared.helpers import resolve_mono_font, get_system_theme, setup_window_icon
    from .._shared.widgets import SpinnerButton, ToolTip, bind_clean_paste, render_svg_icon

from consts import VIDEO_FILE_TYPES, APP_ICON_PNG
from helpers import parse_time, format_time


class VideoTrimmerApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        self.title("Video Trimmer")
        self.resizable(False, False)

        # CENTERED FIXED-SIZE WINDOW
        ww, wh = 540, 360
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
        self.output_path: Optional[str] = None

        self._current_theme: str = get_system_theme()
        self._trimming: bool = False

        ################################################## UI LAYOUT ##################################################
        PAD: int = 16

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=PAD, pady=PAD)

        #################### HEADER ####################
        self.sec_header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.sec_header.pack(fill="x")

        self.lbl_title = ctk.CTkLabel(self.sec_header, text="Video Trimmer", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_title.pack(side="left")

        self.btn_reset_all = ctk.CTkButton(
            self.sec_header, text="", width=28, height=28, corner_radius=6, border_width=0, command=self.reset_all
        )
        self.btn_reset_all.pack(side="right")
        ToolTip(self.btn_reset_all, "Reset all fields")

        # SEPARATOR
        self.sep1 = ctk.CTkFrame(self.main_frame, height=1)
        self.sep1.pack(fill="x", pady=(PAD, 0))

        #################### SELECT FILE SECTION ####################
        self.sec_file = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.sec_file.pack(fill="x", pady=(PAD, 0))
        self.sec_file.grid_columnconfigure(1, weight=1)

        self.lbl_section_file = ctk.CTkLabel(self.sec_file, text="Select Video", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_section_file.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.btn_select_file = ctk.CTkButton(self.sec_file, text="Select Video File", command=self.select_file)
        self.btn_select_file.grid(row=1, column=0, sticky="w")

        self.lbl_file = ctk.CTkLabel(self.sec_file, text="No file selected", anchor="w")
        self.lbl_file.grid(row=1, column=1, padx=(10, 0), sticky="ew")

        self.lbl_duration = ctk.CTkLabel(self.sec_file, text="", anchor="w", font=resolve_mono_font(12))
        self.lbl_duration.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        #################### TRIM RANGE SECTION ####################
        self.sec_trim = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.sec_trim.pack(fill="x", pady=(PAD, 0))
        self.sec_trim.grid_columnconfigure(1, weight=1)
        self.sec_trim.grid_columnconfigure(3, weight=1)

        self.lbl_section_trim = ctk.CTkLabel(self.sec_trim, text="Trim Range", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_section_trim.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))

        self.lbl_start = ctk.CTkLabel(self.sec_trim, text="Start")
        self.lbl_start.grid(row=1, column=0, sticky="w", padx=(0, 8))
        self.entry_start = ctk.CTkEntry(self.sec_trim, border_width=1, placeholder_text="00:00")
        self.entry_start.grid(row=1, column=1, sticky="ew")
        bind_clean_paste(self.entry_start._entry)

        self.lbl_end = ctk.CTkLabel(self.sec_trim, text="End")
        self.lbl_end.grid(row=1, column=2, sticky="w", padx=(PAD, 8))
        self.entry_end = ctk.CTkEntry(self.sec_trim, border_width=1, placeholder_text="end of file")
        self.entry_end.grid(row=1, column=3, sticky="ew")
        bind_clean_paste(self.entry_end._entry)

        self.lbl_hint = ctk.CTkLabel(
            self.sec_trim,
            text="Format: SS, MM:SS or HH:MM:SS  (decimals allowed, e.g. 1:23.5)",
            font=ctk.CTkFont(size=11),
        )
        self.lbl_hint.grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

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

        self._apply_theme()
        self.after(2000, self._poll_theme)

        # VERIFY FFMPEG IN THE BACKGROUND SO THE UI IS FULLY RENDERED FIRST
        if self.ffmpeg_path and self.ffprobe_path and self.btn_apply:
            self.btn_apply.start(COLORS[self._current_theme]["primary_foreground"])
            threading.Thread(target=self._verify_ffmpeg, daemon=True).start()

    def select_file(self) -> None:
        if not (filename := filedialog.askopenfilename(title="Select Video File", filetypes=VIDEO_FILE_TYPES)):
            return

        self.selected_file = filename
        self.duration = None
        c = COLORS[self._current_theme]
        self.lbl_file.configure(text=Path(filename).name, text_color=c["foreground"])
        self.lbl_duration.configure(text="Reading duration\u2026", text_color=c["muted_foreground"])

        threading.Thread(target=self._probe_duration, args=(filename, ), daemon=True).start()

    def _probe_duration(self, filename: str) -> None:
        """Probe the file's duration via FFprobe; called in a background thread."""
        if not self.ffprobe_path:
            return

        cmd = [self.ffprobe_path, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", filename]
        duration: Optional[float] = None

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, **_POPEN_FLAGS)
            data = json.loads(res.stdout or "{}")

            if d := data.get("format", {}).get("duration"):
                duration = float(d)
            else:
                for st in data.get("streams", []):
                    if d := st.get("duration"):
                        duration = float(d)
                        break
        except Exception:
            duration = None

        def _done() -> None:
            self.duration = duration
            c = COLORS[self._current_theme]
            if duration is not None:
                self.lbl_duration.configure(text=f"Duration: {format_time(duration)}", text_color=c["muted_foreground"])
            else:
                self.lbl_duration.configure(text="Duration: unknown", text_color=c["destructive_label"])

        self.after(0, _done)

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
        """Clear all fields."""
        self.entry_start.delete(0, "end")
        self.entry_end.delete(0, "end")

        self.selected_file = None
        self.duration = None
        self.output_path = None

        c = COLORS[self._current_theme]
        self.lbl_file.configure(text="No file selected", text_color=c["placeholder_foreground"])
        self.lbl_duration.configure(text="", text_color=c["muted_foreground"])
        self.lbl_out.configure(text="(auto: same folder, suffix \"_trimmed\")", text_color=c["placeholder_foreground"])

    def _apply_theme(self) -> None:
        self._current_theme = get_system_theme()
        c: dict[str, str] = dict(COLORS[self._current_theme])

        ctk.set_appearance_mode(self._current_theme)
        self.configure(fg_color=c["background"])

        self.main_frame.configure(fg_color=c["background"])
        self.sec_header.configure(fg_color=c["background"])
        self.sec_file.configure(fg_color=c["background"])
        self.sec_trim.configure(fg_color=c["background"])
        self.sec_out.configure(fg_color=c["background"])

        self.sep1.configure(fg_color=c["border"])

        self.lbl_title.configure(text_color=c["foreground"])
        self.lbl_section_file.configure(text_color=c["foreground"])
        self.lbl_section_trim.configure(text_color=c["foreground"])
        self.lbl_section_out.configure(text_color=c["foreground"])

        self.lbl_start.configure(text_color=c["muted_foreground"])
        self.lbl_end.configure(text_color=c["muted_foreground"])
        self.lbl_hint.configure(text_color=c["muted_foreground"])

        self.lbl_file.configure(text_color=c["foreground"] if self.selected_file else c["placeholder_foreground"])
        self.lbl_duration.configure(text_color=c["muted_foreground"])
        self.lbl_out.configure(text_color=c["foreground"] if self.output_path else c["placeholder_foreground"])

        self.btn_select_file.configure(fg_color=c["card"], hover_color=c["card_hover"], text_color=c["card_foreground"])
        self.btn_select_out.configure(
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

        for entry in (self.entry_start, self.entry_end):
            entry.configure(
                fg_color=c["background"],
                border_color=c["secondary_border"],
                text_color=c["foreground"],
                placeholder_text_color=c["placeholder_foreground"],
            )

        if self.btn_apply:
            self.btn_apply.configure(fg_color=c["primary"], hover_color=c["primary_hover"], text_color=c["primary_foreground"])
        if hasattr(self, "progress_bar"):
            self.progress_bar.configure(fg_color=c["secondary_hover"], progress_color=c["placeholder_foreground"])

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

    def apply_trim(self) -> None:
        if not self.ffmpeg_path:
            return
        if not self.selected_file:
            messagebox.showwarning("No File", "Please select a video file first.")
            return
        if self._trimming:
            return

        start_str = self.entry_start.get().strip()
        end_str = self.entry_end.get().strip()

        # PARSE START / END (BOTH OPTIONAL: BLANK START → 0, BLANK END → END OF FILE)
        start_s: float = 0.0
        if start_str:
            if (parsed_start := parse_time(start_str)) is None:
                messagebox.showerror("Invalid Start", f'Cannot parse start time: "{start_str}"')
                return
            start_s = parsed_start

        end_s: Optional[float] = None
        if end_str:
            if (end_s := parse_time(end_str)) is None:
                messagebox.showerror("Invalid End", f'Cannot parse end time: "{end_str}"')
                return

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

        # TOTAL DURATION USED FOR PROGRESS REPORTING
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

            # PARSE FFMPEG'S `-progress pipe:1` STREAM (KEY=VALUE LINES) FOR LIVE PROGRESS
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
