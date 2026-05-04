# pyright: basic
from pathlib import Path
from typing import Optional
from PIL import Image
import customtkinter as ctk
import tkinter as tk
import io

from consts import ICONS  # type: ignore[missing-import]


def bind_clean_paste(tk_widget: tk.Misc) -> None:
    """Bind a `<<Paste>>` handler that strips newlines (replacing them with spaces).<br>
    Works with both `tk.Entry` and `tk.Text` (and their CTk wrappers' internal widgets)."""

    def _on_paste(_event: object) -> str:
        try:
            text: str = tk_widget.clipboard_get()
        except tk.TclError:
            return "break"

        try:
            tk_widget.delete("sel.first", "sel.last")  # type: ignore[attr-defined]
        except tk.TclError:
            pass

        tk_widget.insert(  # type: ignore[attr-defined]
            "insert",
            text.replace("\r\n", " ").replace("\r", " ").replace("\n", " "),
        )

        return "break"

    tk_widget.bind("<<Paste>>", _on_paste)


def _svg_to_pil(svg_path: Path, render_px: int, color: str) -> Image.Image:
    """Render a single SVG file to a `PIL` RGBA image at `render_px × render_px`.\n
    -------------------------------------------------------------------------------------
    Replaces `currentColor` with `color` (CSS hex string) before rasterizing.<br>
    Pipeline: `svglib` → `ReportLab PDF` (no native Cairo needed) → `PyMuPDF` → `PIL`"""
    from reportlab.graphics.renderPDF import drawToString
    from svglib.svglib import svg2rlg
    import fitz  # PyMuPDF

    svg_src = svg_path.read_text(encoding="utf-8").replace("currentColor", color)
    drawing = svg2rlg(io.BytesIO(svg_src.encode()))  # type: ignore[arg-type]

    if drawing is None:
        raise ValueError(f"Failed to parse SVG: {svg_path.name}")

    scale = render_px / drawing.width

    drawing.width = render_px
    drawing.height = render_px
    drawing.transform = (scale, 0, 0, scale, 0, 0)

    doc = fitz.open(stream=drawToString(drawing), filetype="pdf")
    pix = doc.load_page(0).get_pixmap(matrix=fitz.Matrix(1, 1), alpha=True)

    return Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)


def render_svg_icon(name: str, size: int, color: str) -> ctk.CTkImage:
    """Rasterize a named icon from `ICONS` to a `ctk.CTkImage`.\n
    ---------------------------------------------------------------------------------------
    `color` is a CSS hex string, e.g. `"#A1A1AA"`; it replaces `currentColor`.<br>
    Renders at 4× logical size so `CTkImage` can downsample cleanly on any HiDPI scale."""
    pil_img = _svg_to_pil(ICONS[name], size * 4, color)
    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))


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
            bind_clean_paste(self._textbox)

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

    def get(self) -> str:
        return super().get("1.0", "end").rstrip("\n")

    def delete(self, _start: object, _end: object = None) -> None:
        super().delete("1.0", "end")

    def insert(self, _index: object, value: str) -> None:
        super().delete("1.0", "end")
        super().insert("1.0", value)


