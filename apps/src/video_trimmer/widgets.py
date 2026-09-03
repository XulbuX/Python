import tkinter as tk
from typing import TYPE_CHECKING
import customtkinter as ctk  # type:ignore[no-stubs]
from _shared.consts import COLORS

if TYPE_CHECKING:
    from collections.abc import Callable


class TrimTimeline(tk.Canvas):
    """Draggable timeline range selector for video trimming.\n
    ------------------------------------------------------------------------------------
    `on_change(start_frac, end_frac)` is fired continuously while dragging.<br>
    `on_commit(start_frac, end_frac)` is fired once on mouse-button release.<br>
    Both fractions are in [0.0, 1.0].  Apply colors via `apply_colors(colors_dict)`."""

    _TRACK_H: int = 10
    _HANDLE_W: int = 8
    _HANDLE_H: int = 28
    _GRAB_PX: int = 14

    def __init__(self, master: tk.Misc, height: int = 36, **kwargs: object) -> None:
        super().__init__(master, height=height, highlightthickness=0, bd=0, cursor="arrow", **kwargs)  # type:ignore[arg-type]
        self._start_frac: float = 0.0
        self._end_frac: float = 1.0
        self._drag: str | None = None
        self._drag_ref_x: float = 0.0
        self._drag_ref_s: float = 0.0
        self._drag_ref_e: float = 1.0
        self._enabled: bool = True

        color = COLORS.get(ctk.get_appearance_mode().lower(), COLORS["dark"])
        self._c_bg: str = color["background"]
        self._c_track: str = color["secondary_hover"]
        self._c_range: str = color["primary"]
        self._c_range_dim: str = color["border"]
        self._c_handle: str = color["primary"]
        self.configure(bg=self._c_bg)

        self.on_change: Callable[[float, float], None] | None = None
        self.on_commit: Callable[[float, float], None] | None = None

        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Motion>", self._on_motion)

    # **************************************** PUBLIC API ****************************************

    def apply_colors(self, c: dict[str, str]) -> None:
        self._c_bg = c["background"]
        self._c_track = c["secondary_hover"]
        self._c_range = c["primary"]
        self._c_range_dim = c["border"]
        self._c_handle = c["primary"]
        self.configure(bg=c["background"])
        self._draw()

    def set_range(self, start_frac: float, end_frac: float) -> None:
        self._start_frac = max(0.0, min(1.0, start_frac))
        self._end_frac = max(self._start_frac + 0.001, min(1.0, end_frac))
        self._draw()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.configure(cursor="arrow")
        self._draw()

    # **************************************** INTERNAL HELPERS ****************************************

    def _pad(self) -> int:
        return self._HANDLE_W // 2 + 4

    def _frac_to_x(self, frac: float) -> float:
        w = max(2, self.winfo_width())
        p = self._pad()
        return p + frac * (w - 2 * p)

    def _x_to_frac(self, x: float) -> float:
        w = max(2, self.winfo_width())
        p = self._pad()
        return (x - p) / max(1, w - 2 * p)

    def _hit(self, x: float) -> str | None:
        sx = self._frac_to_x(self._start_frac)
        ex = self._frac_to_x(self._end_frac)
        if abs(x - sx) <= self._GRAB_PX:
            return "start"
        if abs(x - ex) <= self._GRAB_PX:
            return "end"
        if sx <= x <= ex:
            return "range"
        return None

    # **************************************** EVENT HANDLERS ****************************************

    def _on_motion(self, event: object) -> None:
        if not self._enabled:
            return
        zone = self._hit(event.x)  # type:ignore[attr-defined]
        if zone in ("start", "end"):
            self.configure(cursor="sb_h_double_arrow")
        elif zone == "range":
            self.configure(cursor="hand2")
        else:
            self.configure(cursor="arrow")

    def _on_press(self, event: object) -> None:
        if not self._enabled:
            return
        self._drag = self._hit(event.x)  # type:ignore[attr-defined]
        if self._drag == "range":
            self._drag_ref_x = float(event.x)  # type:ignore[attr-defined]
            self._drag_ref_s = self._start_frac
            self._drag_ref_e = self._end_frac

    def _on_drag(self, event: object) -> None:
        if not self._drag or not self._enabled:
            return
        frac = max(0.0, min(1.0, self._x_to_frac(event.x)))  # type:ignore[attr-defined]
        if self._drag == "start":
            self._start_frac = min(frac, self._end_frac - 0.001)
        elif self._drag == "end":
            self._end_frac = max(frac, self._start_frac + 0.001)
        elif self._drag == "range":
            delta = self._x_to_frac(event.x) - self._x_to_frac(self._drag_ref_x)  # type:ignore[attr-defined]
            span = self._drag_ref_e - self._drag_ref_s
            new_s = max(0.0, min(1.0 - span, self._drag_ref_s + delta))
            self._start_frac = new_s
            self._end_frac = new_s + span
        self._draw()
        if self.on_change:
            self.on_change(self._start_frac, self._end_frac)

    def _on_release(self, event: object) -> None:
        self._drag = None
        if self.on_commit and self._enabled:
            self.on_commit(self._start_frac, self._end_frac)

    # **************************************** DRAWING ****************************************

    def _draw(self) -> None:
        self.delete("all")

        if (w := self.winfo_width()) < 4 or (h := self.winfo_height()) < 4:
            return

        cy = h // 2
        ty1 = cy - self._TRACK_H // 2
        ty2 = cy + self._TRACK_H // 2
        tr = self._TRACK_H // 2
        pad = self._pad()

        tc = self._c_track if self._enabled else self._c_range_dim
        rc = self._c_range if self._enabled else self._c_range_dim
        hc = self._c_handle if self._enabled else self._c_range_dim

        # Background track:
        self._rrect(pad, ty1, w - pad, ty2, tr, tc)

        sx = self._frac_to_x(self._start_frac)
        ex = self._frac_to_x(self._end_frac)

        # Selected range fill:
        self._rrect(sx, ty1, ex, ty2, tr, rc)

        # Handle pills (taller than track):
        hw = self._HANDLE_W // 2
        hy1 = cy - self._HANDLE_H // 2
        hy2 = cy + self._HANDLE_H // 2
        hr = min(hw, 4)

        self._rrect(sx - hw, hy1, sx + hw, hy2, hr, hc)
        self._rrect(ex - hw, hy1, ex + hw, hy2, hr, hc)

    def _rrect(self, x1: float, y1: float, x2: float, y2: float, r: int, fill: str) -> None:
        """Draw a filled rounded rectangle onto this canvas."""
        x1, y1, x2, y2 = float(x1), float(y1), float(x2), float(y2)

        if (rr := max(0, min(r, int((x2 - x1) / 2), int((y2 - y1) / 2)))) < 1:
            self.create_rectangle(x1, y1, x2, y2, fill=fill, outline="")
            return

        pts: list[float] = [
            x1 + rr,
            y1,
            x2 - rr,
            y1,
            x2,
            y1,
            x2,
            y1 + rr,
            x2,
            y2 - rr,
            x2,
            y2,
            x2 - rr,
            y2,
            x1 + rr,
            y2,
            x1,
            y2,
            x1,
            y2 - rr,
            x1,
            y1 + rr,
            x1,
            y1,
        ]

        self.create_polygon(pts, smooth=True, fill=fill, outline="")
