from typing import Optional, TypedDict
from enum import IntEnum
from PIL import Image, ImageDraw
import customtkinter as ctk  # type: ignore[no-stubs]
import tkinter as tk


class FieldType(IntEnum):
    SINGLE = 1  # SINGLE-LINE CTkEntry
    EXPANDING = 2  # SINGLE-LINE THAT EXPANDS TO MULTI-LINE (NO HARD NEWLINES)
    MULTILINE = 3  # FREE MULTI-LINE WITH NEWLINES ALLOWED


class FieldDef(TypedDict):
    tags: tuple[str, ...]  # PRIMARY (CROSS-PLATFORM) TAG FIRST; ALL ARE WRITTEN, PRIMARY USED FOR READING BACK
    type: FieldType


class FieldEntry(TypedDict):
    tags: tuple[str, ...]  # PRIMARY (CROSS-PLATFORM) TAG FIRST; ALL ARE WRITTEN, PRIMARY USED FOR READING BACK
    widget: ctk.CTkEntry  # ctk.CTkEntry OR MultilineEntry


class MultilineEntry(ctk.CTkTextbox):
    """Auto-resizing `CTkTextbox`: single-line height when content fits on one display line,
    three-line height the moment it wraps. Pass `allow_newlines=True` for real line breaks."""

    def __init__(self, master: object, allow_newlines: bool = False, always_expanded: bool = False, **kwargs: object) -> None:
        kwargs.pop("height", None)
        super().__init__(master, **kwargs)  # type: ignore[arg-type]

        self._expanded: bool | None = None
        self._always_expanded = always_expanded

        # REMOVE tk.Text INTERNAL PADDING AND TRIM THE SCROLLBAR-ROW/COL MINSIZE SO THE
        # COLLAPSED HEIGHT MATCHES CTkEntry (42px RENDERED AT 1.5x SCALING)
        self._textbox.configure(pady=0)
        self.grid_rowconfigure(1, minsize=7)
        self.grid_columnconfigure(1, minsize=7)

        if not allow_newlines:
            self.bind("<Return>", lambda _e: "break")
            self.bind("<Shift-Return>", lambda _e: "break")

        self._textbox.bind("<<Modified>>", self._on_modified)
        if always_expanded:
            self._expanded = True
            self.configure(height=80)
        else:
            self.after_idle(self._update_height)

    def _on_modified(self, _event: object = None) -> None:
        # DEFER VIA after_idle SO RAPID-FIRE EVENTS (INCLUDING THE SPURIOUS RE-TRIGGER
        # THAT TKINTER EMITS WHEN edit_modified(False) IS CALLED) ARE COLLAPSED
        self.after_idle(self._do_modified)

    def _do_modified(self) -> None:
        # IF THE FLAG WAS ALREADY CLEARED BY A PREVIOUS IDLE CALLBACK, SKIP
        if not self._textbox.edit_modified():
            return
        self._textbox.edit_modified(False)
        self._update_height()

    def _update_height(self) -> None:
        result = self._textbox.count("1.0", "end", "displaylines")
        expanded = self._always_expanded or (result[0] if result else 1) > 1

        if expanded == self._expanded:
            return  # STATE UNCHANGED, NO REDRAW NEEDED

        self._expanded = expanded
        if not expanded:
            self.configure(height=28)

        else:
            if info := self._textbox.dlineinfo("1.0"):
                scale: float = getattr(self, "_get_widget_scaling", lambda: 1.0)()
                self.configure(height=round(2 * info[3] / scale + 28))
            else:
                self.configure(height=80)

    def get(self) -> str:  # type: ignore[override]
        return super().get("1.0", "end").rstrip("\n")

    def delete(self, _start: object, _end: object = None) -> None:  # type: ignore[override]
        super().delete("1.0", "end")

    def insert(self, _index: object, value: str) -> None:  # type: ignore[override]
        super().delete("1.0", "end")
        super().insert("1.0", value)