class ToolTip:
    """Minimal hover tooltip for any tkinter/CTk widget."""

    def __init__(self, widget: tk.Misc, text: str, delay_ms: int = 1000) -> None:
        self._widget = widget
        self._text = text
        self._tip: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None
        self._delay_ms = delay_ms
        # Use widget.bind() so that for CTkButton, all internal children (canvas, text
        # label, image label) each receive the binding – CTkButton.bind() proxies to them.
        # add="+" preserves any existing bindings on those children.
        widget.bind("<Enter>", self._schedule, add="+")  # type: ignore[call-arg]
        widget.bind("<Leave>", self._hide, add="+")  # type: ignore[call-arg]

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
        tip_x = int(self._widget.winfo_rootx()) + 20
        tip_y = int(self._widget.winfo_rooty() + self._widget.winfo_height()) + 4

        mode = ctk.get_appearance_mode().lower()
        tip_bg = self._TIP_COLORS.get(mode, self._TIP_COLORS["dark"])["bg"]
        tip_fg = self._TIP_COLORS.get(mode, self._TIP_COLORS["dark"])["fg"]
        tip_border = self._TIP_COLORS.get(mode, self._TIP_COLORS["dark"])["border"]

        # COMPUTE A DPI-AWARE FONT SIZE SO THE TOOLTIP LOOKS CONSISTENT ACROSS SCREEN SCALES.
        # tk REPORTS PIXELS-PER-INCH; 96 PPI IS THE REFERENCE (100% SCALE ON MOST SYSTEMS).
        _FONT_PT = 11
        try:
            ppi = self._widget.winfo_fpixels("1i")  # PIXELS PER LOGICAL INCH
            _FONT_PT = max(8, round(_FONT_PT * ppi / 96))
        except Exception:
            pass
        _FONT = ("TkDefaultFont", _FONT_PT)

        # MEASURE WIDTH FROM FULL TEXT, THEN EACH PARAGRAPH SEPARATELY FOR HEIGHT
        PARA_GAP = 6
        probe = tk.Label(self._widget, text=self._text, font=_FONT, justify="left", wraplength=280, padx=0, pady=0, bd=0)
        probe.update_idletasks()
        tw = probe.winfo_reqwidth() + self._TIP_PX * 2
        probe.destroy()

        text_w = tw - self._TIP_PX * 2
        paragraphs = self._text.split("\n")
        para_heights: list[int] = []
        for para in paragraphs:
            pl = tk.Label(self._widget, text=para or " ", font=_FONT, justify="left", wraplength=text_w, padx=0, pady=0, bd=0)
            pl.update_idletasks()
            para_heights.append(pl.winfo_reqheight())
            pl.destroy()
        th = sum(para_heights) + PARA_GAP * (len(paragraphs) - 1) + self._TIP_PY * 2

        cr = self._TIP_R
        self._tip = tk.Toplevel(self._widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"{tw}x{th}+{tip_x}+{tip_y}")
        self._tip.configure(bg=self._TIP_TRANSPARENT)
        try:
            self._tip.wm_attributes("-transparentcolor", self._TIP_TRANSPARENT)
        except tk.TclError:
            pass

        cv = tk.Canvas(self._tip, width=tw, height=th, bg=self._TIP_TRANSPARENT, highlightthickness=0)
        cv.pack()
        # DESTROY TOOLTIP WHEN MOUSE LEAVES IT
        self._tip.bind("<Leave>", self._hide)
        # ROUNDED RECTANGLE VIA smooth=True POLYGON; BORDER DRAWN FIRST (1px LARGER), FILL ON TOP
        pts = [cr, 0, tw - cr, 0, tw, 0, tw, cr, tw, th - cr, tw, th, tw - cr, th, cr, th, 0, th, 0, th - cr, 0, cr, 0, 0]
        cv.create_polygon(pts, smooth=True, fill=tip_border, outline="")
        inset = 1
        ipts = [
            cr, inset, tw - cr, inset, tw - inset, inset, tw - inset, cr, tw - inset, th - cr, tw - inset, th - inset, tw - cr,
            th - inset, cr, th - inset, inset, th - inset, inset, th - cr, inset, cr, inset, inset
        ]
        cv.create_polygon(ipts, smooth=True, fill=tip_bg, outline="")
        ty = self._TIP_PY
        for para, ph in zip(paragraphs, para_heights):
            cv.create_text(self._TIP_PX, ty, text=para, anchor="nw", fill=tip_fg, font=_FONT, width=text_w, justify="left")
            ty += ph + PARA_GAP

    def _hide(self, event: object = None) -> None:
        # Moving between a CTkButton's internal sub-widgets (canvas → text label etc.) fires
        # spurious Leave events. Ignore them if the pointer is still within the outer widget.
        try:
            wx = self._widget.winfo_rootx()
            wy = self._widget.winfo_rooty()
            ww = self._widget.winfo_width()
            wh = self._widget.winfo_height()
            px = self._widget.winfo_pointerx()
            py = self._widget.winfo_pointery()
            if wx <= px < wx + ww and wy <= py < wy + wh:
                return  # pointer still inside – not a real Leave
        except tk.TclError:
            pass
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
        # RENDER LOADER SVG AT 3× FOR ANTI-ALIASING, THEN GENERATE ONE ROTATED FRAME PER STEP
        HI = size * 3
        r, g, b, a = _svg_to_pil(ICONS["loader"], HI, color_hex).split()
        base = Image.merge("RGBA", (r, g, b, a.point(lambda v: round(v * 0.5))))  # type: ignore[attr-defined]

        step = 360.0 / self._FRAME_COUNT
        self._spin_frames = []
        for i in range(self._FRAME_COUNT):
            rotated = base.rotate(-i * step, resample=Image.BICUBIC, expand=False)  # type: ignore[attr-defined]
            lo = rotated.resize((size, size), Image.LANCZOS)  # type: ignore[attr-defined]
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
