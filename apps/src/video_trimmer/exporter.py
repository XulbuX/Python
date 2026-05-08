"""Frame-accurate, lossless video trimming via FFmpeg.\n
----------------------------------------------------------------------
The exporter runs ffmpeg in a background thread and reports<br>
progress via callbacks. The caller is responsible for marshalling<br>
those callbacks back onto its UI thread (e.g. with `tk.after`).
"""
from typing import Callable, Optional
import subprocess
import threading

# SHARED – ABSOLUTE IMPORTS DURING RUNTIME, RELATIVE ONES DURING DEVELOPMENT
from _shared.consts import POPEN_FLAGS as _POPEN_FLAGS

from helpers import format_time


ProgressCallback = Callable[[float], None]
DoneCallback = Callable[[bool, Optional[str]], None]


class TrimExporter:
    """Run a frame-accurate, mathematically lossless trim using FFmpeg.\n
    ----------------------------------------------------------------------
    The output is re-encoded with `libx264 -qp 0` (bit-exact pixels),<br>
    audio is stream-copied, subtitles are stream-copied. Output seek<br>
    is used so the cut lands on the exact requested frame."""

    def __init__(self, ffmpeg_path: str) -> None:
        self.ffmpeg_path = ffmpeg_path
        self._proc: Optional[subprocess.Popen[str]] = None

    def export(
        self,
        src: str,
        dst: str,
        start_s: float,
        end_s: Optional[float],
        clip_total: Optional[float],
        on_progress: ProgressCallback,
        on_done: DoneCallback,
    ) -> threading.Thread:
        """Start a background trim. Returns the worker thread."""
        thread = threading.Thread(
            target=self._worker,
            args=(src, dst, start_s, end_s, clip_total, on_progress, on_done),
            daemon=True,
        )
        thread.start()

        return thread

    def cancel(self) -> None:
        """Kill the in-flight ffmpeg process if any."""
        if (proc := self._proc) is not None and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass

    ######################################## INTERNAL ########################################

    def _build_cmd(self, src: str, dst: str, start_s: float, end_s: Optional[float]) -> list[str]:
        # FAST INPUT SEEK TO ~2s BEFORE THE TARGET CUTS DECODE COST FOR LONG INPUTS.
        # OUTPUT SEEK (-ss/-to AFTER -i) IS FRAME-ACCURATE.
        prelude = max(0.0, start_s - 2.0)
        rel_start = start_s - prelude

        cmd: list[str] = [self.ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error", "-progress", "pipe:1"]

        if prelude > 0:
            cmd += ["-ss", format_time(prelude)]

        cmd += ["-i", src, "-ss", format_time(rel_start)]

        if end_s is not None:
            cmd += ["-to", format_time(end_s - prelude)]

        cmd += [
            "-map", "0", "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0", "-c:a", "copy", "-c:s", "copy",
            "-avoid_negative_ts", "make_zero", dst
        ]

        return cmd

    def _worker(
        self,
        src: str,
        dst: str,
        start_s: float,
        end_s: Optional[float],
        clip_total: Optional[float],
        on_progress: ProgressCallback,
        on_done: DoneCallback,
    ) -> None:
        cmd = self._build_cmd(src, dst, start_s, end_s)

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
            self._proc = proc
        except Exception as err:
            on_done(False, str(err))
            return

        assert proc.stdout is not None

        for line in proc.stdout:
            if not (line := line.strip()) or "=" not in line:
                continue

            key, _, val = line.partition("=")

            if key == "out_time_ms" and clip_total and val.isdigit():
                elapsed = int(val) / 1_000_000.0
                frac = max(0.0, min(0.99, elapsed / clip_total))
                on_progress(frac)

            elif key == "progress" and val == "end":
                on_progress(1.0)

        stderr_out: str = proc.stderr.read() if proc.stderr is not None else ""
        rc = proc.wait()
        self._proc = None

        if rc == 0:
            on_done(True, None)
        else:
            on_done(False, stderr_out.strip() or f"FFmpeg exited with code {rc}")