class ToolTip:
    """Minimal hover tooltip for any tkinter/CTk widget."""

    def __init__(self, widget: object, text: str, delay_ms: int = 1000) -> None:
        self._widget = widget
        self._text = text
        self._tip: object = None
        self._after_id: Optional[str] = None
        self._delay_ms = delay_ms
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _schedule(self, event: object = None) -> None:
        if self._after_id:
            self._widget.after_cancel(self._after_id)
        self._after_id = self._widget.after(self._delay_ms, self._show)

    _TIP_R = 14
    _TIP_PX, _TIP_PY = 10, 7
    _TIP_COLORS = {
        "dark": {"bg": "#252525", "border": "#3F3F46", "fg": "#D4D4D4"},
        "light": {"bg": "#FFFFFF", "border": "#E4E4E7", "fg": "#18181B"},
    }
    _TIP_TRANSPARENT = "#010203"  # UNIQUE NEAR-BLACK USED AS TRANSPARENCY KEY ON WINDOWS

    def _show(self, event: object = None) -> None:
        self._after_id = None
        if self._tip:
            return
        x = int(self._widget.winfo_rootx()) + 20
        y = int(self._widget.winfo_rooty() + self._widget.winfo_height()) + 4

        mode = ctk.get_appearance_mode()
        tip_bg = self._TIP_COLORS.get(mode, self._TIP_COLORS["dark"])["bg"]
        tip_fg = self._TIP_COLORS.get(mode, self._TIP_COLORS["dark"])["fg"]
        tip_border = self._TIP_COLORS.get(mode, self._TIP_COLORS["dark"])["border"]

        # MEASURE WIDTH FROM FULL TEXT, THEN EACH PARAGRAPH SEPARATELY FOR HEIGHT
        PARA_GAP = 6
        probe = tk.Label(self._widget, text=self._text, font=("TkDefaultFont", 11), justify="left", wraplength=280)
        probe.update_idletasks()
        tw = probe.winfo_reqwidth() + self._TIP_PX * 2
        probe.destroy()

        text_w = tw - self._TIP_PX * 2
        paragraphs = self._text.split("\n")
        para_heights: list[int] = []
        for para in paragraphs:
            p = tk.Label(self._widget, text=para or " ", font=("TkDefaultFont", 11), justify="left", wraplength=text_w)
            p.update_idletasks()
            para_heights.append(p.winfo_reqheight())
            p.destroy()
        th = sum(para_heights) + PARA_GAP * (len(paragraphs) - 1) + self._TIP_PY * 2

        r = self._TIP_R
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"{tw}x{th}+{x}+{y}")
        self._tip.configure(bg=self._TIP_TRANSPARENT)
        try:
            self._tip.wm_attributes("-transparentcolor", self._TIP_TRANSPARENT)
        except tk.TclError:
            pass

        cv = tk.Canvas(self._tip, width=tw, height=th, bg=self._TIP_TRANSPARENT, highlightthickness=0)
        cv.pack()
        # ROUNDED RECTANGLE VIA smooth=True POLYGON; BORDER DRAWN FIRST (1px LARGER), FILL ON TOP
        pts = [r, 0, tw - r, 0, tw, 0, tw, r, tw, th - r, tw, th, tw - r, th, r, th, 0, th, 0, th - r, 0, r, 0, 0]
        cv.create_polygon(pts, smooth=True, fill=tip_border, outline="")
        inset = 1
        ipts = [
            r, inset, tw - r, inset, tw, inset, tw, r, tw, th - r, tw, th - inset, tw - r, th - inset, r, th - inset, inset,
            th - inset, inset, th - r, inset, r, inset, inset
        ]
        cv.create_polygon(ipts, smooth=True, fill=tip_bg, outline="")
        ty = self._TIP_PY
        for para, ph in zip(paragraphs, para_heights):
            cv.create_text(
                self._TIP_PX,
                ty,
                text=para,
                anchor="nw",
                fill=tip_fg,
                font=("TkDefaultFont", 11),
                width=text_w,
                justify="left"
            )
            ty += ph + PARA_GAP

    def _hide(self, event: object = None) -> None:
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        if self._tip:
            self._tip.destroy()
            self._tip = None


