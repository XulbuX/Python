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
    """Frame-accurate video trim via FFmpeg.\n
    ----------------------------------------------------------------------------
    Input seek (`-ss before -i`) jumps cheaply to ~2 s before the target.<br>
    Output seek (`-ss after -i`) then decodes to the exact requested frame.<br>
    Re-encoding is required for frame accuracy; the source video bitrate<br>
    is probed and matched so output size is proportional to clip length."""

    def __init__(self, ffmpeg_path: str, ffprobe_path: Optional[str] = None) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
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
        # INPUT SEEK TO ~2s BEFORE THE TARGET REDUCES DECODING COST FOR LONG INPUTS.
        # OUTPUT SEEK (-ss AFTER -i) IS FRAME-ACCURATE BECAUSE RE-ENCODING IS USED.
        prelude = max(0.0, start_s - 2.0)
        rel_start = start_s - prelude

        cmd: list[str] = [self.ffmpeg_path, "-y", "-hide_banner", "-loglevel", "error", "-progress", "pipe:1"]

        if prelude > 0:
            cmd += ["-ss", format_time(prelude)]

        cmd += ["-i", src, "-ss", format_time(rel_start)]

        if end_s is not None:
            cmd += ["-to", format_time(end_s - prelude)]

        # MATCH SOURCE BITRATE SO OUTPUT SIZE SCALES PROPORTIONALLY WITH CLIP LENGTH.
        # FALL BACK TO CRF 23 (LIBX264 DEFAULT) IF PROBING FAILS.
        video_bitrate = self._probe_video_bitrate(src)
        video_flags = ["libx264", "-b:v", str(video_bitrate)] if video_bitrate else ["libx264", "-crf", "23"]
        video_flags += ["-preset", "medium"]

        cmd += ["-map", "0", "-c:v"] + video_flags + ["-c:a", "copy", "-c:s", "copy", "-avoid_negative_ts", "make_zero", dst]

        return cmd

    def _probe_video_bitrate(self, src: str) -> Optional[int]:
        """Return the video stream bitrate in bits/s, or None if unavailable."""
        if not self.ffprobe_path:
            return None

        # TRY STREAM-LEVEL BITRATE FIRST
        try:
            res = subprocess.run(
                [
                    self.ffprobe_path, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=bit_rate", "-of",
                    "default=noprint_wrappers=1:nokey=1", src
                ],
                capture_output=True,
                text=True,
                timeout=10,
                **_POPEN_FLAGS,
            )

            if (val := res.stdout.strip()).isdigit() and int(val) > 0:
                return int(val)

        except Exception:
            pass

        # FALL BACK TO FORMAT (CONTAINER) BITRATE MINUS A TYPICAL AUDIO ESTIMATE
        try:
            res = subprocess.run(
                [
                    self.ffprobe_path, "-v", "error", "-show_entries", "format=bit_rate", "-of",
                    "default=noprint_wrappers=1:nokey=1", src
                ],
                capture_output=True,
                text=True,
                timeout=10,
                **_POPEN_FLAGS,
            )

            if (val := res.stdout.strip()).isdigit() and int(val) > 0:
                return max(1, int(val) - 192_000)  # SUBTRACT TYPICAL AUDIO BITRATE

        except Exception:
            pass

        return None

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
        except Exception as exc:
            on_done(False, str(exc))
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