class SpinnerButton(ctk.CTkButton):
    """`CTkButton` with an animated spinner that replaces the button content while busy."""

    _FRAME_COUNT: int = 36
    _INTERVAL_MS: int = 33

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self._spin_frames: list[ctk.CTkImage] = []
        self._spin_idx: int = 0
        self._spin_after_id: Optional[str] = None
        self._spinning: bool = False
        self._saved_text: str = ""
        self._saved_state: str = "normal"

    def _build_frames(self, color_hex: str, size: int = 18) -> None:
        try:
            r, g, b = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
        except (ValueError, IndexError):
            r, g, b = 255, 255, 255

        alpha = 160

        # RENDER AT 3× FOR ANTI-ALIASING, THEN DOWNSAMPLE
        HI = size * 3
        sc = HI / 24.0
        stroke_w = max(2, round(2 * sc / 3.0))
        rad = stroke_w / 2.0
        color = (r, g, b, alpha)

        # DRAW THE ICON ONCE AS A STATIC BASE IMAGE
        base = Image.new("RGBA", (HI, HI), (0, 0, 0, 0))
        draw = ImageDraw.Draw(base)
        for (x1, y1), (x2, y2) in [
            ((12.0, 2.0), (12.0, 6.0)),
            ((16.2, 7.8), (19.1, 4.9)),
            ((18.0, 12.0), (22.0, 12.0)),
            ((16.2, 16.2), (19.1, 19.1)),
            ((12.0, 18.0), (12.0, 22.0)),
            ((4.9, 19.1), (7.8, 16.2)),
            ((2.0, 12.0), (6.0, 12.0)),
            ((4.9, 4.9), (7.8, 7.8)),
        ]:
            x1s, y1s, x2s, y2s = x1 * sc, y1 * sc, x2 * sc, y2 * sc
            draw.line([(x1s, y1s), (x2s, y2s)], fill=color, width=stroke_w)
            for cx, cy in ((x1s, y1s), (x2s, y2s)):
                draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=color)

        # EACH FRAME PHYSICALLY ROTATES THE BASE IMAGE CLOCKWISE BY ONE STEP
        step = 360.0 / self._FRAME_COUNT
        self._spin_frames = []
        for i in range(self._FRAME_COUNT):
            rotated = base.rotate(-i * step, resample=Image.BICUBIC, expand=False)
            lo = rotated.resize((size, size), Image.LANCZOS)
            self._spin_frames.append(ctk.CTkImage(light_image=lo, dark_image=lo, size=(size, size)))

    def start(self, color_hex: str = "#FFFFFF") -> None:
        if self._spinning:
            return
        self._build_frames(color_hex)
        self._saved_text = str(self.cget("text"))
        self._saved_state = str(self.cget("state"))
        self._spinning = True
        self._spin_idx = 0
        self.configure(text="", image=self._spin_frames[0], state="disabled")
        self._tick()

    def stop(self, *, state: Optional[str] = None) -> None:
        if not self._spinning:
            return
        self._spinning = False
        if self._spin_after_id is not None:
            self.after_cancel(self._spin_after_id)
            self._spin_after_id = None
        self.configure(text=self._saved_text, image=None, state=state if state is not None else self._saved_state)

    def _tick(self) -> None:
        if not self._spinning:
            return
        self._spin_idx = (self._spin_idx + 1) % len(self._spin_frames)
        self.configure(image=self._spin_frames[self._spin_idx])
        self._spin_after_id = self.after(self._INTERVAL_MS, self._tick)
